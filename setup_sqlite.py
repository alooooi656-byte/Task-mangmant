"""
SQLite Database Setup & Seeding Script for Task Management Backend
==================================================================
Initializes the local SQLite database 'mini.db':
1. Connects to SQLite database file 'mini.db'.
2. Enables foreign key constraints (PRAGMA foreign_keys = ON;).
3. Creates exactly 3 tables:
   - 'users' (user_id, username, email)
   - 'projects' (project_id, name, description)
   - 'tasks' (task_id, title, description, status, project_id, user_id)
4. Seeds clean initial sample records with relational mapping.
5. Displays the database contents to verify relational integrity.
"""

import os
import sqlite3
from typing import Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mini.db")


def get_connection(db_file: str = DB_FILE) -> sqlite3.Connection:
    """Creates an SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Drops and recreates the 3 required tables with cascading constraints."""
    cursor = conn.cursor()

    # Drop existing tables in reverse dependency order
    cursor.execute("DROP TABLE IF EXISTS tasks;")
    cursor.execute("DROP TABLE IF EXISTS projects;")
    cursor.execute("DROP TABLE IF EXISTS users;")

    # 1. Users table
    cursor.execute(
        """
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE
        );
        """
    )

    # 2. Projects table
    cursor.execute(
        """
        CREATE TABLE projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        );
        """
    )

    # 3. Tasks table
    cursor.execute(
        """
        CREATE TABLE tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'To Do',
            project_id INTEGER NOT NULL,
            user_id INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL
        );
        """
    )

    print("[OK] Created tables: 'users', 'projects', 'tasks'.")


def seed_sample_data(conn: sqlite3.Connection) -> None:
    """Seeds test records into users, projects, and tasks."""
    cursor = conn.cursor()

    # Seed Users
    users = [
        ("Ali", "ali@example.com"),
        ("Saad", "saad@example.com"),
        ("Ahmed", "ahmed@example.com"),
        ("Omer", "omer@example.com"),
    ]
    cursor.executemany("INSERT INTO users (username, email) VALUES (?, ?);", users)
    print(f"[OK] Seeded {cursor.rowcount} users.")

    # Seed Projects
    projects = [
        ("Website Redesign", "Revamp frontend UI/UX and optimize Core Web Vitals."),
        ("Mobile App MVP", "Develop cross-platform Flutter application for task tracking."),
        ("Cloud Infrastructure", "Migrate backend microservices and configure CI/CD pipelines."),
        ("Analytics Dashboard", "Build executive real-time reporting metrics and KPI dashboards."),
    ]
    cursor.executemany("INSERT INTO projects (name, description) VALUES (?, ?);", projects)
    print(f"[OK] Seeded {cursor.rowcount} projects.")

    # Seed Tasks
    tasks = [
        ("Design Homepage Mockup", "Create responsive Figma wireframes.", "In Progress", 1, 1),
        ("Build Auth & JWT Middleware", "Implement secure authentication endpoints.", "Completed", 2, 2),
        ("Deploy Docker Containers to AWS", "Set up ECS task definitions and load balancers.", "To Do", 3, 3),
        ("Implement Real-time KPI Charts", "Render interactive task velocity graphs.", "In Progress", 4, 4),
    ]
    cursor.executemany(
        """
        INSERT INTO tasks (title, description, status, project_id, user_id)
        VALUES (?, ?, ?, ?, ?);
        """,
        tasks,
    )
    print(f"[OK] Seeded {cursor.rowcount} tasks.")


def display_seeded_data(conn: sqlite3.Connection) -> None:
    """Displays seeded tables to verify relational data."""
    cursor = conn.cursor()
    query = """
        SELECT 
            t.task_id,
            t.title,
            t.status,
            p.name AS project_name,
            COALESCE(u.username, 'Unassigned') AS assigned_user
        FROM tasks t
        JOIN projects p ON t.project_id = p.project_id
        LEFT JOIN users u ON t.user_id = u.user_id
        ORDER BY t.task_id ASC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    print("\n" + "=" * 80)
    print(f"{'Task ID':<8} | {'Title':<30} | {'Status':<12} | {'Project':<20} | {'Assigned'}")
    print("-" * 80)
    for row in rows:
        print(f"{row['task_id']:<8} | {row['title']:<30} | {row['status']:<12} | {row['project_name']:<20} | {row['assigned_user']}")
    print("=" * 80 + "\n")


def setup_database():
    """Main setup entry point."""
    conn: Optional[sqlite3.Connection] = None
    try:
        print("=" * 75)
        print("  TASK MANAGEMENT SYSTEM - SQLITE DATABASE INITIALIZATION")
        print("=" * 75)
        print(f"Target Database File: {DB_FILE}")

        conn = get_connection(DB_FILE)
        create_tables(conn)
        seed_sample_data(conn)
        conn.commit()

        display_seeded_data(conn)
        print("SUCCESS: SQLite database 'mini.db' initialized and ready for use!\n")

    except sqlite3.Error as err:
        print(f"\n[ERROR] SQLite error: {err}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    setup_database()
