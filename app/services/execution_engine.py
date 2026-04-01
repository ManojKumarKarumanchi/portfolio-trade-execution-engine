"""Core execution engine for portfolio trade execution."""
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.logger import logger
from app.database.models import Execution, ExecutionStatus, Order, OrderStatus, OrderAction
from app.brokers import (
    BaseBroker,
    BrokerAPIError,
    InvalidSymbolError,
    RateLimitError,
)
from app.schemas import OrderActionSchema


class ExecutionEngine:
    """
    Core execution engine for processing portfolio trades.

    Responsibilities:
    - Idempotency checking (prevent duplicate execution)
    - Order processing with retry logic
    - Partial failure handling (continue on errors)
    - State tracking and persistence
    - Result aggregation

    This is the heart of the trading system - correctness over speed.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize execution engine.

        Args:
            db: Database session for persistence
        """
        self.db = db

    async def execute_portfolio(
        self,
        execution_id: str,
        broker: BaseBroker,
        actions: list[OrderActionSchema]
    ) -> Execution:
        """
        Execute a portfolio of trades.

        This is the main entry point for trade execution.

        Args:
            execution_id: Unique execution ID (for idempotency)
            broker: Authenticated broker adapter instance
            actions: List of order actions to execute

        Returns:
            Execution model with complete results

        Flow:
        1. Check idempotency (already executed?)
        2. Create execution record
        3. Process each action sequentially
        4. Handle failures gracefully (don't stop)
        5. Aggregate results
        6. Update execution status
        """
        logger.info(f"Starting execution: {execution_id}")

        # Step 1: Idempotency check
        existing = await self._get_existing_execution(execution_id)
        if existing:
            logger.info(f"Execution {execution_id} already exists - returning cached result")
            return existing

        # Step 2: Create execution record
        execution = await self._create_execution(
            execution_id=execution_id,
            broker_name=broker.broker_name,
            total_orders=len(actions)
        )

        # Step 3: Update status to in_progress
        execution.status = ExecutionStatus.IN_PROGRESS
        await self.db.commit()

        # Step 4: Process each action
        results = []
        successful_count = 0
        failed_count = 0

        for action in actions:
            try:
                # Determine action type (BUY or SELL)
                order_action = self._determine_action(action)

                # Create order record
                order = await self._create_order(
                    execution_id=execution_id,
                    symbol=action.symbol,
                    action=order_action,
                    quantity=abs(action.qty)  # Handle REBALANCE negative qty
                )

                # Execute order with retry logic
                result = await self._execute_order_with_retry(
                    broker=broker,
                    order=order
                )

                if result.success:
                    successful_count += 1
                else:
                    failed_count += 1

                results.append(result)

            except Exception as e:
                # CRITICAL: Do NOT stop on failure - continue processing
                logger.error(
                    f"Order failed for {action.symbol}: {e}",
                    exc_info=True
                )
                failed_count += 1

                # Record failure in database
                await self._mark_order_failed(order, str(e))

        # Step 5: Update execution statistics
        execution.total_orders = len(actions)
        execution.successful_orders = successful_count
        execution.failed_orders = failed_count

        # Step 6: Determine final status
        if failed_count == 0:
            execution.status = ExecutionStatus.COMPLETED
        elif successful_count == 0:
            execution.status = ExecutionStatus.FAILED
        else:
            execution.status = ExecutionStatus.PARTIAL_SUCCESS

        execution.completed_at = datetime.now()
        await self.db.commit()

        logger.info(
            f"Execution {execution_id} completed: "
            f"{successful_count} success, {failed_count} failed"
        )

        return execution

    def _determine_action(self, action: OrderActionSchema) -> OrderAction:
        """
        Determine order action (BUY or SELL).

        Rules:
        - BUY → BUY
        - SELL → SELL
        - REBALANCE with qty > 0 → BUY
        - REBALANCE with qty < 0 → SELL
        """
        if action.type == "BUY":
            return OrderAction.BUY
        elif action.type == "SELL":
            return OrderAction.SELL
        elif action.type == "REBALANCE":
            return OrderAction.BUY if action.qty > 0 else OrderAction.SELL
        else:
            raise ValueError(f"Unknown action type: {action.type}")

    async def _get_existing_execution(self, execution_id: str) -> Execution | None:
        """Check if execution already exists (idempotency)."""
        result = await self.db.execute(
            select(Execution).where(Execution.id == execution_id)
        )
        return result.scalar_one_or_none()

    async def _create_execution(
        self,
        execution_id: str,
        broker_name: str,
        total_orders: int
    ) -> Execution:
        """Create new execution record."""
        execution = Execution(
            id=execution_id,
            broker=broker_name,
            status=ExecutionStatus.PENDING,
            total_orders=total_orders,
            successful_orders=0,
            failed_orders=0
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        logger.info(f"Created execution record: {execution_id}")
        return execution

    async def _create_order(
        self,
        execution_id: str,
        symbol: str,
        action: OrderAction,
        quantity: int
    ) -> Order:
        """Create order record."""
        order = Order(
            execution_id=execution_id,
            symbol=symbol,
            action=action,
            quantity=quantity,
            status=OrderStatus.PENDING,
            retry_count=0
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        return order

    @retry(
        retry=retry_if_exception_type((BrokerAPIError, RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=1, max=5),
    )
    async def _execute_order_with_retry(
        self,
        broker: BaseBroker,
        order: Order
    ):
        """
        Execute single order with retry logic.

        Retries on:
        - BrokerAPIError (transient failures)
        - RateLimitError (API throttling)

        Does NOT retry on:
        - InvalidSymbolError (permanent error)
        - AuthenticationError (needs user intervention)
        """
        try:
            logger.info(f"Executing: {order.action.value} {order.quantity} {order.symbol}")

            # Update order status
            order.status = OrderStatus.PENDING
            order.retry_count += 1
            await self.db.commit()

            # Place order via broker
            result = await broker.place_order(
                symbol=order.symbol,
                action=order.action.value,
                quantity=order.quantity
            )

            # Update order with result
            if result.success:
                order.status = OrderStatus.SUCCESS
                order.broker_order_id = result.broker_order_id
                order.executed_at = datetime.now()

                logger.info(
                    f"Order successful: {order.symbol} - "
                    f"Broker ID: {result.broker_order_id}"
                )
            else:
                order.status = OrderStatus.FAILED
                order.error_message = result.error_message

                logger.error(f"Order failed: {order.symbol} - {result.error_message}")

            await self.db.commit()
            return result

        except InvalidSymbolError as e:
            # Permanent error - don't retry
            logger.error(f"Invalid symbol {order.symbol}: {e}")
            await self._mark_order_failed(order, str(e))
            raise

        except Exception as e:
            # Log retry attempt
            logger.warning(
                f"Order attempt {order.retry_count} failed for {order.symbol}: {e}"
            )
            raise

    async def _mark_order_failed(self, order: Order, error: str):
        """Mark order as failed with error message."""
        order.status = OrderStatus.FAILED
        order.error_message = error
        await self.db.commit()

    async def get_execution_status(self, execution_id: str) -> Execution | None:
        """
        Get execution status by ID.

        Returns:
            Execution with all orders, or None if not found
        """
        result = await self.db.execute(
            select(Execution).where(Execution.id == execution_id)
        )
        return result.scalar_one_or_none()


def generate_execution_id() -> str:
    """Generate unique execution ID."""
    return str(uuid.uuid4())
