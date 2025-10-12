from functools import wraps
from typing import Any, Callable, TypeVar

from fastapi.exceptions import HTTPException
from starlette import status

T = TypeVar("T")


def handle_crud_errors(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to handle common CRUD error patterns"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            result = func(*args, **kwargs)
            if result is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            return result
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    return wrapper
