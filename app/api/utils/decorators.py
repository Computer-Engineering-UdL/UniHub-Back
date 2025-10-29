from functools import wraps
from typing import Any, Callable, TypeVar

from fastapi.exceptions import HTTPException
from sqlalchemy.exc import NoResultFound
from starlette import status

T = TypeVar("T")


def handle_api_errors(
    not_found_message: str = "Not found",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator factory to handle common CRUD errors.
    Accepts a custom message for the 404 Not Found error.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                result = func(*args, **kwargs)
                return result
            except NoResultFound as e:
                detail_message = str(e) if e.args else not_found_message
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail_message)
            except HTTPException as e:
                raise e
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )

        return wrapper

    return decorator
