import functools
from typing import Callable, Any
from ops_pilot.utils.logger import log

def handle_tool_errors(func: Callable) -> Callable:
    """
    Decorator for tool functions to standardize error handling.
    - ValueError (Validation Error): returned clearly to the LLM.
    - Exception (System Error): logged with exc_info, generic string returned to the LLM.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            # User or tool input problem
            log.warning(f"Validation error in {func.__name__}: {str(e)}")
            return f"Validation Error: {str(e)}"
        except Exception as e:
            # System or application problem
            log.error(f"Unexpected system error in {func.__name__}: {str(e)}", exc_info=True)
            return "System Error: An unexpected error occurred while executing this tool. Please try again or escalate to an administrator."
    return wrapper
