import asyncio
import sys

from loguru import logger

from app.application import run_application
from app.core.config import get_settings


def main() -> int:
    try:
        settings = get_settings()
        asyncio.run(run_application(settings))
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    return 0


if __name__ == "__main__":
    sys.exit(main())
