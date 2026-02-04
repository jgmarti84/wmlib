"""Main entry point for ingestion service."""
import sys
from pathlib import Path
import structlog

from .config import load_settings
from .database import DatabaseManager
from .services import IngestionService


def setup_logging(log_level: str = "INFO"):
    """Configure structured logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def main():
    """Main function to run the ingestion service."""
    # Load settings
    try:
        settings = load_settings()
    except Exception as e:
        print(f"Failed to load settings: {e}")
        sys.exit(1)
    
    # Setup logging
    setup_logging(settings.app.log_level)
    logger = structlog.get_logger()
    
    logger.info(
        "ingestion_service_initializing",
        environment=settings.app.environment,
        log_level=settings.app.log_level
    )
    
    # Initialize database
    db_manager = DatabaseManager(settings)
    
    # Create tables if they don't exist
    try:
        db_manager.create_all()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        sys.exit(1)
    
    # Initialize ingestion service
    service = IngestionService(settings, db_manager)
    
    # Initialize radars from configuration
    try:
        service.initialize_radars()
        logger.info("radars_initialized")
    except Exception as e:
        logger.error("radar_initialization_failed", error=str(e))
        sys.exit(1)
    
    # Run service
    try:
        # For testing, run once. For production, use run_continuous()
        if len(sys.argv) > 1 and sys.argv[1] == "--once":
            logger.info("running_once_mode")
            service.run_once()
        else:
            logger.info("running_continuous_mode")
            service.run_continuous()
    except KeyboardInterrupt:
        logger.info("service_interrupted")
    except Exception as e:
        logger.error("service_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
