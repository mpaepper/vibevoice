import os
import re
import difflib

class TodoManager:
    def __init__(self, file_path='todos.md'):
        self.file_path = os.path.abspath(file_path)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                f.write("# To-Do List\n\n")

    def read_todos(self):
        if not os.path.exists(self.file_path):
            return "# To-Do List\n\n"
        with open(self.file_path, 'r') as f:
            return f.read()

    def write_todos(self, content):
        with open(self.file_path, 'w') as f:
            f.write(content)

    def display_todos(self):
        content = self.read_todos()
        # ANSI escape codes: \033[H (cursor home), \033[J (clear screen)
        # However, for a CLI tool, clearing the screen might be too intrusive.
        # Let's just print a separator.
        print("\n" + "=" * 40)
        print("       CURRENT TO-DO LIST")
        print("=" * 40)
        lines = content.splitlines()
        found_todo = False
        for line in lines:
            if line.strip().startswith('- ['):
                print(line)
                found_todo = True
        if not found_todo:
            print("(No open to-dos)")
        print("=" * 40 + "\n")

    def show_diff(self, old_content, new_content):
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        diff = difflib.unified_diff(old_lines, new_lines, fromfile='Current', tofile='Updated', lineterm='')
        
        has_changes = False
        print("\n--- Changes ---")
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                print(f"\033[92m{line}\033[0m")  # Green for additions
                has_changes = True
            elif line.startswith('-') and not line.startswith('---'):
                print(f"\033[91m{line}\033[0m")  # Red for deletions
                has_changes = True
        
        if not has_changes:
            print("No changes detected.")
        print("---------------\n")