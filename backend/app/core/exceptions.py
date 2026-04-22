"""
Custom exceptions for the application
"""

from fastapi import HTTPException, status


class BusinessLogicError(HTTPException):
    """Exception for business logic violations"""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ResourceNotFoundError(HTTPException):
    """Exception for resource not found"""

    def __init__(self, resource_type: str, resource_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type} with id {resource_id} not found",
        )


class ResourceInUseError(HTTPException):
    """Exception for trying to delete a resource that's in use"""

    def __init__(
        self,
        resource_type: str,
        resource_name: str,
        usage_count: int,
        usage_context: str = "quote item(s)",
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete {resource_type} '{resource_name}'. It is being used in {usage_count} {usage_context}. Please remove it from all quotes first.",
        )
