from pynput import keyboard
from pynput.keyboard import Controller as KeyboardController, Key, Listener

def on_press(key):
    print(f'Key pressed: {key}')

def on_release(key):
    if hasattr(key, 'vk'):
        print(key.vk)
    print(f'Key released: {key}')

def main():
    print('Press any key to see the key name. Note: you may need to press the key outside of the terminal.')
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == '__main__':
    main()
