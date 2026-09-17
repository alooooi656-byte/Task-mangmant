"""
Task Management Backend — SQLite Edition
=========================================
Connects directly to 'mini.db' using Python's built-in sqlite3 module.
No external packages or running servers required.

Confirmed database schema (mini.db):
  users    : user_id (PK AUTOINCREMENT), username, email
  projects : project_id (PK AUTOINCREMENT), name, description
  tasks    : task_id (PK AUTOINCREMENT), title, description,
             status (DEFAULT 'To Do'), project_id (FK), user_id (FK)
"""

import os
import sys
import sqlite3

# ── Database path ─────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mini.db")


# ── Connection helper ──────────────────────────────────────────────────────────
def get_conn() -> sqlite3.Connection:
    """Return an sqlite3 connection with FK enforcement and dict-style rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def ask(prompt: str) -> str:
    """Strip-safe input helper."""
    return input(prompt).strip()


# ── Existence checks ───────────────────────────────────────────────────────────
def _project_row(cursor: sqlite3.Cursor, project_id: int):
    cursor.execute(
        "SELECT project_id, name, description FROM projects WHERE project_id = ?",
        (project_id,),
    )
    return cursor.fetchone()


def _user_row(cursor: sqlite3.Cursor, user_id: int):
    cursor.execute(
        "SELECT user_id, username, email FROM users WHERE user_id = ?",
        (user_id,),
    )
    return cursor.fetchone()


# ==============================================================================
# USER MANAGEMENT  (table: users)
# ==============================================================================
def add_user():
    print("\n── Add User ──")
    username = ask("Username: ")
    email    = ask("Email: ")
    if not username or not email:
        print("[ERROR] Username and email are required.")
        return
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO users (username, email) VALUES (?, ?)",
                (username, email),
            )
            conn.commit()
            print("[OK] User added.")
        except sqlite3.IntegrityError:
            print("[ERROR] That username or email already exists.")


def view_users():
    print("\n── All Users ──")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT user_id, username, email FROM users ORDER BY user_id"
        ).fetchall()
    if not rows:
        print("[INFO] No users found.")
        return
    print(f"{'ID':<6} {'Username':<24} {'Email'}")
    print("─" * 60)
    for r in rows:
        print(f"{r['user_id']:<6} {r['username']:<24} {r['email']}")


def update_user():
    print("\n── Update User ──")
    raw = ask("User ID to update: ")
    if not raw.isdigit():
        print("[ERROR] ID must be a number.")
        return
    uid = int(raw)
    with get_conn() as conn:
        cur = conn.cursor()
        row = _user_row(cur, uid)
        if not row:
            print(f"[WARNING] No user with ID {uid}.")
            return
        new_name  = ask(f"New username  (current: '{row['username']}'): ") or row["username"]
        new_email = ask(f"New email     (current: '{row['email']}'): ")    or row["email"]
        try:
            cur.execute(
                "UPDATE users SET username = ?, email = ? WHERE user_id = ?",
                (new_name, new_email, uid),
            )
            conn.commit()
            print(f"[OK] User {uid} updated.")
        except sqlite3.IntegrityError:
            print("[ERROR] That username or email is already taken.")


def delete_user():
    print("\n── Delete User ──")
    raw = ask("User ID to delete: ")
    if not raw.isdigit():
        print("[ERROR] ID must be a number.")
        return
    uid = int(raw)
    with get_conn() as conn:
        cur = conn.cursor()
        row = _user_row(cur, uid)
        if not row:
            print(f"[WARNING] No user with ID {uid}.")
            return
        confirm = ask(f"Delete '{row['username']}'? (y/n): ")
        if confirm.lower() != "y":
            print("[INFO] Cancelled.")
            return
        cur.execute("DELETE FROM users WHERE user_id = ?", (uid,))
        conn.commit()
        print(f"[OK] User {uid} deleted.")


# ==============================================================================
# PROJECT MANAGEMENT  (table: projects)
# ==============================================================================
def add_project():
    print("\n── Add Project ──")
    name = ask("Project name: ")
    if not name:
        print("[ERROR] Project name is required.")
        return
    description = ask("Description (optional): ")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO projects (name, description) VALUES (?, ?)",
            (name, description or None),
        )
        conn.commit()
        print(f"[OK] Project added (ID: {cur.lastrowid}).")


def view_projects():
    print("\n── All Projects ──")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT project_id, name, description FROM projects ORDER BY project_id"
        ).fetchall()
    if not rows:
        print("[INFO] No projects found.")
        return
    print(f"{'ID':<6} {'Name':<30} Description")
    print("─" * 75)
    for r in rows:
        desc = (r["description"] or "")[:38]
        print(f"{r['project_id']:<6} {r['name']:<30} {desc}")


def update_project():
    print("\n── Update Project ──")
    raw = ask("Project ID to update: ")
    if not raw.isdigit():
        print("[ERROR] ID must be a number.")
        return
    pid = int(raw)
    with get_conn() as conn:
        cur = conn.cursor()
        row = _project_row(cur, pid)
        if not row:
            print(f"[WARNING] No project with ID {pid}.")
            return
        new_name = ask(f"New name        (current: '{row['name']}'): ")        or row["name"]
        new_desc = ask(f"New description (current: '{row['description']}'): ") or row["description"]
        cur.execute(
            "UPDATE projects SET name = ?, description = ? WHERE project_id = ?",
            (new_name, new_desc, pid),
        )
        conn.commit()
        print(f"[OK] Project {pid} updated.")


def delete_project():
    print("\n── Delete Project ──")
    raw = ask("Project ID to delete: ")
    if not raw.isdigit():
        print("[ERROR] ID must be a number.")
        return
    pid = int(raw)
    with get_conn() as conn:
        cur = conn.cursor()
        row = _project_row(cur, pid)
        if not row:
            print(f"[WARNING] No project with ID {pid}.")
            return
        confirm = ask(f"Delete project '{row['name']}' and all its tasks? (y/n): ")
        if confirm.lower() != "y":
            print("[INFO] Cancelled.")
            return
        cur.execute("DELETE FROM projects WHERE project_id = ?", (pid,))
        conn.commit()
        print(f"[OK] Project {pid} (and related tasks) deleted.")


# ==============================================================================
# TASK MANAGEMENT  (table: tasks)
# ==============================================================================
def add_task():
    print("\n── Add Task ──")
    title = ask("Task title: ")
    if not title:
        print("[ERROR] Title is required.")
        return
    description = ask("Description (optional): ")
    status = ask("Status [To Do / In Progress / Completed] (default: To Do): ") or "To Do"

    raw_pid = ask("Project ID: ")
    if not raw_pid.isdigit():
        print("[ERROR] Project ID must be a number.")
        return
    pid = int(raw_pid)

    raw_uid = ask("Assign to User ID (optional, Enter to skip): ")
    uid = int(raw_uid) if raw_uid.isdigit() else None

    with get_conn() as conn:
        cur = conn.cursor()
        if not _project_row(cur, pid):
            print(f"[ERROR] Project ID {pid} does not exist.")
            return
        if uid and not _user_row(cur, uid):
            print(f"[ERROR] User ID {uid} does not exist.")
            return
        cur.execute(
            """INSERT INTO tasks (title, description, status, project_id, user_id)
               VALUES (?, ?, ?, ?, ?)""",
            (title, description or None, status, pid, uid),
        )
        conn.commit()
        print(f"[OK] Task added (ID: {cur.lastrowid}).")


def view_tasks():
    print("\n── All Tasks ──")
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT t.task_id, t.title, t.status,
                   p.name        AS project_name,
                   COALESCE(u.username, '—') AS assigned_to
            FROM   tasks t
            JOIN   projects p ON p.project_id = t.project_id
            LEFT   JOIN users u ON u.user_id = t.user_id
            ORDER  BY t.task_id
            """
        ).fetchall()
    if not rows:
        print("[INFO] No tasks found.")
        return
    print(f"{'ID':<6} {'Title':<28} {'Status':<14} {'Project':<20} Assigned")
    print("─" * 90)
    for r in rows:
        print(
            f"{r['task_id']:<6} {r['title'][:26]:<28} {r['status']:<14}"
            f" {r['project_name'][:18]:<20} {r['assigned_to']}"
        )


def update_task():
    print("\n── Update Task ──")
    raw = ask("Task ID to update: ")
    if not raw.isdigit():
        print("[ERROR] ID must be a number.")
        return
    tid = int(raw)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE task_id = ?", (tid,))
        row = cur.fetchone()
        if not row:
            print(f"[WARNING] No task with ID {tid}.")
            return

        new_title  = ask(f"New title   (current: '{row['title']}'): ")       or row["title"]
        new_desc   = ask(f"New description (current: '{row['description']}'): ") or row["description"]
        new_status = ask(f"New status  (current: '{row['status']}'): ")       or row["status"]

        raw_pid = ask(f"New Project ID (current: {row['project_id']}): ")
        new_pid = int(raw_pid) if raw_pid.isdigit() else row["project_id"]
        if not _project_row(cur, new_pid):
            print(f"[ERROR] Project ID {new_pid} does not exist.")
            return

        raw_uid = ask(f"New User ID (current: {row['user_id']}, 'none' to unassign): ")
        if raw_uid.lower() == "none":
            new_uid = None
        elif raw_uid.isdigit():
            new_uid = int(raw_uid)
            if not _user_row(cur, new_uid):
                print(f"[ERROR] User ID {new_uid} does not exist.")
                return
        else:
            new_uid = row["user_id"]

        cur.execute(
            """UPDATE tasks
               SET title = ?, description = ?, status = ?, project_id = ?, user_id = ?
               WHERE task_id = ?""",
            (new_title, new_desc, new_status, new_pid, new_uid, tid),
        )
        conn.commit()
        print(f"[OK] Task {tid} updated.")


def delete_task():
    print("\n── Delete Task ──")
    raw = ask("Task ID to delete: ")
    if not raw.isdigit():
        print("[ERROR] ID must be a number.")
        return
    tid = int(raw)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT task_id, title FROM tasks WHERE task_id = ?", (tid,))
        row = cur.fetchone()
        if not row:
            print(f"[WARNING] No task with ID {tid}.")
            return
        confirm = ask(f"Delete task '{row['title']}'? (y/n): ")
        if confirm.lower() != "y":
            print("[INFO] Cancelled.")
            return
        cur.execute("DELETE FROM tasks WHERE task_id = ?", (tid,))
        conn.commit()
        print(f"[OK] Task {tid} deleted.")


# ==============================================================================
# MENUS
# ==============================================================================
def user_menu():
    options = {"1": view_users, "2": add_user, "3": update_user, "4": delete_user}
    while True:
        print("\n┌─ User Management ─┐")
        print("│ 1. View users      │")
        print("│ 2. Add user        │")
        print("│ 3. Update user     │")
        print("│ 4. Delete user     │")
        print("│ 5. Back            │")
        print("└────────────────────┘")
        choice = ask("Choice: ")
        if choice == "5":
            break
        action = options.get(choice)
        if action:
            action()
        else:
            print("[WARNING] Invalid option.")


def project_menu():
    options = {"1": view_projects, "2": add_project, "3": update_project, "4": delete_project}
    while True:
        print("\n┌─ Project Management ─┐")
        print("│ 1. View projects      │")
        print("│ 2. Add project        │")
        print("│ 3. Update project     │")
        print("│ 4. Delete project     │")
        print("│ 5. Back               │")
        print("└───────────────────────┘")
        choice = ask("Choice: ")
        if choice == "5":
            break
        action = options.get(choice)
        if action:
            action()
        else:
            print("[WARNING] Invalid option.")


def task_menu():
    options = {"1": view_tasks, "2": add_task, "3": update_task, "4": delete_task}
    while True:
        print("\n┌─ Task Management ─┐")
        print("│ 1. View tasks      │")
        print("│ 2. Add task        │")
        print("│ 3. Update task     │")
        print("│ 4. Delete task     │")
        print("│ 5. Back            │")
        print("└────────────────────┘")
        choice = ask("Choice: ")
        if choice == "5":
            break
        action = options.get(choice)
        if action:
            action()
        else:
            print("[WARNING] Invalid option.")


def main_menu():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found at: {DB_PATH}")
        print("  Run 'py setup_sqlite.py' first to create mini.db.")
        sys.exit(1)

    print("\n══════════════════════════════════")
    print("  Task Management System — SQLite")
    print(f"  DB: {os.path.basename(DB_PATH)}")
    print("══════════════════════════════════")

    menus = {"1": user_menu, "2": project_menu, "3": task_menu}
    while True:
        print("\n┌─ Main Menu ──────────┐")
        print("│ 1. User Management   │")
        print("│ 2. Project Management│")
        print("│ 3. Task Management   │")
        print("│ 4. Exit              │")
        print("└──────────────────────┘")
        choice = ask("Choice: ")
        if choice == "4":
            print("Goodbye!")
            sys.exit(0)
        action = menus.get(choice)
        if action:
            action()
        else:
            print("[WARNING] Invalid option — please choose 1–4.")


if __name__ == "__main__":
    main_menu()
