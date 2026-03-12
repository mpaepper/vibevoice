import os
import sqlite3
import sys
from datetime import datetime

class TodoManager:
    def __init__(self, db_path='todo.db'):
        self.db_path = os.path.abspath(os.path.expanduser(db_path))
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def add_task(self, description, status='Backlog', priority='Medium'):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (description, status, priority) VALUES (?, ?, ?)",
                (description, status, priority)
            )
            conn.commit()
            return cursor.lastrowid

    def update_task_status(self, task_id, status):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_task_description(self, task_id, description):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET description = ? WHERE id = ?", (description, task_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_task(self, task_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_tasks(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_task_summary(self):
        """Returns a concise string of tasks for LLM context."""
        tasks = self.get_all_tasks()
        if not tasks:
            return "No tasks currently on the board."
        
        summary = []
        for t in tasks:
            summary.append(f"ID {t['id']}: {t['description']} [{t['status']}]")
        return "\n".join(summary)

    def display_todos(self):
        tasks = self.get_all_tasks()
        print("\n" + "=" * 50)
        print(f"       SQLITE KANBAN BOARD ({os.path.basename(self.db_path)})")
        print("=" * 50)
        
        sections = {
            "In Progress": "🚀 [IN PROGRESS]",
            "Waiting": "⏳ [WAITING]",
            "Backlog": "📋 [BACKLOG]",
            "Completed": "✅ [COMPLETED (Recent 5)]"
        }
        
        for status, title in sections.items():
            print(f"\n{title}")
            section_tasks = [t for t in tasks if t['status'] == status]
            
            if status == "Completed":
                section_tasks = section_tasks[:5]
                
            if section_tasks:
                for t in section_tasks:
                    print(f"  [{t['id']}] {t['description']}")
            else:
                print("  (Empty)")
            
        print("\n" + "=" * 50 + "\n")
        sys.stdout.flush()