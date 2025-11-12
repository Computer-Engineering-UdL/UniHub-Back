import asyncio
from functools import wraps
from typing import Any, Callable, TypeVar

from fastapi.exceptions import HTTPException
from sqlalchemy.exc import NoResultFound
from starlette import status

from app.core.logger import logger

T = TypeVar("T")


def handle_api_errors(
    not_found_message: str = "Not found",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator factory to handle common CRUD errors.
    Accepts a custom message for the 404 Not Found error.
    Supports both sync and async functions.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                result = await func(*args, **kwargs)
                return result
            except NoResultFound as e:
                detail_message = str(e) if e.args else not_found_message
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail_message)
            except HTTPException as e:
                raise e
            except Exception as e:
                logger.error(e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                result = func(*args, **kwargs)
                return result
            except NoResultFound as e:
                detail_message = str(e) if e.args else not_found_message
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail_message)
            except HTTPException as e:
                raise e
            except Exception as e:
                logger.error(e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
