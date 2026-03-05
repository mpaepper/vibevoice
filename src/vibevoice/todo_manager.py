import os
import re
import difflib

class TodoManager:
    def __init__(self, file_path='todos.md'):
        self.file_path = os.path.abspath(os.path.expanduser(file_path))
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                f.write("# To-Do List\n\n## In Progress\n\n## Waiting\n\n## Backlog\n\n## Completed\n")
        else:
            # Check if it needs migration to Kanban format
            content = self.read_todos()
            if "## Backlog" not in content and "## In Progress" not in content:
                self.migrate_to_kanban(content)

    def migrate_to_kanban(self, old_content):
        """Migrate a simple list to the Kanban structure."""
        lines = old_content.splitlines()
        tasks = []
        completed = []
        
        for line in lines:
            if line.strip().startswith("- [ ]"):
                tasks.append(line.strip())
            elif line.strip().startswith("- [x]"):
                completed.append(line.strip())
        
        new_content = "# To-Do List\n\n## In Progress\n\n## Waiting\n\n## Backlog\n"
        for task in tasks:
            new_content += f"{task}\n"
        
        new_content += "\n## Completed\n"
        for task in completed:
            new_content += f"{task}\n"
            
        self.write_todos(new_content)
        print(f"Migrated {self.file_path} to Kanban format.")

    def read_todos(self):
        if not os.path.exists(self.file_path):
            return "# To-Do List\n\n## In Progress\n\n## Waiting\n\n## Backlog\n\n## Completed\n"
        with open(self.file_path, 'r') as f:
            return f.read()

    def write_todos(self, content):
        with open(self.file_path, 'w') as f:
            f.write(content)

    def display_todos(self):
        content = self.read_todos()
        print("\n" + "=" * 40)
        print(f"       KANBAN TO-DO BOARD ({os.path.basename(self.file_path)})")
        print("=" * 40)
        
        sections = {"In Progress": [], "Waiting": [], "Backlog": [], "Completed": []}
        current_section = None
        
        for line in content.splitlines():
            line_strip = line.strip()
            if "## In Progress" in line:
                current_section = "In Progress"
            elif "## Waiting" in line:
                current_section = "Waiting"
            elif "## Backlog" in line or "## To-Do" in line:
                current_section = "Backlog"
            elif "## Completed" in line or "## Done" in line:
                current_section = "Completed"
            elif line_strip.startswith("- ["):
                if current_section:
                    sections[current_section].append(line_strip)
                else:
                    # Fallback for lines before any header
                    sections["Backlog"].append(line_strip)

        # 1. Show In Progress (Active Focus)
        print("\n🚀 [IN PROGRESS]")
        if sections["In Progress"]:
            for item in sections["In Progress"]:
                print(f"  {item}")
        else:
            print("  (Nothing currently active)")

        # 2. Show Waiting (Blocked/Pending)
        print("\n⏳ [WAITING]")
        if sections["Waiting"]:
            for item in sections["Waiting"]:
                print(f"  {item}")
        else:
            print("  (No tasks waiting)")

        # 3. Show Backlog
        print("\n📋 [BACKLOG]")
        if sections["Backlog"]:
            for item in sections["Backlog"]:
                print(f"  {item}")
        else:
            print("  (Backlog is empty)")

        # 4. Show Completed (Last 3)
        print("\n✅ [COMPLETED (Recent 3)]")
        if sections["Completed"]:
            recent_completed = sections["Completed"][-3:]
            for item in recent_completed:
                print(f"  {item}")
        else:
            print("  (No completed tasks yet)")
            
        print("\n" + "=" * 40 + "\n")

    def show_diff(self, old_content, new_content):
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        diff = difflib.unified_diff(old_lines, new_lines, fromfile='Current', tofile='Updated', lineterm='')
        
        has_changes = False
        print("\n--- Board Updates ---")
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                print(f"\033[92m{line}\033[0m")  # Green for additions
                has_changes = True
            elif line.startswith('-') and not line.startswith('---'):
                print(f"\033[91m{line}\033[0m")  # Red for deletions
                has_changes = True
        
        if not has_changes:
            print("No changes detected.")
        print("----------------------\n")
