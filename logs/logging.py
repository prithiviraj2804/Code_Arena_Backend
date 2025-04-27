import logging, os, sys
from loguru import logger

LOG_DIR  = "logs"
LOG_FILE = os.path.join(LOG_DIR, "code_arena.log")
os.makedirs(LOG_DIR, exist_ok=True)

# 1) Remove default sink
logger.remove()

# 2) Console sink (no filter; let std‐logging suppression handle watchfiles)
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>"
)

# 3) File sink with rotation & retention
logger.add(
    LOG_FILE,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

# 4) Intercept stdlib logging
class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=2, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())

logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)

# 5) Suppress watchfiles at WARNING+
logging.getLogger("watchfiles").setLevel(logging.WARNING)
