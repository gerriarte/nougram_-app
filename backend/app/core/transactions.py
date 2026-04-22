"""
Transaction management utilities
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def transaction(db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Transaction context manager with automatic rollback on error

    Usage:
        async with transaction(db):
            project = Project(...)
            db.add(project)
            quote = Quote(...)
            db.add(quote)
            # If anything fails, automatic rollback

    Args:
        db: Database session

    Yields:
        Database session for use in the context
    """
    try:
        yield db
        await db.commit()
        logger.debug("Transaction committed successfully")
    except Exception as e:
        await db.rollback()
        logger.error("Transaction rolled back due to error", error=str(e), exc_info=True)
        raise
