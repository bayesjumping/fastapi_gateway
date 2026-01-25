"""Todo API router with CRUD operations."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Path, status

from app.models.todo import Priority, TodoCreate, TodoUpdate, TodoResponse, TodoListResponse
from app.services.todo_service import TodoService


router = APIRouter()
todo_service = TodoService()


@router.get(
    "/todos",
    response_model=TodoListResponse,
    summary="List all todos",
    description="Retrieve a list of all todos with optional filtering by completion status and priority",
    response_description="List of todos with metadata"
)
async def list_todos(
    completed: Optional[bool] = Query(
        None,
        description="Filter by completion status"
    ),
    priority: Optional[Priority] = Query(
        None,
        description="Filter by priority level"
    ),
    tags: Optional[str] = Query(
        None,
        description="Filter by tags (comma-separated)",
        examples=["shopping,urgent"]
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Number of items to skip"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=100,
        description="Maximum number of items to return"
    )
) -> TodoListResponse:
    """
    List all todos with optional filtering.
    
    - **completed**: Filter by completion status
    - **priority**: Filter by priority level
    - **tags**: Filter by tags (comma-separated)
    - **skip**: Number of items to skip (pagination)
    - **limit**: Maximum items to return (pagination)
    """
    return todo_service.list_todos(completed, priority, tags, skip, limit)


@router.get(
    "/todos/{todo_id}",
    response_model=TodoResponse,
    summary="Get a specific todo",
    responses={
        200: {"description": "Todo found and returned"},
        404: {"description": "Todo not found"}
    }
)
async def get_todo(
    todo_id: int = Path(
        ...,
        ge=1,
        description="The ID of the todo to retrieve",
        examples=[1]
    )
) -> TodoResponse:
    """
    Retrieve a specific todo by its ID.
    
    - **todo_id**: The unique identifier of the todo (must be >= 1)
    """
    todo = todo_service.get_todo(todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )
    return todo


@router.post(
    "/todos",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new todo",
    responses={
        201: {"description": "Todo created successfully"},
        422: {"description": "Validation error"}
    }
)
async def create_todo(todo: TodoCreate) -> TodoResponse:
    """
    Create a new todo item.
    
    - **title**: Title of the todo (required, 1-200 characters)
    - **description**: Optional detailed description (max 1000 characters)
    - **completed**: Whether the todo is completed (default: false)
    - **priority**: Priority level (default: medium)
    - **tags**: List of tags for categorization (max 10 tags)
    """
    return todo_service.create_todo(todo)


@router.put(
    "/todos/{todo_id}",
    response_model=TodoResponse,
    summary="Update a todo",
    responses={
        200: {"description": "Todo updated successfully"},
        404: {"description": "Todo not found"},
        422: {"description": "Validation error"}
    }
)
async def update_todo(
    todo_update: TodoUpdate,
    todo_id: int = Path(..., ge=1, description="The ID of the todo to update")
) -> TodoResponse:
    """
    Update an existing todo. Only provided fields will be updated.
    
    - **todo_id**: The unique identifier of the todo (must be >= 1)
    - All fields are optional - only provided fields will be updated
    """
    todo = todo_service.update_todo(todo_id, todo_update)
    
    if todo is None:
        # Check if todo exists
        if not todo_service.get_todo(todo_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Todo with id {todo_id} not found"
            )
        # Todo exists but no fields to update
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one field must be provided for update"
        )
    
    return todo


@router.patch(
    "/todos/{todo_id}/toggle",
    response_model=TodoResponse,
    summary="Toggle todo completion status",
    responses={
        200: {"description": "Todo completion status toggled"},
        404: {"description": "Todo not found"}
    }
)
async def toggle_todo(
    todo_id: int = Path(..., ge=1, description="The ID of the todo to toggle")
) -> TodoResponse:
    """
    Toggle the completion status of a todo.
    
    - **todo_id**: The unique identifier of the todo (must be >= 1)
    """
    todo = todo_service.toggle_todo(todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )
    return todo


@router.delete(
    "/todos/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a todo",
    responses={
        204: {"description": "Todo deleted successfully"},
        404: {"description": "Todo not found"}
    }
)
async def delete_todo(
    todo_id: int = Path(..., ge=1, description="The ID of the todo to delete")
) -> None:
    """
    Delete a todo by its ID.
    
    - **todo_id**: The unique identifier of the todo (must be >= 1)
    """
    if not todo_service.delete_todo(todo_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )


@router.delete(
    "/todos",
    status_code=status.HTTP_200_OK,
    summary="Delete completed todos",
    response_description="Number of deleted todos"
)
async def delete_completed_todos() -> dict[str, int]:
    """
    Delete all completed todos.
    
    Returns the number of todos that were deleted.
    """
    deleted_count = todo_service.delete_completed_todos()
    return {"deleted_count": deleted_count}
