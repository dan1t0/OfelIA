import sys
import requests
import json
import os
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QWidget, QTextBrowser, QPushButton, QHBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QIcon
import markdown

# Define the root directory of this script and the path to the configuration file
ROOT_DIR = str(Path(__file__).parent)
CONFIG_PATH = os.path.join(ROOT_DIR, 'config.json')
APIS = os.path.join(ROOT_DIR, 'apikey.json')


class ResultWindow(QWidget):
    """
    A simple GUI window for displaying text results.
    """

    def __init__(self):
        super().__init__()

        # Set up the window's title and text browser widget
        self.setWindowTitle("OfelIA")
        self.setWindowIcon(QIcon.fromTheme("dialog-information"))  # Standard icon

        layout = QVBoxLayout()

        self.text_browser = QTextBrowser(self)
        self.text_browser.setReadOnly(True)
        self.text_browser.setOpenExternalLinks(True)
        # Modern style for the text area
        self.text_browser.setStyleSheet(
            "background: #f5f5f7; color: #222; border-radius: 10px; border: 1px solid #bbb; padding: 16px; font: 15pt 'Menlo', 'Consolas', monospace;"
        )
        self.text_browser.setMinimumHeight(100)
        self.text_browser.setMaximumHeight(600)
        self.text_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.text_browser)

        # Add Copy and Close buttons in a horizontal layout
        button_layout = QHBoxLayout()
        self.send_button = QPushButton("Copy & Close", self)
        self.send_button.clicked.connect(self.send_and_paste)
        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.close)
        # Style for the buttons
        button_style = (
            "QPushButton { background-color: #0078d7; color: white; border-radius: 8px; padding: 8px 24px; font-size: 14px; }"
            "QPushButton:hover { background-color: #005fa3; }"
        )
        self.send_button.setStyleSheet(button_style)
        self.close_button.setStyleSheet(button_style.replace('#0078d7', '#888').replace('#005fa3', '#666'))
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        
        # Set initial, minimum, and maximum window size
        self.setMinimumSize(400, 200)
        self.resize(600, 350)
        self.setMaximumSize(1200, 900)
        # The window is resizable by the user

        # Initialize a variable to store the markdown text
        self.markdown_text = ""

    def append_text(self, text):
        """
        Append text to the text browser widget in markdown format.
        :param text: The text to be appended.
        """
        # Append the new markdown text
        self.markdown_text += text
        
        # Convert the complete markdown text to HTML using markdown
        html_content = markdown.markdown(self.markdown_text)
        self.text_browser.setStyleSheet("font: 16pt")
        # Fix the output with Spanish characters
        html_content = html_content.replace("Ã¡", "á")
        html_content = html_content.replace("Ã©", "é")
        html_content = html_content.replace("Ã", "í")
        html_content = html_content.replace("í³", "ó")
        html_content = html_content.replace("íº", "ú")
        html_content = html_content.replace("í±", "ñ")
        html_content = html_content.replace("Ã¼", "ü")
        html_content = html_content.replace("Ã±", "ñ")
        html_content = html_content.replace("Ã±", "ñ")
        html_content = html_content.replace("Â¿", "¿")
        html_content = html_content.replace("Â¡", "¡")
        html_content = html_content.replace("â¢", "*")
        html_content = html_content.replace("â¢", "'") 
        
        self.text_browser.setHtml(html_content)  # Update the text browser widget with the new text
        # Adjust the window size to the content
        self.adjustSize()

    def keyPressEvent(self, event):
        """
        Close the window when Enter/Return is pressed.
        """
        from PyQt5.QtCore import Qt
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.close()
        else:
            super().keyPressEvent(event)

    def send_and_paste(self):
        """
        Copy the plain text to clipboard and close the window.
        """
        plain_text = self.text_browser.toPlainText()
        QApplication.clipboard().setText(plain_text)
        self.close()


class StreamThread(QThread):
    """
    A thread for streaming responses from the API.
    """
    new_text = pyqtSignal(str)

    def __init__(self, url, payload, apikeys, provider):
        super().__init__()
        self.url = url
        self.payload = payload
        self.apikeys = apikeys
        self.provider = provider

    def run(self):

        # Build the header
        # If key is not "dummy" add bearer to the header
        if self.apikeys[self.provider]["key"] != "dummy":
            headers = {
                "Authorization": "Bearer " + self.apikeys[self.provider]["key"],
                "Content-Type": "application/json"
            }
        else:
            headers = {
                "Content-Type": "application/json"
            }

        response = requests.post(self.url, json=self.payload, headers=headers, stream=True)

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
        print("Usage: ofelia.py <text> <action>")
        return

    text = sys.argv[1]
    action = sys.argv[2]

    # Load the configuration file
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    # Load API keys file
    with open(APIS, 'r') as f:
        apikeys = json.load(f)

    if action not in config:
        print(f"Error: Action '{action}' not found in configuration.")
        return

    action_config = config[action]
    

    # Construct the URL and payload for sending a request to the chat completion API
    path = "/v1/chat/completions"
    # Get provider from config
    provider = action_config["provider"]
    url = apikeys[provider]["url"].rstrip("/") + path
    
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

    thread = StreamThread(url, payload, apikeys, provider)
    thread.new_text.connect(window.append_text)
    thread.start()

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
