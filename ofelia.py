import sys
import requests
import json
import os
from pathlib import Path
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
        #setDinwod tittle to the model used
        self.setWindowTitle("OfelIA")
        #self.setWindowTitle("OfelIA is using: ")
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        
        # Create a vertical layout for the window's widgets
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def append_text(self, text):
        """
        Append text to the text edit widget.
        :param text: The text to be appended.
        """
        self.text_edit.append(text)


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
    prompt = action_config["prompt_template"].format(text=text)
   
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": action_config["model"],
        "max_tokens": action_config["max_tokens"],
        "temperature": action_config["temperature"]
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        # Show the result in a GUI window
        show_result(response.json()["choices"][0]["message"]["content"])
    else:
        # Show an error message in a GUI window
        show_result("Error: " + response.text)


def show_result(result):
    """
    Display the given text result in a GUI window.
    :param result: The text to be displayed.
    """
    app = QApplication(sys.argv)
    window = ResultWindow()
    window.append_text(result)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()