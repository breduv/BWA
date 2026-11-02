import asyncio
import sys

from loguru import logger

from app.application import run_application
from app.core.config import get_settings
from app.core.logging import configure_logging


def main() -> int:
    try:
        settings = get_settings()
        configure_logging(settings.log_level)
        asyncio.run(run_application(settings))
    except KeyboardInterrupt:
        pass
    except (OSError, RuntimeError, ValueError) as exc:
        reason = " ".join(str(exc).split())[:250]
        logger.error(f"Application failed: {type(exc).__name__}: {reason}")
        logger.opt(exception=exc).debug("Application traceback")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
