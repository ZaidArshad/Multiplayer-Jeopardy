# TCP Client
import time
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

        numOfPlayers = len(json[KEY.PLAYER_LIST])
        for i in range(2, numOfPlayers-1, -1):
            self.mainScreen.playerCards[i].clear()

    # Updates a single player
    def updatePlayer(self, json: dict) -> None:
        self.mainScreen.playerCards[json[KEY.PLAYER_NUM]].widget.nameLabel.setText(json[KEY.PLAYER_NAME])
        self.mainScreen.playerCards[json[KEY.PLAYER_NUM]].widget.scoreLabel.setText("$"+str(json[KEY.PLAYER_SCORE])+" ")

    # Connects the sets up the client to the server
    def connect(self) -> None:
        if len(self.loginScreen.usernameLineEdit.text()) == 0:
            self.loginScreen.errorLabel.setText("Please insert a username.")
            return

        connectionThread = threading.Thread(target=self.client.connect, args=(ADDRESS, self.loginScreen.usernameLineEdit.text()))
        self.threads.append(connectionThread)
        connectionThread.start()

        # Times out after 2.00 seconds
        ticker = 0
        while not self.client.connected and ticker < 20:
            ticker += 1
            print("ticker:", ticker)
            time.sleep(0.1)
            pass
        if self.client.connected:
            self.goToMainScreen()
        else:
            self.loginScreen.errorLabel.setText("Server time out.")

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

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            gui.connect()
        event.accept()

# Has the main screen with players and board
class MainScreen(QDialog):
    def __init__(self, gui):
        super(MainScreen, self).__init__()
        loadUi("ui/main_screen.ui", self)
        self.gui = gui
        self.debugLabel.setText("TEMP_TEXT")
        self.playerCards = [
            PlayerCard(self,  21, 520, "#FF4B4B"),
            PlayerCard(self,  251, 520, "#F36CFF"),
            PlayerCard(self,  480, 520, "#6FD966")
        ]

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.gui.submitAnswer()
        event.accept()

# Has the playercard with the score and name 
class PlayerCard():
    def __init__(self, parent: QDialog, x: int, y: int, color: str):
        self.widget = QWidget(parent)
        self.color = color
        self.widget.move(x, y)
        self.widget.resize(200, 100)
        layout = QVBoxLayout(self.widget)
        self.widget.setStyleSheet("QWidget {"
        "   background: " + color + ";"
        "   border-radius: 15px;k;"
        "}")
        self.widget.nameLabel = QLabel()
        self.widget.nameLabel.setStyleSheet("QLabel {"
        "   color: white;"
        "   font: 25px \"Inter\";"
        "}")
        self.widget.scoreLabel = QLabel()
        self.widget.scoreLabel.setStyleSheet("QLabel {"
        "   color: white;"
        "   font: 20px \"Inter\";"
        "}")
        layout.addWidget(self.widget.nameLabel, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.widget.scoreLabel, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def clear(self) -> None:
        self.widget.nameLabel.clear()
        self.widget.scoreLabel.clear()


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

        # Prompt error on failure to connect      
        except Exception as e:
            print(e)
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
            gui.mainScreen.debugLabel.setText(json.dumps(responseJSON)+"\n"+gui.mainScreen.debugLabel.text())

            token = responseJSON[TKN.TKN]

            if token == TKN.PLAYER_UPDATE:
                updateThread = threading.Thread(target=self.gui.updatePlayers, args=(responseJSON, ))
                updateThread.start()

            
            elif token == TKN.CLIENT_CLOSED and self.playerNum == responseJSON[KEY.PLAYER_NUM]:
                self.connected = False

            elif token == TKN.PLAYER_ANSWER:
                pass
                #gui.mainScreen.debugLabel.setText(responseJSON[KEY.ANSWER])

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
