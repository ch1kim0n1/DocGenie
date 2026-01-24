#!/usr/bin/env python3
"""
Sample Python project for demonstrating DocGenie capabilities.

This is a simple web API built with FastAPI that demonstrates various
programming patterns that DocGenie can analyze and document.
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from datetime import datetime


# Data models
class User(BaseModel):
    """User model for the API."""

    id: Optional[int] = None
    name: str
    email: str
    created_at: Optional[datetime] = None


class UserCreate(BaseModel):
    """Model for creating new users."""

    name: str
    email: str


class Task(BaseModel):
    """Task model."""

    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    completed: bool = False
    user_id: int
    created_at: Optional[datetime] = None


# Database connection
def get_db():
    """Get database connection."""
    conn = sqlite3.connect("sample.db")
    conn.row_factory = sqlite3.Row
    return conn


# Initialize FastAPI app
app = FastAPI(
    title="Sample Task API",
    description="A sample API for managing users and tasks",
    version="1.0.0",
)


class UserService:
    """Service class for user operations."""

    def __init__(self, db_connection):
        """Initialize user service with database connection."""
        self.db = db_connection

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user object
        """
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, created_at) VALUES (?, ?, ?)",
            (user_data.name, user_data.email, datetime.now()),
        )
        user_id = cursor.lastrowid
        self.db.commit()

        return self.get_user(user_id)

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None if not found
        """
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            return User(**dict(row))
        return None

    def list_users(self) -> List[User]:
        """
        Get all users.

        Returns:
            List of all users
        """
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()

        return [User(**dict(row)) for row in rows]


class TaskService:
    """Service class for task operations."""

    def __init__(self, db_connection):
        """Initialize task service."""
        self.db = db_connection

    async def create_task(self, task_data: dict, user_id: int) -> Task:
        """
        Create a new task for a user.

        Args:
            task_data: Task data dictionary
            user_id: ID of the user creating the task

        Returns:
            Created task object
        """
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, user_id, created_at) VALUES (?, ?, ?, ?)",
            (task_data["title"], task_data.get("description"), user_id, datetime.now()),
        )
        task_id = cursor.lastrowid
        self.db.commit()

        return self.get_task(task_id)

    def get_task(self, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        if row:
            return Task(**dict(row))
        return None

    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed."""
        cursor = self.db.cursor()
        cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
        self.db.commit()
        return cursor.rowcount > 0


# API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the Sample Task API"}


@app.post("/users/", response_model=User)
async def create_user(user: UserCreate, db=Depends(get_db)):
    """Create a new user."""
    service = UserService(db)
    return service.create_user(user)


@app.get("/users/", response_model=List[User])
async def list_users(db=Depends(get_db)):
    """Get all users."""
    service = UserService(db)
    return service.list_users()


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, db=Depends(get_db)):
    """Get a specific user."""
    service = UserService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users/{user_id}/tasks/")
async def create_task(user_id: int, task_data: dict, db=Depends(get_db)):
    """Create a task for a user."""
    service = TaskService(db)
    return await service.create_task(task_data, user_id)


@app.put("/tasks/{task_id}/complete")
async def complete_task(task_id: int, db=Depends(get_db)):
    """Mark a task as completed."""
    service = TaskService(db)
    success = service.complete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task completed successfully"}


def initialize_database():
    """Initialize the database with required tables."""
    conn = get_db()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP
        )
    """)

    # Create tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT FALSE,
            user_id INTEGER,
            created_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    import uvicorn

    # Initialize database
    initialize_database()

    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
