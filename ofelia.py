import sys
import requests
import json
import os
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QWidget, QTextBrowser
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
        self.text_browser = QTextBrowser(self)
        self.text_browser.setReadOnly(True)
        self.text_browser.setOpenExternalLinks(True)  # Permitir enlaces clicables

        # Create a vertical layout for the window's widgets
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()
        layout.addWidget(self.text_browser)
        self.setLayout(layout)
        
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
        #fix the output with Spanish characters
        html_content = html_content.replace("Ã¡", "á")
        html_content = html_content.replace("Ã©", "é")
        html_content = html_content.replace("Ã", "í")
        html_content = html_content.replace("í³", "ó")
        html_content = html_content.replace("íº", "ú")
        html_content = html_content.replace("í±", "ñ")
        html_content = html_content.replace("Ã¼", "ü")
        html_content = html_content.replace("Ã‘", "Ñ")
        html_content = html_content.replace("Ã±", "ñ")
        html_content = html_content.replace("Â¿", "¿")
        html_content = html_content.replace("Â¡", "¡")
        html_content = html_content.replace("â¢", "*")
        html_content = html_content.replace("â¢", "'") 
       
        
        self.text_browser.setHtml(html_content)  # Update the text browser widget with the new text


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

        # building the header
        # if key is not "dummy" adding bearer to the header
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
        print("Usage: ai.py <text> <action>")
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
    #get provider from config
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
