# TCP Client
import helper
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

# Controls the GUI
class GUI():
    def __init__(self) -> None:
        self.client = Client(self)
        self.app = QApplication([])
        self.user = None
        self.loginScreen = LoginScreen(self)
        self.mainScreen = MainScreen(self)
        self.window = self.initializeWindow()
        self.threads = []

    # Goes to the main screen
    def goToMainScreen(self) -> None:
        self.window.setCurrentIndex(self.window.currentIndex() + 1)

    def submitAnswer(self) -> None:
        answer = self.mainScreen.answerLineEdit.text()
        self.mainScreen.answerLineEdit.clear()
        answerJSON = {
            TKN.TKN:TKN.PLAYER_ANSWER,
            KEY.ANSWER:answer
        }
        self.client.send(answerJSON)

    # Creates and formats window and widgets for GUI
    def initializeWindow(self) -> QStackedWidget:
        window = QStackedWidget()
        window.setFixedSize(700, 600)
        window.setAttribute(Qt.WA_StyledBackground, True)
        window.setStyleSheet('background-color: rgb(255, 168, 119)')
        window.addWidget(self.loginScreen)
        window.addWidget(self.mainScreen)
        window.show()
        return window

    # Updates the list of players
    def updatePlayers(self, json: dict) -> None:
        for player in json[KEY.PLAYER_LIST]:
            self.updatePlayer(player)

    # Updates a single player
    def updatePlayer(self, json: dict) -> None:
        self.mainScreen.usernameLabels[json[KEY.PLAYER_NUM]].setText(json[KEY.PLAYER_NAME])
        self.mainScreen.scoreLabels[json[KEY.PLAYER_NUM]].setText(str(json[KEY.PLAYER_SCORE]))

    # Connects the sets up the client to the server
    def connect(self) -> None:
        connectionThread = threading.Thread(target=self.client.connect, args=(ADDRESS, self.loginScreen.usernameLineEdit.text()))
        self.threads.append(connectionThread)
        connectionThread.start()

    # Closes the client and GUI and join all the threads
    def close(self) -> None:
        msgJSON = {TKN.TKN:TKN.CLIENT_CLOSED}
        closingThread = threading.Thread(target=self.client.send, args=(msgJSON, ))
        closingThread.start()
        self.threads.append(closingThread)

        for thread in self.threads:
            thread.join()
        helper.log("Closing GUI".encode())
        sys.exit()

# Has the screen to join the game
class LoginScreen(QDialog):
    def __init__(self, gui):
        super(LoginScreen, self).__init__()
        loadUi("ui/login.ui", self)
        self.connectButton.clicked.connect(lambda:
            gui.connect())
        self.errorLabel.setText("")
        self.setFixedSize(700, 600)

# Has the main screen with players and board
class MainScreen(QDialog):
    def __init__(self, gui):
        super(MainScreen, self).__init__()
        loadUi("ui/main_screen.ui", self)
        self.gui = gui
        self.debugLabel.setText("TEMP_TEXT")
        self.scoreLabels = [
            self.scoreLabel0, self.scoreLabel1, self.scoreLabel2]
        self.usernameLabels = [
            self.usernameLabel0, self.usernameLabel1, self.usernameLabel2]

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.gui.submitAnswer()
        event.accept()


# Controls the GUI <-> Client <-> Server connection
class Client():
    def __init__(self, gui):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gui = gui
        self.bufferLength = BUFFER
        self.connected = False

    # Connects to the server, prints confirmation
    def connect(self, address: tuple[str, int], playerName: str) -> None:
        self.playerName = playerName

        # Try to connect to the server
        try:
            self.socket.connect(address)
            responseJson = self.recieve()
            self.playerNum = responseJson[KEY.PLAYER_NUM]

            if responseJson[KEY.STATUS]:
                self.gui.goToMainScreen()
                msgJSON = {
                    TKN.TKN:TKN.PLAYER_JOIN,
                    KEY.SEND_TYPE:VAL.CLIENT,
                    KEY.PLAYER_NUM:self.playerNum,
                    KEY.PLAYER_NAME:self.playerName,
                    KEY.PLAYER_SCORE:0
                }
                self.socket.send(json.dumps(msgJSON).encode())

                responseJson = self.recieve()
                self.gui.updatePlayers(responseJson)

                # Starts the thread for listening to the server
                self.connected = True
                listeningThread = threading.Thread(target=self.listeningThread)
                self.gui.threads.append(listeningThread)
                listeningThread.start()
                self.gui.go

        # Prompt error on failure to connect      
        except:
            self.gui.loginScreen.errorLabel.setText("Server Error")

    # Listens to the server for a block of data
    def recieve(self) -> dict:
        response = self.socket.recv(self.bufferLength)
        helper.log(response)
        responseJson = helper.loadJSON(response)
        return responseJson

    # Repeatedly listens to the server for any messages
    def listeningThread(self) -> None:
        while self.connected:
            responseJSON = self.recieve()
            gui.mainScreen.debugLabel.setText(json.dumps(responseJSON))

            token = responseJSON[TKN.TKN]

            if token == TKN.CLIENT_CLOSED:
                self.connected = False

            if token == TKN.PLAYER_UPDATE:
                updateThread = threading.Thread(target=self.gui.updatePlayers, args=(responseJSON, ))
                updateThread.start()

            if token == TKN.PLAYER_ANSWER:
                gui.mainScreen.debugLabel.setText(responseJSON[KEY.ANSWER])

    # Takes a message and add a header with client info and sends to server
    def send(self, msg: dict) -> None:
        standardHeader = {
            KEY.SEND_TYPE:VAL.CLIENT,
            KEY.PLAYER_NUM:self.playerNum,
            KEY.PLAYER_NAME:self.playerName,
        }
        msg.update(standardHeader)
        msgJson = json.dumps(msg)
        self.socket.send(msgJson.encode())

if __name__ == "__main__":
    gui = GUI()
    gui.app.exec()
    gui.close()
