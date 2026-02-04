"""Database session and connection management."""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from ..config import Settings
import structlog

logger = structlog.get_logger()


class DatabaseManager:
    """Database connection and session manager.
    
    Manages database engine, connection pooling, and session lifecycle.
    """
    
    def __init__(self, settings: Settings):
        """Initialize database manager.
        
        Args:
            settings: Application settings containing database config
        """
        self.settings = settings
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
    def _create_engine(self):
        """Create SQLAlchemy engine with connection pooling.
        
        Returns:
            SQLAlchemy engine instance
        """
        engine = create_engine(
            self.settings.database.url,
            poolclass=QueuePool,
            pool_size=self.settings.database.pool_size,
            max_overflow=self.settings.database.max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            echo=self.settings.app.log_level == "DEBUG",
        )
        
        # Add connection event listeners for logging
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("database_connection_established")
            
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            logger.debug("database_connection_checkout")
            
        return engine
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup.
        
        Yields:
            Database session
            
        Example:
            >>> with db_manager.get_session() as session:
            >>>     radar = session.query(Radar).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("database_session_error", error=str(e))
            raise
        finally:
            session.close()
    
    def create_all(self):
        """Create all database tables."""
        from ..models import Base
        Base.metadata.create_all(self.engine)
        logger.info("database_tables_created")
    
    def drop_all(self):
        """Drop all database tables (use with caution)."""
        from ..models import Base
        Base.metadata.drop_all(self.engine)
        logger.warning("database_tables_dropped")
