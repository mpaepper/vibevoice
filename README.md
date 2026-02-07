# Vibevoice 🎙️

Hi, I'm [Marc Päpper](https://x.com/mpaepper) and I wanted to vibe code like [Karpathy](https://x.com/karpathy/status/1886192184808149383) ;D, so I looked around and found the cool work of [Vlad](https://github.com/vlad-ds/whisper-keyboard). I extended it to run with a local whisper model, so I don't need to pay for OpenAI tokens.
I hope you have fun with it!

## What it does 🚀

![Demo Video](docs/vibevoice-demo-caption.gif)

Simply run `cli.py` and start dictating text anywhere in your system:
1. Hold down right control key (Ctrl_r)
2. Speak your text
3. Release the key
4. Watch as your spoken words are transcribed and automatically typed!

Works in any application or window - your text editor, browser, chat apps, anywhere you can type!

NEW: LLM voice command mode:

1. Hold down the scroll_lock key (I think it's normally not used anymore that's why I chose it)
2. Speak what you want the LLM to do
3. The LLM receives your transcribed text and a screenshot of your current view
4. The LLM answer is typed into your keyboard (streamed)

Works everywhere on your system and the LLM always has the screen context

## Installation 🛠️

```bash
git clone https://github.com/mpaepper/vibevoice.git
cd vibevoice
pip install -r requirements.txt
python src/vibevoice/cli.py
```

## Requirements 📋

### Python Dependencies
- Python 3.13 or higher

### System Requirements
- CUDA-capable GPU (recommended) -> in server.py you can enable cpu use
- CUDA 12.x
- cuBLAS
- cuDNN 9.x
- In case you get this error: `OSError: PortAudio library not found` run `sudo apt install libportaudio2`
- [Ollama](https://ollama.com) for AI command mode (with multimodal models for screenshot support)

#### Setting up Ollama
1. Install Ollama by following the instructions at [ollama.com](https://ollama.com)
2. Pull a model that supports both text and images for best results:
   ```bash
   ollama pull gemma3:27b  # Great model which can run on RTX 3090 or similar
   ```
3. Make sure Ollama is running in the background:
   ```bash
   ollama serve
   ```

#### Handling the CUDA requirements

* Make sure that you have CUDA >= 12.4 and cuDNN >= 9.x
* I had some trouble at first with Ubuntu 24.04, so I did the following:
* Attention: DO NOT do this if your are a WSL user (https://docs.nvidia.com/cuda/wsl-user-guide/index.html)

```bash
sudo apt update && sudo apt upgrade
sudo apt autoremove nvidia* --purge
ubuntu-drivers devices
sudo ubuntu-drivers autoinstall
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb && sudo apt update
sudo apt install cuda-toolkit-12-8
```
or alternatively:

``` 
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install cudnn9-cuda-12
```

* Then after rebooting, it worked well.

## Usage 💡

1. Start the application:
```bash
python src/vibevoice/cli.py
```

2. Hold down right control key (Ctrl_r) while speaking
3. Release to transcribe
4. Your text appears wherever your cursor is!

### Configuration

You can customize various aspects of VibeVoice with the following environment variables:

#### Keyboard Controls
- `VOICEKEY`: Change the dictation activation key (default: "ctrl_r")
  ```bash
  export VOICEKEY="ctrl"  # Use left control instead
  ```
- `VOICEKEY_CMD`: Set the key for AI command mode (default: "scroll_lock")
  ```bash
  export VOICEKEY_CMD="ctsl"  # Use left control instead of Scroll Lock key
  ```

#### AI and Screenshot Features
- `OLLAMA_MODEL`: Specify which Ollama model to use (default: "gemma3:27b")
  ```bash
  export OLLAMA_MODEL="gemma3:4b"  # Use a smaller VLM in case you have less GPU RAM
  ```
- `INCLUDE_SCREENSHOT`: Enable or disable screenshots in AI command mode (default: "true")
  ```bash
  export INCLUDE_SCREENSHOT="false"  # Disable screenshots (but they are local only anyways)
  ```
- `SCREENSHOT_MAX_WIDTH`: Set the maximum width for screenshots (default: "1024")
  ```bash
  export SCREENSHOT_MAX_WIDTH="800"  # Smaller screenshots
  ```

#### Screenshot Dependencies
To use the screenshot functionality:
```bash
sudo apt install gnome-screenshot
```

#### Transcription Backend
- `TRANSCRIPTION_BACKEND`: Choose between `whisper` (default) and `voxtral`.
  ```bash
  export TRANSCRIPTION_BACKEND="voxtral"
  ```
- `VOXTRAL_URL`: Set the Voxtral API URL (default: "http://localhost:8000/v1")
- `VOXTRAL_MODEL`: Set the Voxtral model name (default: "mistralai/Voxtral-Mini-4B-Realtime-2602")

## Usage Modes 💡

VibeVoice supports two modes:

### 1. Dictation Mode
1. Hold down the dictation key (default: right Control)
2. Speak your text
3. Release to transcribe
4. Your text appears wherever your cursor is!

### 2. AI Command Mode
1. Hold down the command key (default: Scroll Lock)
2. Ask a question or give a command
3. Release the key
4. The AI will analyze your request (and current screen if enabled) and type a response

## Voxtral Realtime Support 🎙️

You can use the new Mistral Voxtral real-time model instead of the local Whisper model.

### Setup Instructions

1.  **Install vLLM (nightly version):**
    ```bash
    uv pip install -U vllm --torch-backend=auto --extra-index-url https://wheels.vllm.ai/nightly
    ```
    Ensure `mistral_common >= 1.9.0` is installed.

2.  **Start the model via vLLM:**
    ```bash
    vllm serve mistralai/Voxtral-Mini-4B-Realtime-2602 --host 0.0.0.0 --port 8000
    ```
    *Note: The model requires a GPU with at least 16 GB VRAM.*

3.  **Run VibeVoice with Voxtral backend:**
    ```bash
    export TRANSCRIPTION_BACKEND="voxtral"
    python src/vibevoice/cli.py
    ```

### Optional Optimizations
Install additional audio libraries for better performance:
```bash
pip install soxr librosa soundfile
```
(Note: `soundfile`, `librosa`, and `soxr` are already included in `requirements.txt`)

## Credits 🙏

- Original inspiration: [whisper-keyboard](https://github.com/vlad-ds/whisper-keyboard) by Vlad
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper) for the optimized Whisper implementation
- Built by [Marc Päpper](https://www.paepper.com)
