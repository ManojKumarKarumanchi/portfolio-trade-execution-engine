"""
Database initialization script.

Usage:
    python init_db.py              # Create tables
    python init_db.py --reset      # Drop and recreate tables
    python init_db.py --seed       # Create tables and seed test data
    python init_db.py --validate   # Validate schema
    python init_db.py --stats      # Show database statistics
"""
import asyncio
import sys
from app.database.schema import (
    DatabaseSchema,
    DatabaseSeeder,
    DatabaseQueries,
    init_database,
    reset_database,
    validate_database,
)
from app.core.logger import logger


async def main():
    """Main initialization function."""
    args = sys.argv[1:]

    try:
        if "--reset" in args:
            # Drop and recreate tables
            logger.warning("Resetting database...")
            await reset_database()

        elif "--validate" in args:
            # Validate schema
            logger.info("Validating database schema...")
            is_valid = await validate_database()
            if is_valid:
                logger.info("Database schema is valid")
                sys.exit(0)
            else:
                logger.error("Database schema validation failed")
                sys.exit(1)

        elif "--stats" in args:
            # Show statistics
            counts = await DatabaseSchema.get_table_counts()
            stats = await DatabaseQueries.get_statistics()

            logger.info("\n" + "="*50)
            logger.info("DATABASE STATISTICS")
            logger.info("="*50)
            logger.info(f"Table Counts:")
            logger.info(f"  - Executions: {counts.get('executions', 0)}")
            logger.info(f"  - Orders: {counts.get('orders', 0)}")
            logger.info(f"\nPerformance:")
            logger.info(f"  - Total Orders: {stats.get('total_orders', 0)}")
            logger.info(f"  - Successful: {stats.get('successful_orders', 0)}")
            logger.info(f"  - Failed: {stats.get('failed_orders', 0)}")
            logger.info(f"  - Success Rate: {stats.get('success_rate', 0)}%")
            logger.info("="*50)

        elif "--seed" in args:
            # Create tables and seed test data
            logger.info("Creating database tables...")
            await init_database()

            logger.info("Seeding test data...")
            await DatabaseSeeder.seed_test_data(execution_count=5)

            logger.info("Database initialized and seeded with test data")

        elif "--clear" in args:
            # Clear all data but keep tables
            logger.warning("Clearing all data...")
            await DatabaseSeeder.clear_all_data()

        else:
            # Default: just create tables
            logger.info("Initializing database...")
            await init_database()

            # Check if tables were created successfully
            if await DatabaseSchema.check_tables_exist():
                logger.info("Database initialization complete")
                logger.info("\nAvailable commands:")
                logger.info("  python init_db.py --reset     # Drop and recreate")
                logger.info("  python init_db.py --seed      # Create and seed test data")
                logger.info("  python init_db.py --validate  # Validate schema")
                logger.info("  python init_db.py --stats     # Show statistics")
                logger.info("  python init_db.py --clear     # Clear all data")
            else:
                logger.error("Database initialization failed")
                sys.exit(1)

    except Exception as e:
        logger.error(f"Database operation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

