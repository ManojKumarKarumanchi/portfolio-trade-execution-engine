"""Execution API routes."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_dependency
from app.schemas import ExecutionRequest, ExecutionResponse, StatusResponse, OrderResponse
from app.services import ExecutionEngine, generate_execution_id
from app.services.notifications import ConsoleNotifier
from app.brokers import BrokerFactory, AuthenticationError
from app.core.logger import logger

router = APIRouter(prefix="/api/v1", tags=["execution"])


async def execute_portfolio_background(
    execution_id: str,
    broker_name: str,
    credentials: dict,
    actions: list,
    db: AsyncSession
):
    """
    Background task for portfolio execution.

    This runs asynchronously after the API returns a response.
    """
    try:
        logger.info(f"Background execution started: {execution_id}")

        # Create broker instance
        broker = BrokerFactory.get_broker(broker_name, credentials)

        # Authenticate
        await broker.authenticate()

        # Create execution engine
        engine = ExecutionEngine(db)

        # Execute portfolio
        execution = await engine.execute_portfolio(
            execution_id=execution_id,
            broker=broker,
            actions=actions
        )

        # Send notification
        notifier = ConsoleNotifier()
        await notifier.send(execution)

        logger.info(f"Background execution completed: {execution_id}")

    except Exception as e:
        logger.error(
            f"Background execution failed for {execution_id}: {e}",
            exc_info=True
        )


@router.post("/execute", response_model=ExecutionResponse, status_code=202)
async def execute_portfolio(
    request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_dependency)
):
    """
    Execute a portfolio of trades.

    This endpoint accepts a list of trade actions (BUY, SELL, REBALANCE)
    and executes them via the specified broker.

    **Execution is asynchronous** - the API returns immediately with an
    execution_id. Use GET /status/{execution_id} to check progress.

    **Idempotency:** If you provide an execution_id, the same request will
    return the cached result (safe to retry).

    Args:
        request: Execution request with broker, credentials, and actions
        background_tasks: FastAPI background tasks
        db: Database session (injected)

    Returns:
        ExecutionResponse with execution_id and status

    Example:
        POST /api/v1/execute
        {
          "broker": "zerodha",
          "credentials": {"api_key": "xxx", "access_token": "yyy"},
          "actions": [
            {"type": "BUY", "symbol": "INFY", "qty": 10},
            {"type": "SELL", "symbol": "TCS", "qty": 5}
          ]
        }
    """
    try:
        # Generate or use provided execution_id
        execution_id = request.execution_id or generate_execution_id()

        # Check if execution already exists (idempotency)
        engine = ExecutionEngine(db)
        existing = await engine.get_execution_status(execution_id)

        if existing:
            logger.info(f"Execution {execution_id} already exists - returning cached result")

            return ExecutionResponse(
                execution_id=existing.id,
                status=existing.status.value,
                message="Execution already processed (idempotent response)",
                broker=existing.broker,
                total_orders=existing.total_orders,
                successful_orders=existing.successful_orders,
                failed_orders=existing.failed_orders,
                created_at=existing.created_at,
                completed_at=existing.completed_at,
                orders=[
                    OrderResponse(
                        symbol=o.symbol,
                        action=o.action.value,
                        quantity=o.quantity,
                        status=o.status.value,
                        broker_order_id=o.broker_order_id,
                        error_message=o.error_message,
                        retry_count=o.retry_count,
                        executed_at=o.executed_at
                    )
                    for o in existing.orders
                ]
            )

        # Start background execution
        background_tasks.add_task(
            execute_portfolio_background,
            execution_id=execution_id,
            broker_name=request.broker,
            credentials=request.credentials,
            actions=request.actions,
            db=db
        )

        logger.info(f"Execution {execution_id} started in background")

        return ExecutionResponse(
            execution_id=execution_id,
            status="pending",
            message="Execution started in background. Use GET /status/{execution_id} to check progress.",
            broker=request.broker,
            total_orders=len(request.actions)
        )

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Broker authentication failed: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Execution request failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/status/{execution_id}", response_model=StatusResponse)
async def get_execution_status(
    execution_id: str,
    db: AsyncSession = Depends(get_db_dependency)
):
    """
    Get execution status by ID.

    Returns the current status of an execution including all orders.

    Args:
        execution_id: Unique execution identifier
        db: Database session (injected)

    Returns:
        StatusResponse with complete execution details

    Raises:
        404: Execution not found

    Example:
        GET /api/v1/status/550e8400-e29b-41d4-a716-446655440000
    """
    try:
        engine = ExecutionEngine(db)
        execution = await engine.get_execution_status(execution_id)

        if not execution:
            raise HTTPException(
                status_code=404,
                detail=f"Execution {execution_id} not found"
            )

        return StatusResponse(
            execution_id=execution.id,
            status=execution.status.value,
            broker=execution.broker,
            total_orders=execution.total_orders,
            successful_orders=execution.successful_orders,
            failed_orders=execution.failed_orders,
            created_at=execution.created_at,
            updated_at=execution.updated_at,
            completed_at=execution.completed_at,
            error_message=execution.error_message,
            orders=[
                OrderResponse(
                    symbol=o.symbol,
                    action=o.action.value,
                    quantity=o.quantity,
                    status=o.status.value,
                    broker_order_id=o.broker_order_id,
                    error_message=o.error_message,
                    retry_count=o.retry_count,
                    executed_at=o.executed_at
                )
                for o in execution.orders
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
