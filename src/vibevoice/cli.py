"""Command-line interface for vibevoice"""

import os
import subprocess
import time
import json
import sounddevice as sd
import numpy as np
import requests
import sys
import base64
import re

SCREENSHOT_AVAILABLE = False
try:
    import pyautogui
    from PIL import Image
    SCREENSHOT_AVAILABLE = True
except ImportError as e:
    print(f"Screenshot functionality not available: {e}")
    print("Install Pillow with: pip install Pillow")

from pynput.keyboard import Controller as KeyboardController, Key, Listener, KeyCode
from scipy.io import wavfile
from dotenv import load_dotenv

from loading_indicator import LoadingIndicator
from todo_manager import TodoManager

loading_indicator = LoadingIndicator()

def start_whisper_server():
    server_script = os.path.join(os.path.dirname(__file__), 'server.py')
    process = subprocess.Popen(['python', server_script])
    return process

def wait_for_server(timeout=1800, interval=0.5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get('http://localhost:4242/health')
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(interval)
    raise TimeoutError("Server failed to start within timeout")

def capture_screenshot():
    """Capture a screenshot, save it, and return the path and base64 data."""
    if not SCREENSHOT_AVAILABLE:
        print("Screenshot functionality not available. Install Pillow with: pip install Pillow")
        return None, None
        
    try:
        screenshot_path = os.path.abspath('screenshot.png')
        print(f"Capturing screenshot to: {screenshot_path}")
        
        screenshot = pyautogui.screenshot()
        
        max_width = int(os.getenv('SCREENSHOT_MAX_WIDTH', '1024'))
        width, height = screenshot.size
        
        if width > max_width:
            ratio = max_width / width
            new_width = max_width
            new_height = int(height * ratio)
            screenshot = screenshot.resize((new_width, new_height))
        
        screenshot.save(screenshot_path)
        
        with open(screenshot_path, "rb") as image_file:
            base64_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        return screenshot_path, base64_data
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None, None

def _process_llm_cmd(keyboard_controller, transcript):
    """Process transcript with Ollama and type the response."""

    try:
        loading_indicator.show(message=f"Processing: {transcript}")
        
        model = os.getenv('OLLAMA_MODEL', 'gemma3:27b')
        include_screenshot = os.getenv('INCLUDE_SCREENSHOT', 'true').lower() == 'true'
        
        screenshot_path, screenshot_base64 = (None, None)
        if include_screenshot and SCREENSHOT_AVAILABLE:
            screenshot_path, screenshot_base64 = capture_screenshot()
        
        user_prompt = transcript.strip()
        
        system_prompt = """You are a voice-controlled AI assistant. The user is talking to their computer using voice commands.
Your responses will be directly typed into the user's keyboard at their cursor position, so:
1. Be concise and to the point, but friendly and engaging - prefer shorter answers
2. Focus on answering the specific question or request
3. Don't use introductory phrases like "Here's..." or "Based on the screenshot..."
4. Don't include formatting like bullet points, which might look strange when typed
5. If you see a screenshot, analyze it and use it to inform your response
6. Never apologize for limitations or explain what you're doing"""
        
        if screenshot_base64:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": True,
                "images": [screenshot_base64],  # Pass base64 data directly without data URI prefix
                "keep_alive": 0
            }
            print(f"Sending request with screenshot to model: {model}")
        else:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": True,
                "keep_alive": 0
            }
            print(f"Sending text-only request")
        
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                data = line.decode('utf-8')
                if data.startswith('{'):
                    chunk = json.loads(data)
                    if 'response' in chunk:
                        chunk_text = chunk['response']
                        print(f"Debug - received chunk: {repr(chunk_text)}")
                        
                        # Replace smart/curly quotes with standard apostrophes
                        # U+2018 (') and U+2019 (') are both replaced with standard apostrophe (')
                        normalized_text = chunk_text.replace('\u2019', "'").replace('\u2018', "'")
                        
                        keyboard_controller.type(normalized_text)
                        loading_indicator.hide()
        
        return "Successfully processed with Ollama"
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama: {e}")
    finally:
        loading_indicator.hide()

def _process_todo_cmd(todo_manager, transcript):
    """Process transcript with Ollama to generate SQLite commands for the to-do list."""
    try:
        loading_indicator.show(message=f"Updating To-Dos: {transcript}")
        task_summary = todo_manager.get_task_summary()
        
        model = os.getenv('OLLAMA_MODEL', 'gemma3:27b')
        
        system_prompt = f"""You are a productivity assistant managing a Kanban-style to-do board stored in an SQLite database.
The current board's task summary is provided below.
The user will give you a voice command to add, move, complete, or delete a task.

You MUST respond with one or more comma-separated commands, each on its own line, and NOTHING ELSE.
No conversational text, no explanations, no markdown code blocks.

AVAILABLE COMMANDS:
1. ADD,"description","status"
   - Possible status values: 'Backlog', 'In Progress', 'Waiting', 'Completed'
   - Default status is 'Backlog' if not specified.
2. UPDATE,id,"new_status"
   - Use this to move tasks between sections.
3. DELETE,id
   - Use this to remove tasks entirely.
4. RENAME,id,"new_description"
   - Use this to fix typos or refine task descriptions.

RULES:
- When the user says "work on", "start", or "switch to", move the task to 'In Progress'.
- When the user says "waiting", "blocked", or "on hold", move it to 'Waiting'.
- When the user says "finish", "done", or "complete", move it to 'Completed'.
- For new tasks, use ADD and put them in 'Backlog' unless specified otherwise.
- Use the ID from the summary below to reference existing tasks.

Current board summary:
{task_summary}"""

        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model,
            "prompt": transcript,
            "system": system_prompt,
            "stream": False,
            "keep_alive": 0
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        commands_text = response.json()['response'].strip()
        
        # Remove any accidental markdown code blocks
        commands_text = re.sub(r'```[a-zA-Z]*\n?', '', commands_text)
        commands_text = re.sub(r'\n?```', '', commands_text)
        
        print(f"\n--- AI Commands ---\n{commands_text}\n------------------")
        
        for line in commands_text.splitlines():
            line = line.strip()
            if not line or not ("," in line): continue
            
            # Simple but more robust CSV-like split
            parts = []
            import csv
            import io
            reader = csv.reader(io.StringIO(line))
            try:
                parts = next(reader)
            except:
                continue
                
            if not parts: continue
            cmd = parts[0].upper().strip()
            
            if cmd == "ADD" and len(parts) >= 2:
                status = parts[2].strip() if len(parts) >= 3 else "Backlog"
                todo_manager.add_task(parts[1].strip(), status=status)
                print(f"Added: {parts[1].strip()} ({status})")
            elif cmd == "UPDATE" and len(parts) >= 3:
                todo_manager.update_task_status(int(parts[1]), parts[2].strip())
                print(f"Moved ID {parts[1]} to {parts[2].strip()}")
            elif cmd == "DELETE" and len(parts) >= 2:
                todo_manager.delete_task(int(parts[1]))
                print(f"Deleted ID {parts[1]}")
            elif cmd == "RENAME" and len(parts) >= 3:
                todo_manager.update_task_description(int(parts[1]), parts[2].strip())
                print(f"Renamed ID {parts[1]} to {parts[2].strip()}")
        
        print("\nUpdating view...")
        todo_manager.display_todos()
            
    except Exception as e:
        print(f"Error updating to-dos: {e}")
    finally:
        loading_indicator.hide()

def main():
    load_dotenv()
    key_label = os.environ.get("VOICEKEY", "ctrl_r")
    cmd_label = os.environ.get("VOICEKEY_CMD", "scroll_lock")
    todo_label = os.environ.get("VOICEKEY_TODO", "pause")
    
    todo_db_path = os.environ.get("TODO_DB", "~/todo.db")
    
    RECORD_KEY = getattr(Key, key_label, None) or KeyCode.from_char(key_label)
    CMD_KEY = getattr(Key, cmd_label, None) or KeyCode.from_char(cmd_label)
    TODO_KEY = getattr(Key, todo_label, None) or KeyCode.from_char(todo_label)
    
    todo_manager = TodoManager(db_path=todo_db_path)
    todo_manager.display_todos()

    recording = False
    audio_data = []
    sample_rate = 16000
    keyboard_controller = KeyboardController()

    def on_press(key):
        nonlocal recording, audio_data
        if (key == RECORD_KEY or key == CMD_KEY or key == TODO_KEY) and not recording:
            recording = True
            audio_data = []
            print("Listening...")

    def on_release(key):
        nonlocal recording, audio_data
        if key == RECORD_KEY or key == CMD_KEY or key == TODO_KEY:
            recording = False
            print("Transcribing...")
            
            try:
                audio_data_np = np.concatenate(audio_data, axis=0)
            except ValueError as e:
                print(e)
                return
            
            recording_path = os.path.abspath('recording.wav')
            audio_data_int16 = (audio_data_np * np.iinfo(np.int16).max).astype(np.int16)
            wavfile.write(recording_path, sample_rate, audio_data_int16)

            try:
                response = requests.post('http://localhost:4242/transcribe/', 
                                      json={'file_path': recording_path})
                response.raise_for_status()
                transcript = response.json()['text']
                
                if transcript and key == RECORD_KEY:
                    processed_transcript = transcript + " "
                    print(processed_transcript)
                    keyboard_controller.type(processed_transcript)
                elif transcript and key == CMD_KEY:
                    _process_llm_cmd(keyboard_controller, transcript)
                elif transcript and key == TODO_KEY:
                    _process_todo_cmd(todo_manager, transcript)
            except requests.exceptions.RequestException as e:
                print(f"Error sending request to local API: {e}")
            except Exception as e:
                print(f"Error processing transcript: {e}")

    def callback(indata, frames, time, status):
        if status:
            print(status)
        if recording:
            audio_data.append(indata.copy())

    server_process = start_whisper_server()
    
    try:
        print(f"Waiting for the server to be ready...")
        wait_for_server()
        print(f"vibevoice is active. Hold down {key_label} to start dictating.")
        with Listener(on_press=on_press, on_release=on_release) as listener:
            with sd.InputStream(callback=callback, channels=1, samplerate=sample_rate):
                listener.join()
    except TimeoutError as e:
        print(f"Error: {e}")
        server_process.terminate()
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        server_process.terminate()

if __name__ == "__main__":
    main()
