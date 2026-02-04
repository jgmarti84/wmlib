"""Database migration utilities."""
import structlog
from sqlalchemy import text, inspect

logger = structlog.get_logger()


def check_schema_compatibility(engine) -> bool:
    """Check if the existing database schema is compatible with current models.
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        True if schema is compatible, False if migration needed
    """
    inspector = inspect(engine)
    
    # Check if radars table exists
    if 'radars' not in inspector.get_table_names():
        # No tables exist, safe to create
        return True
    
    # Check radars table structure
    columns = inspector.get_columns('radars')
    column_names = [col['name'] for col in columns]
    
    # Old schema has 'id' (UUID), new schema has 'code' (String)
    if 'id' in column_names and 'code' not in column_names:
        logger.warning("incompatible_schema_detected", 
                      reason="radars table has 'id' instead of 'code'")
        return False
    
    return True


def migrate_to_new_schema(engine):
    """Migrate from old schema to new schema.
    
    This drops all existing tables and recreates them with the new schema.
    WARNING: This will delete all existing data!
    
    Args:
        engine: SQLAlchemy engine
    """
    logger.warning("starting_schema_migration", 
                   message="This will drop all existing tables and data")
    
    with engine.connect() as conn:
        # Drop all tables in correct order to handle foreign keys
        tables_to_drop = [
            'bufr_files',
            'radar_strategies', 
            'volumes',
            'strategies',
            'radars'
        ]
        
        for table in tables_to_drop:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                logger.info("table_dropped", table=table)
            except Exception as e:
                logger.warning("table_drop_failed", table=table, error=str(e))
        
        conn.commit()
    
    logger.info("schema_migration_completed")


def ensure_schema(engine):
    """Ensure database schema is up to date.
    
    Checks schema compatibility and migrates if needed.
    
    Args:
        engine: SQLAlchemy engine
    """
    if not check_schema_compatibility(engine):
        logger.warning("schema_migration_required")
        migrate_to_new_schema(engine)
    else:
        logger.info("schema_compatible")
