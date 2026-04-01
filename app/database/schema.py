"""Database schema management and utilities.

This module provides comprehensive database operations including:
- Table creation and deletion
- Schema validation
- Test data generation
- Common query utilities
"""

import asyncio
import sys
from datetime import datetime

from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger

from .base import Base
from .engine import engine
from .models import Execution, ExecutionStatus, Order, OrderAction, OrderStatus
from .session import SessionLocal


class DatabaseSchema:
    """Handles database schema operations."""

    @staticmethod
    async def create_all_tables() -> None:
        """Create all database tables defined in models.

        This operation is idempotent and safe to run multiple times.
        """
        try:
            logger.info("Creating database tables")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            table_names = ', '.join(Base.metadata.tables.keys())
            logger.info(f"Database tables created: {table_names}")

        except Exception as e:
            logger.error(f"Failed to create tables: {e}", exc_info=True)
            raise

    @staticmethod
    async def drop_all_tables() -> None:
        """Drop all database tables.

        Warning: This operation is destructive and will delete all data.
        """
        try:
            logger.warning("Dropping all database tables")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("All tables dropped")

        except Exception as e:
            logger.error(f"Failed to drop tables: {e}", exc_info=True)
            raise

    @staticmethod
    async def reset_database() -> None:
        """Reset database by dropping and recreating all tables.

        Warning: This operation is destructive and will delete all data.
        """
        logger.warning("Resetting database")
        await DatabaseSchema.drop_all_tables()
        await DatabaseSchema.create_all_tables()
        logger.info("Database reset complete")

    @staticmethod
    async def check_tables_exist() -> bool:
        """Check if all required tables exist in the database.

        Returns:
            True if all required tables exist, False otherwise.
        """
        try:
            async with engine.connect() as conn:
                result = await conn.run_sync(
                    lambda sync_conn: inspect(sync_conn).get_table_names()
                )

                required_tables = {"executions", "orders"}
                existing_tables = set(result)
                missing_tables = required_tables - existing_tables

                if missing_tables:
                    logger.warning(f"Missing tables: {missing_tables}")
                    return False

                logger.info(f"All required tables exist: {required_tables}")
                return True

        except Exception as e:
            logger.error(f"Error checking tables: {e}", exc_info=True)
            return False

    @staticmethod
    async def get_table_counts() -> dict[str, int]:
        """Get row counts for all tables.

        Returns:
            Dictionary mapping table names to row counts.
        """
        try:
            async with SessionLocal() as session:
                exec_count = await session.execute(
                    select(Execution).with_only_columns(text("count(*)"))
                )
                executions = exec_count.scalar()

                order_count = await session.execute(
                    select(Order).with_only_columns(text("count(*)"))
                )
                orders = order_count.scalar()

                counts = {
                    "executions": executions,
                    "orders": orders
                }

                logger.info(f"Table counts: {counts}")
                return counts

        except Exception as e:
            logger.error(f"Error getting table counts: {e}", exc_info=True)
            return {}

    @staticmethod
    async def validate_schema() -> bool:
        """Validate database schema against model definitions.

        Validates that all required tables and columns exist.

        Returns:
            True if schema is valid, False otherwise.
        """
        try:
            logger.info("Validating database schema")

            if not await DatabaseSchema.check_tables_exist():
                logger.error("Schema validation failed: Missing tables")
                return False

            async with engine.connect() as conn:
                inspector = await conn.run_sync(
                    lambda sync_conn: inspect(sync_conn)
                )

                exec_columns = await conn.run_sync(
                    lambda sync_conn: inspector.get_columns("executions")
                )
                exec_column_names = {col["name"] for col in exec_columns}

                required_exec_columns = {
                    "id", "broker", "status", "created_at", "updated_at",
                    "completed_at", "total_orders", "successful_orders",
                    "failed_orders", "error_message"
                }

                if not required_exec_columns.issubset(exec_column_names):
                    missing = required_exec_columns - exec_column_names
                    logger.error(f"Missing columns in executions: {missing}")
                    return False

                order_columns = await conn.run_sync(
                    lambda sync_conn: inspector.get_columns("orders")
                )
                order_column_names = {col["name"] for col in order_columns}

                required_order_columns = {
                    "id", "execution_id", "symbol", "action", "quantity",
                    "status", "retry_count", "broker_order_id",
                    "error_message", "created_at", "executed_at"
                }

                if not required_order_columns.issubset(order_column_names):
                    missing = required_order_columns - order_column_names
                    logger.error(f"Missing columns in orders: {missing}")
                    return False

            logger.info("Schema validation passed")
            return True

        except Exception as e:
            logger.error(f"Schema validation error: {e}", exc_info=True)
            return False


class DatabaseSeeder:
    """Provides utilities for seeding test data."""

    @staticmethod
    async def seed_sample_execution(
        execution_id: str = "sample-execution-001",
        broker: str = "zerodha",
        order_count: int = 3
    ) -> Execution:
        """Create a sample execution with orders for testing.

        Args:
            execution_id: Unique execution identifier.
            broker: Broker name.
            order_count: Number of sample orders to create.

        Returns:
            Created execution instance.
        """
        try:
            logger.info(f"Creating sample execution: {execution_id}")

            async with SessionLocal() as session:
                execution = Execution(
                    id=execution_id,
                    broker=broker,
                    status=ExecutionStatus.COMPLETED,
                    total_orders=order_count,
                    successful_orders=order_count - 1,
                    failed_orders=1,
                    completed_at=datetime.now()
                )
                session.add(execution)

                symbols = ["INFY", "TCS", "RELIANCE", "HDFC", "WIPRO"]
                for i in range(order_count):
                    order = Order(
                        execution_id=execution_id,
                        symbol=symbols[i % len(symbols)],
                        action=OrderAction.BUY if i % 2 == 0 else OrderAction.SELL,
                        quantity=(i + 1) * 10,
                        status=OrderStatus.SUCCESS if i < order_count - 1 else OrderStatus.FAILED,
                        broker_order_id=f"SAMPLE{i:06d}" if i < order_count - 1 else None,
                        error_message=None if i < order_count - 1 else "Sample error",
                        retry_count=0 if i < order_count - 1 else 3,
                        executed_at=datetime.now() if i < order_count - 1 else None
                    )
                    session.add(order)

                await session.commit()
                await session.refresh(execution)

                logger.info(f"Sample execution created: {execution_id}")
                return execution

        except Exception as e:
            logger.error(f"Failed to create sample execution: {e}", exc_info=True)
            raise

    @staticmethod
    async def clear_all_data() -> None:
        """Delete all data from tables while preserving structure.

        Warning: This operation is destructive and will delete all data.
        """
        try:
            logger.warning("Clearing all data from tables")
            async with SessionLocal() as session:
                await session.execute(text("DELETE FROM orders"))
                await session.execute(text("DELETE FROM executions"))
                await session.commit()
            logger.info("All data cleared")

        except Exception as e:
            logger.error(f"Failed to clear data: {e}", exc_info=True)
            raise

    @staticmethod
    async def seed_test_data(execution_count: int = 5) -> None:
        """Seed database with test data.

        Args:
            execution_count: Number of test executions to create.
        """
        try:
            logger.info(f"Seeding {execution_count} test executions")
            brokers = ["zerodha", "fyers", "angelone", "groww", "upstox"]

            for i in range(execution_count):
                execution_id = f"test-execution-{i+1:03d}"
                broker = brokers[i % len(brokers)]
                order_count = (i % 5) + 2

                await DatabaseSeeder.seed_sample_execution(
                    execution_id=execution_id,
                    broker=broker,
                    order_count=order_count
                )

            logger.info(f"Seeded {execution_count} test executions")

        except Exception as e:
            logger.error(f"Failed to seed test data: {e}", exc_info=True)
            raise


class DatabaseQueries:
    """Common database query utilities."""

    @staticmethod
    async def get_recent_executions(limit: int = 10) -> list[Execution]:
        """Get recent executions ordered by creation time.

        Args:
            limit: Maximum number of executions to return.

        Returns:
            List of recent executions.
        """
        async with SessionLocal() as session:
            result = await session.execute(
                select(Execution)
                .order_by(Execution.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    @staticmethod
    async def get_execution_by_id(execution_id: str) -> Execution | None:
        """Get execution by ID with all associated orders.

        Args:
            execution_id: Execution identifier.

        Returns:
            Execution instance if found, None otherwise.
        """
        async with SessionLocal() as session:
            result = await session.execute(
                select(Execution).where(Execution.id == execution_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_orders_by_symbol(symbol: str) -> list[Order]:
        """Get all orders for a specific symbol.

        Args:
            symbol: Stock symbol to search.

        Returns:
            List of matching orders.
        """
        async with SessionLocal() as session:
            result = await session.execute(
                select(Order)
                .where(Order.symbol == symbol)
                .order_by(Order.created_at.desc())
            )
            return list(result.scalars().all())

    @staticmethod
    async def get_failed_orders(limit: int = 20) -> list[Order]:
        """Get recent failed orders.

        Args:
            limit: Maximum number of orders to return.

        Returns:
            List of failed orders.
        """
        async with SessionLocal() as session:
            result = await session.execute(
                select(Order)
                .where(Order.status == OrderStatus.FAILED)
                .order_by(Order.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    @staticmethod
    async def get_statistics() -> dict[str, int | float]:
        """Get database statistics.

        Returns:
            Dictionary containing execution and order statistics.
        """
        async with SessionLocal() as session:
            total_exec = await session.execute(
                select(Execution).with_only_columns(text("count(*)"))
            )

            total_orders = await session.execute(
                select(Order).with_only_columns(text("count(*)"))
            )

            failed_orders = await session.execute(
                select(Order)
                .where(Order.status == OrderStatus.FAILED)
                .with_only_columns(text("count(*)"))
            )

            successful_orders = await session.execute(
                select(Order)
                .where(Order.status == OrderStatus.SUCCESS)
                .with_only_columns(text("count(*)"))
            )

            total_o = total_orders.scalar()
            success_o = successful_orders.scalar()
            success_rate = (success_o / total_o * 100) if total_o > 0 else 0

            return {
                "total_executions": total_exec.scalar(),
                "total_orders": total_o,
                "successful_orders": success_o,
                "failed_orders": failed_orders.scalar(),
                "success_rate": round(success_rate, 2)
            }


async def init_database() -> None:
    """Initialize database by creating all tables."""
    await DatabaseSchema.create_all_tables()


async def reset_database() -> None:
    """Reset database by dropping and recreating all tables."""
    await DatabaseSchema.reset_database()


async def validate_database() -> bool:
    """Validate database schema against model definitions."""
    return await DatabaseSchema.validate_schema()


async def seed_test_data() -> None:
    """Seed database with test data."""
    await DatabaseSeeder.seed_test_data()


async def get_db_stats() -> dict[str, int | float]:
    """Get database statistics."""
    return await DatabaseQueries.get_statistics()


async def main() -> None:
    """CLI interface for database operations."""
    if len(sys.argv) < 2:
        print("Usage: python schema.py [init|reset|validate|seed|stats|clear]")
        sys.exit(1)

    command = sys.argv[1].lower()

    try:
        if command == "init":
            await init_database()
        elif command == "reset":
            await reset_database()
        elif command == "validate":
            valid = await validate_database()
            sys.exit(0 if valid else 1)
        elif command == "seed":
            await seed_test_data()
        elif command == "stats":
            stats = await get_db_stats()
            print("\nDatabase Statistics:")
            print(f"Total Executions: {stats['total_executions']}")
            print(f"Total Orders: {stats['total_orders']}")
            print(f"Successful Orders: {stats['successful_orders']}")
            print(f"Failed Orders: {stats['failed_orders']}")
            print(f"Success Rate: {stats['success_rate']}%")
        elif command == "clear":
            await DatabaseSeeder.clear_all_data()
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
