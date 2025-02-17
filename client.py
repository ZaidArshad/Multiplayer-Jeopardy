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
from PyQt5.QtGui import QPalette, QColor
from PyQt5 import QtTest

print("TCP Client")
BUFFER = 1024

UI_WIDTH = 700
UI_HEIGHT = 600


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

        self.animationThread = AnimationThread()
        self.animationThread.buzzSignal.connect(self.buzzPlayer)
        self.animationThread.unBuzzSignal.connect(self.unBuzzPlayer)

        # Connecting functions to signals
        self.interfaceUpdateThread = InterfaceUpdateThread()
        self.interfaceUpdateThread.answerLineEditTextSignal.connect(
            self.mainScreen.questionPrompt.answerLineEdit.setText)
        self.interfaceUpdateThread.playerCardSignal.connect(self.updatePlayers) 
        self.interfaceUpdateThread.answerLineEditColorSignal.connect(
            self.mainScreen.questionPrompt.setLineEditColor)
        self.interfaceUpdateThread.answerLineEditClearSignal.connect(
            self.mainScreen.questionPrompt.resetLineEdit)
        self.interfaceUpdateThread.playerCardChoosingSignal.connect(
            self.mainScreen.lockInPlayer)
        self.interfaceUpdateThread.promptUpdateSignal.connect(self.initializePrompt)

    # Buzzes the player through the GUI
    def buzzPlayer(self, playerNum: int) -> None:
        self.mainScreen.playerCards[playerNum].buzzedIn()
    
    # Unbuzzes the player through the GUI  
    def unBuzzPlayer(self, playerNum: int) -> None:
        self.mainScreen.playerCards[playerNum].buzzedOut()

    # Fills in the data for the question prompt
    def initializePrompt(self, category: str, question: str, value: int) -> None:
        self.mainScreen.questionPrompt.timerLabel.show()
        self.mainScreen.questionPrompt.valueLabel.setText("$" + str(value*200))
        self.mainScreen.questionPrompt.categoryLabel.setText(category)
        self.mainScreen.questionPrompt.questionLabel.setText(question)
        self.mainScreen.questionPrompt.answerLineEdit.hide()
        self.client.answeredQuestions += 1

    # Goes to the main screen
    def goToMainScreen(self) -> None:
        self.window.setCurrentIndex(self.window.currentIndex() + 1)

    # Submits an answer to the server
    def submitAnswer(self) -> None:
        answer = self.mainScreen.questionPrompt.answerLineEdit.text()
        answerJSON = {
            TKN.TKN:TKN.PLAYER_ANSWER,
            KEY.ANSWER:answer,
            KEY.CURRENT_PLAYER_TURN:self.mainScreen.gui.client.turn,
        }
        self.client.send(answerJSON, True)

    # Easily send a message that only contains a token 
    def submitToken(self, token: str) -> None:
        self.client.send({TKN.TKN:token})

    # Tells the server which question has been chosen
    def chooseQuestion(self, row: int, col: int) -> None:
        # if its not your turn, do not allow question selection
        if self.client.turn != self.client.playerNum:
            return
        
        questionSelectionJSON = {
            TKN.TKN:TKN.PLAYER_QUESTION_SELECT,
            KEY.ROW:row,
            KEY.COL:col
        }
        self.mainScreen.questionPrompt.categoryLabel.setText(self.client.categories[col])
        self.mainScreen.questionPrompt.readyToAnswer = False
        self.client.send(questionSelectionJSON)

    # Creates and formats window and widgets for GUI
    def initializeWindow(self) -> QStackedWidget:
        window = QStackedWidget()
        window.setFixedSize(UI_WIDTH, UI_HEIGHT)
        window.addWidget(self.loginScreen)
        window.addWidget(self.mainScreen)
        window.show()
        return window

    # Updates the list of players
    def updatePlayers(self, json: dict) -> None:
        self.client.playerNum = json[KEY.SELF_PLAYER_NUM]

        for playerJSON in json[KEY.PLAYER_LIST]:
            self.updatePlayer(playerJSON)

        numOfPlayers = len(json[KEY.PLAYER_LIST])
        for i in range(2, numOfPlayers-1, -1):
            self.mainScreen.playerCards[i].clear()

    # Updates a single player
    def updatePlayer(self, playerJSON: dict) -> None:
        self.mainScreen.playerCards[playerJSON[KEY.PLAYER_NUM]].widget.nameLabel.setText(playerJSON[KEY.PLAYER_NAME])
        self.mainScreen.playerCards[playerJSON[KEY.PLAYER_NUM]].widget.scoreLabel.setText("$"+str(playerJSON[KEY.PLAYER_SCORE])+" ")

    # Connects the sets up the client to the server
    def connect(self) -> None:
        if len(self.loginScreen.usernameLineEdit.text()) == 0:
            self.loginScreen.errorLabel.setText("Please insert a username.")
            return

        connectionThread = threading.Thread(target=self.client.connect, args=(VAL.ADDRESS, self.loginScreen.usernameLineEdit.text()))
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
        if self.client.connected:
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

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            gui.connect()
        event.accept()

# Has the main screen with players and board
class MainScreen(QDialog):
    def __init__(self, gui: GUI):
        super(MainScreen, self).__init__()
        self.gui = gui
        loadUi("ui/main_screen.ui", self)
        
        self.widgetIndex = 0
        self.board = Board(self)
        self.questionPrompt = QuestionPrompt(self)
        self.stackedWidget = QStackedWidget()
        self.stackedWidgetHolder.addWidget(self.stackedWidget)
        self.stackedWidget.addWidget(self.board)
        self.stackedWidget.addWidget(self.questionPrompt)
        self.setFixedSize(700, 600)

        self.promptThread = PromptThread()
        self.promptThread.togglePromptSignal.connect(self.togglePrompt)

        self.debugLabel.hide()
        self.debugLabel.setText("THIS IS DEBUG LOG PRESS ESCAPE TO SHOW AND HIDE")
        self.playerCards = [
            PlayerCard(self,  21, 520, "#FF4B4B"),
            PlayerCard(self,  251, 520, "#F36CFF"),
            PlayerCard(self,  480, 520, "#6FD966")
        ]
        self.playerCards[1].greyOut()
        self.playerCards[2].greyOut()

    # Color in a player and grey out other players
    def lockInPlayer(self, playerNum: int) -> None:
        self.playerCards[playerNum].colorIn()
        for i in range(len(self.playerCards)):
            if i != playerNum:
                self.playerCards[i].greyOut()
    
    # Colors in all players
    def colorPlayers(self) -> None:
        for player in self.playerCards:
            player.colorIn()

    # Switches between the game board and question prompt
    def togglePrompt(self) -> None:
        if self.widgetIndex == VAL.WIDGET_PROMPT:
            self.widgetIndex = VAL.WIDGET_BOARD
        else:
            self.widgetIndex = VAL.WIDGET_PROMPT
            self.colorPlayers()
        self.stackedWidget.setCurrentIndex(self.widgetIndex)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            if self.debugLabel.isHidden():
                self.debugLabel.show()
            else:
                self.debugLabel.hide()
        
        event.accept()

# Widget that has the question and line edit for answering 
class QuestionPrompt(QWidget):
    def __init__(self, mainscreen: MainScreen):
        super(QuestionPrompt, self).__init__()
        loadUi("ui/question_prompt.ui", self)
        self.mainScreen = mainscreen
        self.isBuzzed = False
        self.readyToAnswer = False
        self.hasGuessed = False
        
        self.answerLineEditThread = AnswerLineEditThread()
        self.answerLineEditThread.enabledSignal.connect(self.enableAnswerLineEdit)

        self.buzzTimerThread = TimerThread()
        self.buzzTimerThread.displaySignal.connect(self.updateTimer)
        self.buzzTimerThread.finishedSignal.connect(self.enableGuessing)

        self.guessTimerThread = TimerThread()
        self.guessTimerThread.displaySignal.connect(self.updateTimer)
        self.guessTimerThread.finishedSignal.connect(self.terminateGuessing)

        self.answerTimerThread = TimerThread()
        self.answerTimerThread.displaySignal.connect(self.updateTimer)
        self.answerTimerThread.finishedSignal.connect(self.answer)

        self.setFocusPolicy(Qt.StrongFocus)

    # Updates the timer on the GUI
    def updateTimer(self, time: int) -> None:
        self.timerLabel.setText(str(time))
    
    # Disables guessing for all players
    def terminateGuessing(self) -> None:
        if self.mainScreen.gui.client.playerNum == 0 and self.readyToAnswer:
            msgJSON = {
                TKN.TKN:TKN.GUESS_TIMEOUT,
                KEY.CURRENT_PLAYER_TURN:self.mainScreen.gui.client.turn
            }
            self.mainScreen.gui.client.send(msgJSON)
        self.readyToAnswer = False

    # Starts the timer, shows the textbox and allows players to buzz
    def enableGuessing(self):
        self.guessTimerThread.timeLength = 15
        self.guessTimerThread.start()
        self.answerLineEdit.show()
        self.readyToAnswer = True
        self.hasGuessed = False

    # Sets the color of the textbox
    def setLineEditColor(self, color: str) -> None:
        self.setStyleSheet("QLineEdit {"
        "   background-color:"+ color +";"
        "}")

    # Clears the line edit and sets it white
    def resetLineEdit(self) -> None:
        self.setLineEditColor("#FFFFFF")
        self.answerLineEdit.clear()

    # Sends the server message of buzzing in
    def buzzed(self, status: bool) -> None:
        self.mainScreen.gui.client.send({
            TKN.TKN:TKN.PLAYER_BUZZ,
            KEY.STATUS:status
        }, True)

    # Allows the user to type in the text box
    def enableAnswerLineEdit(self, status: bool) -> None:
        self.isBuzzed = status
        self.answerLineEdit.setEnabled(status)

    # Submits the player's answer and disables guessing
    def answer(self):
        if self.isBuzzed and self.readyToAnswer:
            self.buzzed(False)
            time.sleep(2)
            self.readyToAnswer = False
            self.mainScreen.gui.submitAnswer()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.answer()
        if event.key() == Qt.Key.Key_Space:
            if not self.isBuzzed and self.readyToAnswer and not self.hasGuessed:
                self.buzzed(True)
                self.hasGuessed = True
        event.accept()
    

# Widget that holds the game board with all the buttons
class Board(QWidget):
    def __init__(self, mainscreen: MainScreen):
        super(Board, self).__init__()
        loadUi("ui/board.ui", self)
        self.mainScreen = mainscreen
        self.buttons = [[0 for i in range(5)] for j in range(6)]

        # Initializing the buttons
        for col in range(6):
            for row in range(5):
                button = QPushButton()
                sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                sizePolicy.setRetainSizeWhenHidden(True)
                button.setSizePolicy(sizePolicy)
                button.setText("$" + str((row+1)*200))
                button.clicked.connect(lambda state, row=row, col=col:(
                    self.mainScreen.gui.chooseQuestion(row, col)))
                self.gridLayout.addWidget(button, row+1, col)
                self.buttons[col][row] = button

# Has the playercard with the score and name 
class PlayerCard():
    def __init__(self, parent: QDialog, x: int, y: int, color: str):
        self.widget = QWidget(parent)
        self.parent = parent
        self.color = color
        self.widget.move(x, y)
        self.xPos = x
        self.yPos = y
        self.widget.resize(200, 300)
        layout = QVBoxLayout(self.widget)
        self.setColor(color)
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

    # Clears the name and score
    def clear(self) -> None:
        self.widget.nameLabel.clear()
        self.widget.scoreLabel.clear()

    # Greys the player card
    def greyOut(self) -> None:
        self.setColor("#7D7D7D")

    # Colors the player card
    def colorIn(self) -> None:
        self.setColor(self.color)

    # Buzz in animation
    def buzzedIn(self) -> None:
        self.widget.anim = QPropertyAnimation(self.widget, "pos".encode())
        self.widget.anim.setEndValue(QPoint(self.widget.x(), self.widget.y()-35))
        self.widget.anim.setDuration(200)
        self.widget.anim.start()

    # Buzz out animation
    def buzzedOut(self) -> None:
        self.widget.anim = QPropertyAnimation(self.widget, "pos".encode())
        self.widget.anim.setEndValue(QPoint(self.xPos, self.yPos))
        self.widget.anim.setDuration(200)
        self.widget.anim.start()

    # Sets the color of the player card
    def setColor(self, color: str) -> None:
        self.widget.setStyleSheet("QWidget {"
        "   background: " + color + ";"
        "   border-radius: 15px;k;"
        "}")


# Controls the GUI <-> Client <-> Server connection
class Client():
    def __init__(self, gui: GUI):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gui = gui
        self.bufferLength = BUFFER
        self.connected = False
        self.categories = []
        self.turn = 0
        self.answeredQuestions = 0 #Change number to make the game end sooner (default ends after 30 questions)

    # Connects to the server, prints confirmation
    def connect(self, address: tuple[str, int], playerName: str) -> None:
        self.playerName = playerName

        # Try to connect to the server
        try:
            self.socket.connect(address)
            responseJson = self.receive()
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

                responseJson = self.receive()
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
    def receive(self) -> dict:
        response = self.socket.recv(self.bufferLength)
        helper.log(response)
        responseJson = helper.loadJSON(response)
        return responseJson
        

    # Repeatedly listens to the server for any messages
    def listeningThread(self) -> None:
        while self.connected:
            responseJSON = self.receive()
            #gui.mainScreen.debugLabel.setText(json.dumps(responseJSON)+"\n"+gui.mainScreen.debugLabel.text())

            token = responseJSON[TKN.TKN]

            # Updates the player cards with the server data
            if token == TKN.PLAYER_UPDATE:
                self.gui.interfaceUpdateThread.setPlayerCardData(responseJSON)

            # Disconnects this client
            elif token == TKN.CLIENT_CLOSED and self.playerNum == responseJSON[KEY.PLAYER_NUM]:
                self.connected = False

            # Handles a player buzzing in
            elif token == TKN.PLAYER_BUZZ:
                handleThread = threading.Thread(target=self.handleBuzz, args=(responseJSON, ))
                handleThread.start()
            
            # Updates the GUI with the categories from the server
            elif token == TKN.SERVER_CATEGORY:
                self.categories = responseJSON[KEY.CATEGORIES]
                self.assignCategories(self.categories.copy())
            
            # Updates the question prompt with the server data
            elif token == TKN.SERVER_QUESTION_SELECT:
                self.gui.interfaceUpdateThread.setPromptUpdate(self.categories[responseJSON[KEY.COL]], responseJSON[KEY.ANSWER], responseJSON[KEY.ROW]+1)
                self.gui.mainScreen.promptThread.start()
                
                #Start the timer to allow time for the players to read the question
                self.gui.mainScreen.questionPrompt.buzzTimerThread.timeLength = 5
                self.gui.mainScreen.questionPrompt.buzzTimerThread.start()
            
            # Ends the game
            elif token == TKN.GAME_OVER:
                self.gameOverScreen(responseJSON)
                self.gui.mainScreen.promptThread.start()

            # Updates based on the correctness of the player's answer
            elif token == TKN.ANSWER_RESPONSE:
                handleThread = threading.Thread(target=self.handleAnswerResponse, args=(responseJSON, ))
                handleThread.start()
                self.gui.interfaceUpdateThread.setAnswerLineEditText(responseJSON[KEY.ANSWER])
                self.gui.mainScreen.questionPrompt.answerLineEditThread.status = False
                self.gui.mainScreen.questionPrompt.answerLineEditThread.start()

            # Shows the players answer on all clients
            elif token == TKN.PLAYER_ANSWER:
                self.gui.interfaceUpdateThread.setAnswerLineEditText(responseJSON[KEY.ANSWER])
                self.gui.mainScreen.questionPrompt.answerLineEditThread.status = False
                self.gui.mainScreen.questionPrompt.answerLineEditThread.start()

    # Fills in the data for the question prompt
    def initializePrompt(self, category: str, question: str) -> None:
        self.gui.mainScreen.questionPrompt.timerLabel.show()
        self.gui.mainScreen.questionPrompt.categoryLabel.setText(category)
        self.gui.mainScreen.questionPrompt.questionLabel.setText(question)
        self.gui.mainScreen.questionPrompt.answerLineEdit.hide()
        self.answeredQuestions += 1
    
    # Shows the game over screen
    def gameOverScreen(self, responseJSON: dict) -> None:
        self.gui.mainScreen.questionPrompt.timerLabel.hide()
        self.gui.mainScreen.questionPrompt.categoryLabel.setText("GAME OVER")
        winnerPlayerNum = responseJSON[KEY.PLAYER_NUM]
        if self.playerNum == winnerPlayerNum:
            self.gui.mainScreen.questionPrompt.questionLabel.setText("YOU WIN!")
        else:
            self.gui.mainScreen.questionPrompt.questionLabel.setText("YOU LOSE!")
        if responseJSON[KEY.STATUS]:
            self.gui.mainScreen.questionPrompt.questionLabel.setText("TIE GAME!")
        self.gui.mainScreen.questionPrompt.readyToAnswer = False
        self.gui.mainScreen.questionPrompt.hasGuessed = False
        self.gui.mainScreen.questionPrompt.answerLineEdit.hide()

    # Verifies a valid buzz
    def handleBuzz(self, responseJSON: dict):
        self.gui.animationThread.isBuzzed =  responseJSON[KEY.STATUS]
        self.gui.animationThread.playerNum = responseJSON[KEY.PLAYER_NUM]
        self.gui.mainScreen.questionPrompt.guessTimerThread.terminate()
        self.gui.mainScreen.questionPrompt.answerTimerThread.timeLength = 15
        self.gui.mainScreen.questionPrompt.answerTimerThread.start()
        self.gui.animationThread.start()

        if self.playerNum == responseJSON[KEY.PLAYER_NUM]:
            self.gui.mainScreen.questionPrompt.answerLineEditThread.status = True
            self.gui.mainScreen.questionPrompt.answerLineEditThread.start()
        else:
            self.gui.mainScreen.questionPrompt.readyToAnswer = False

    # Updates based on the correctness of the player's answer
    def handleAnswerResponse(self, responseJSON: dict) -> None:
        self.gui.mainScreen.questionPrompt.answerTimerThread.terminate()
        if responseJSON[KEY.STATUS]:
                self.gui.interfaceUpdateThread.setAnswerLineEditColor("#00FF00")
                self.gui.mainScreen.board.buttons[responseJSON[KEY.COL]][responseJSON[KEY.ROW]].hide()
                self.turn = responseJSON[KEY.CURRENT_PLAYER_TURN]
                self.gui.interfaceUpdateThread.setPlayerCardChoosingNum(responseJSON[KEY.CURRENT_PLAYER_TURN])
                if responseJSON[KEY.PLAYER_NUM] == VAL.NON_PLAYER:
                    self.gui.mainScreen.questionPrompt.guessTimerThread.terminate()
        else:
            self.gui.interfaceUpdateThread.setAnswerLineEditColor("#FF0000")
            self.gui.mainScreen.questionPrompt.guessTimerThread.start()

        time.sleep(2)
        if self.playerNum == responseJSON[KEY.PLAYER_NUM]:
            self.send({TKN.TKN:TKN.PLAYER_UPDATE})
        if responseJSON[KEY.STATUS]:
            self.gui.mainScreen.promptThread.start()
        else:
            self.gui.mainScreen.questionPrompt.readyToAnswer = True
        self.gui.interfaceUpdateThread.clearAnswerLineEdit()

        # If all 30 questions have been answered show the game over screen
        if self.answeredQuestions == 30 and responseJSON[KEY.STATUS]:
            if self.playerNum == responseJSON[KEY.PLAYER_NUM] or (responseJSON[KEY.PLAYER_NUM] == VAL.NON_PLAYER and self.playerNum == 0):
                time.sleep(4)
                self.send({TKN.TKN:TKN.GAME_OVER})

    # Formats the category text to split on separate lines if too long
    def trimCategory(self, category: str, maxLength: int) -> str:
        if len(category) <= maxLength:
            return category

        currentWordLength = 0
        for i in range(len(category)):
            c = category[i]
            if c == " ":
                currentWordLength = 0
            if currentWordLength >= maxLength and category[i:len(category)-1] != "":
                category = category[0:i] + "\n-"+category[i:len(category)-1]
                currentWordLength = 0
            currentWordLength += 1
        return category


    # Fills in the GUI with the categories
    def assignCategories(self, categories: list) -> None:
        for i in range(len(categories)):
            categories[i] = self.trimCategory(categories[i], 13)

        self.gui.mainScreen.board.label.setText(categories[0])
        self.gui.mainScreen.board.label_2.setText(categories[1])
        self.gui.mainScreen.board.label_3.setText(categories[2])
        self.gui.mainScreen.board.label_4.setText(categories[3])
        self.gui.mainScreen.board.label_5.setText(categories[4])
        self.gui.mainScreen.board.label_6.setText(categories[5])

    # Takes a message and add a header with client info and sends to server
    # Can broadcast to other clients if toBroadcast is set
    def send(self, msg: dict, toBroadcast: bool = False) -> None:
        sendType = VAL.CLIENT
        if toBroadcast:
            sendType = VAL.BROADCAST

        standardHeader = {
            KEY.SEND_TYPE:sendType,
            KEY.PLAYER_NUM:self.playerNum,
            KEY.PLAYER_NAME:self.playerName,
        }
        msg.update(standardHeader)
        msgJson = json.dumps(msg)
        self.socket.send(msgJson.encode())

### GUI SIGNALS ###
class AnimationThread(QThread):
    playerNum = -1
    isBuzzed = False
    buzzSignal = pyqtSignal(int)
    unBuzzSignal = pyqtSignal(int)
    def run(self):
        if self.isBuzzed:
            self.buzzSignal.emit(self.playerNum)
        else:
            self.unBuzzSignal.emit(self.playerNum)

class PromptThread(QThread):
    togglePromptSignal = pyqtSignal()
    def run(self):
        self.togglePromptSignal.emit()

class AnswerLineEditThread(QThread):
    enabledSignal = pyqtSignal(bool)
    status = False

    displayedDisplay = pyqtSignal(str)
    text = ""
    def run(self):
        self.enabledSignal.emit(self.status)
        self.enabledSignal.emit(self.status)

class TimerThread(QThread):
    timeLength = 0
    displaySignal = pyqtSignal(int)
    finishedSignal = pyqtSignal()
    def run(self) -> None:
        self.displaySignal.emit(self.timeLength)
        for seconds in range(self.timeLength):
            time.sleep(1)
            elapsed = self.timeLength - seconds - 1
            self.displaySignal.emit(elapsed)
            
        self.timeLength = 0
        self.finishedSignal.emit()

class InterfaceUpdateThread(QThread):
    INTERFACE_OBJECTS = 6
    update = [False]*INTERFACE_OBJECTS

    answerLineEditTextSignal = pyqtSignal(str)
    answerLineEditText = ""

    playerCardSignal = pyqtSignal(object)
    playerCardData = {}

    answerLineEditColorSignal = pyqtSignal(str)
    answerLineEditColor = "#FFFFFF"

    answerLineEditClearSignal = pyqtSignal()

    playerCardChoosingSignal = pyqtSignal(int)
    playerCardChoosingNum = VAL.NON_PLAYER

    promptUpdateSignal = pyqtSignal(str, str, int)
    promptUpdateCategory = ""
    promptUpdateQuestion = ""
    promptValue = 0

    def run(self):
        if self.update[0]:
            self.answerLineEditTextSignal.emit(self.answerLineEditText)

        if self.update[1]:   
            self.playerCardSignal.emit(self.playerCardData)

        if self.update[2]:
            self.answerLineEditColorSignal.emit(self.answerLineEditColor)

        if self.update[3]:
            self.answerLineEditClearSignal.emit()

        if self.update[4]:
            self.playerCardChoosingSignal.emit(self.playerCardChoosingNum)
        
        if self.update[5]:
            self.promptUpdateSignal.emit(self.promptUpdateCategory, self.promptUpdateQuestion, self.promptValue)

        self.update = [False]*self.INTERFACE_OBJECTS

    def setAnswerLineEditText(self, text: str):
        self.update[0] = True
        self.answerLineEditText = text
        self.start()

    def setPlayerCardData(self, data: object):
        self.update[1] = True
        self.playerCardData = data
        self.start()

    def setAnswerLineEditColor(self, color: str):
        self.update[2] = True
        self.answerLineEditColor = color
        self.start()

    def clearAnswerLineEdit(self):
        self.update[3] = True
        self.start()

    def setPlayerCardChoosingNum(self, num: int):
        self.update[4] = True
        self.playerCardChoosingNum = num
        self.start()

    def setPromptUpdate(self, category: str, question: str, value: int):
        self.update[5] = True
        self.promptUpdateCategory = category
        self.promptUpdateQuestion = question
        self.promptValue = value
        self.start()
### GUI SIGNALS END ###

if __name__ == "__main__":
    gui = GUI()
    gui.app.exec()
    gui.close()
