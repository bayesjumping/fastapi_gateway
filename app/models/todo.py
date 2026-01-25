"""Todo models for the API."""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Priority(str, Enum):
    """Todo priority levels."""
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class TodoBase(BaseModel):
    """Base Todo model with common fields."""
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Title of the todo item",
        examples=["Buy groceries"]
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Detailed description of the todo",
        examples=["Get milk, eggs, and bread from the store"]
    )
    completed: bool = Field(
        default=False,
        description="Whether the todo is completed"
    )
    priority: Priority = Field(
        default=Priority.medium,
        description="Priority level of the todo"
    )
    tags: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Tags to categorize the todo",
        examples=[["shopping", "urgent"]]
    )
    
    @field_validator('title')
    @classmethod
    def title_must_not_be_empty(cls, v: str) -> str:
        """Validate that title is not just whitespace."""
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or only whitespace')
        return v.strip()
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and normalize tags."""
        if len(v) > 10:
            raise ValueError('Cannot have more than 10 tags')
        # Remove duplicates and normalize
        return list(set(tag.lower().strip() for tag in v if tag.strip()))


class TodoCreate(TodoBase):
    """Model for creating a new todo."""
    pass


class TodoUpdate(BaseModel):
    """Model for updating a todo - all fields optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None
    priority: Optional[Priority] = None
    tags: Optional[List[str]] = Field(None, max_length=10)
    
    @field_validator('title')
    @classmethod
    def title_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate that title is not just whitespace if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Title cannot be empty or only whitespace')
        return v.strip() if v else v


class TodoResponse(TodoBase):
    """Model for todo responses with additional metadata."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Unique identifier for the todo", examples=[1])
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the todo was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the todo was last updated"
    )


class TodoListResponse(BaseModel):
    """Model for list of todos with metadata."""
    todos: List[TodoResponse] = Field(..., description="List of todo items")
    total: int = Field(..., description="Total number of todos", examples=[42])
    completed: int = Field(..., description="Number of completed todos", examples=[15])
    pending: int = Field(..., description="Number of pending todos", examples=[27])
