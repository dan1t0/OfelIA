import sys
import requests
import json
import os
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QWidget

# Define the root directory of this script and the path to the configuration file
ROOT_DIR = str(Path(__file__).parent)
CONFIG_PATH = os.path.join(ROOT_DIR, 'config.json')


class ResultWindow(QWidget):
    """
    A simple GUI window for displaying text results.
    """

    def __init__(self):
        super().__init__()

        # Set up the window's title and text edit widget
        self.setWindowTitle("OfelIA")
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)

        # Create a vertical layout for the window's widgets
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def append_text(self, text):
        """
        Append text to the text edit widget.
        :param text: The text to be appended.
        """
        current_text = self.text_edit.toPlainText()  # Get the content of the text edit widget
        updated_text = current_text + text  # Concatenate the new text with the existing text
        self.text_edit.setStyleSheet("font: 16pt")
        self.text_edit.setPlainText(updated_text)  # Update the text edit widget with the new text


class StreamThread(QThread):
    """
    A thread for streaming responses from the API.
    """
    new_text = pyqtSignal(str)

    def __init__(self, url, payload):
        super().__init__()
        self.url = url
        self.payload = payload

    def run(self):
        response = requests.post(self.url, json=self.payload, stream=True)
        if response.status_code == 200:
            buffer = ""
            for chunk in response.iter_lines(decode_unicode=True):
                if chunk:
                    try:
                        data = json.loads(chunk[len("data: "):])
                        content = data['choices'][0]['delta'].get('content', '')
                        self.new_text.emit(content)
                    except json.JSONDecodeError:
                        continue
        else:
            self.new_text.emit("Error: " + response.text)


def main():
    """
    The main function for this script. It processes command-line arguments and
    displays results in a GUI window.
    """

    # Check if the correct number of command-line arguments are provided
    if len(sys.argv) != 3:
        print("Usage: ai.py <text> <action>")
        return

    text = sys.argv[1]
    action = sys.argv[2]

    # Load the configuration file
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    if action not in config:
        print(f"Error: Action '{action}' not found in configuration.")
        return

    action_config = config[action]

    # Construct the URL and payload for sending a request to the chat completion API
    url = "http://localhost:11434/v1/chat/completions"
    system_prompt = action_config["system_prompt"].format(text=text)
    user_prompt = action_config["user_prompt"].format(text=text)

    payload = {
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        "model": action_config["model"],
        "max_tokens": action_config["max_tokens"],
        "temperature": action_config["temperature"],
        "stream": True
    }

    app = QApplication(sys.argv)
    window = ResultWindow()

    thread = StreamThread(url, payload)
    thread.new_text.connect(window.append_text)
    thread.start()

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
