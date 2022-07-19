# TCP Client
from datetime import datetime
import json
import socket
import sys
import threading
from strings import *
import tokens as TKN
import values as VAL
import keys as KEY
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtCore import *

print("TCP Client")
ADDRESS = ("127.0.0.1", 8080)
BUFFER = 1024

# Sourced from https://stackoverflow.com/questions/39247342/pyqt-gui-size-on-high-resolution-screens
# Scales the application for 4k monitors
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

def addTimestamp(msg: str) -> str:
    return datetime.now().strftime("<%H:%M:%S> ") + msg

def log(msg: bytes) -> str:
    print(addTimestamp(msg.decode()))

def load(msg: bytes) -> dict:
    return json.loads(msg.decode())

class GUI():
    def __init__(self) -> None:
        self.client = Client(self)
        self.app = QApplication([])
        self.user = None
        self.loginScreen = LoginScreen(self)
        self.mainScreen = MainScreen()
        self.window = self.initializeWindow()
        self.threads = []

    def goToMainScreen(self):
        self.window.setCurrentIndex(self.window.currentIndex() + 1)
    
    def initializeWindow(self):
        '''
        Creates and formats a window.
        Returns: QStackedWidget to be used as window.
        '''
        window = QStackedWidget()
        window.setFixedSize(700, 600)
        window.setAttribute(Qt.WA_StyledBackground, True)
        window.setStyleSheet('background-color: rgb(255, 168, 119)')
        window.addWidget(self.loginScreen)
        window.addWidget(self.mainScreen)
        window.show()
        return window

    def connect(self):
        connectionThread = threading.Thread(target=self.client.connect, args=(ADDRESS, self.loginScreen.usernameLineEdit.text()))
        self.threads.append(connectionThread)
        connectionThread.start()
        
        self.goToMainScreen()

    def close(self):
        msg = json.dumps({
            TKN.TKN:TKN.CLIENT_CLOSED,
            KEY.SEND_TYPE:VAL.CLIENT,
            KEY.PLAYER_NUM:self.client.playerNum,
            KEY.PLAYER_NAME:self.client.playerName
        })
        closingThread = threading.Thread(target=self.client.send, args=(msg, ))
        closingThread.start()
        self.threads.append(closingThread)

        for thread in self.threads:
            thread.join()
        sys.exit()

class LoginScreen(QDialog):
    def __init__(self, gui):
        super(LoginScreen, self).__init__()
        loadUi("ui/login.ui", self)
        self.connectButton.clicked.connect(lambda:
            gui.connect())
        self.errorLabel.hide()
        self.setFixedSize(700, 600)

class MainScreen(QDialog):
    def __init__(self):
        super(MainScreen, self).__init__()
        layout = QVBoxLayout()
        # Label
        helloLabel = QLabel()
        helloLabel.setText("hello")
        # Order of widgets
        layout.addWidget(helloLabel)
        self.setLayout(layout)

class Client():
    def __init__(self, gui):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gui = gui
        self.bufferLength = BUFFER

    # Connects to the server, prints confirmation
    def connect(self, address: tuple[str, int], playerName: str) -> None:
        self.playerName = playerName
        self.socket.connect(address)
        response = self.socket.recv(self.bufferLength)
        log(response)
        responseJson = load(response)
        self.playerNum = responseJson[KEY.PLAYER_NUM]

        if responseJson[KEY.STATUS]:
            self.socket.send(json.dumps({
                TKN.TKN:TKN.PLAYER_JOIN,
                KEY.SEND_TYPE:VAL.CLIENT,
                KEY.PLAYER_NUM:self.playerNum,
                KEY.PLAYER_NAME:self.playerName
            }).encode())

        response = self.socket.recv(self.bufferLength)
        log(response)

        listeningThread = threading.Thread(target=self.listeningThread, daemon=True)
        gui.threads.append(listeningThread)
        listeningThread.start()

    # Listens to the server for any messages
    def listeningThread(self) -> None:
        while True:
            response = self.socket.recv(self.bufferLength)
            log(response)
            msg = response.decode()
            if msg == "":
                break

    def send(self, msg: str) -> None:
        self.socket.send(msg.encode())

    def close(self) -> None:
        self.socket.close()

if __name__ == "__main__":
    gui = GUI()
    gui.app.exec()
    gui.close()
