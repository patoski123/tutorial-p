from loguru import logger
import sys
from pathlib import Path


def setup_logger():
    """Setup logger configuration"""
    log_dir = Path("reports/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    # Add file handler
    logger.add(
        log_dir / "test_execution.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="10 days"
    )

    return logger


def get_logger(name: str):
    """Get logger instance"""
    setup_logger()
    return logger.bind(name=name)