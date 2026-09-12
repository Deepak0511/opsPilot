import sys
from pathlib import Path
from loguru import logger
from ops_pilot.config.settings import lookup_for_setting

log_dir = Path(lookup_for_setting["env_log_dir"])

# Ensure the log directory exists
log_dir.mkdir(parents=True, exist_ok=True)

# Remove the default Loguru console handler
logger.remove()

# 1. Console Sink (INFO and above) - Major steps
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# 2. Application Log Sink (DEBUG and above) - Verbose insiders
logger.add(
    log_dir / "application.log",
    level="DEBUG",
    rotation="10 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# 3. Audit Log Sink (INFO and above, exclusively for audit logs)
def audit_filter(record):
    return record["extra"].get("audit", False)

logger.add(
    log_dir / "audit.log",
    level="INFO",
    rotation="10 MB",
    retention="30 days",
    filter=audit_filter,
    format="{time:YYYY-MM-DD HH:mm:ss} | AUDIT | {message}"
)

# Expose the standard logger as `log`
log = logger

# Expose the audit logger (which attaches the `audit=True` extra context)
audit_log = logger.bind(audit=True)
