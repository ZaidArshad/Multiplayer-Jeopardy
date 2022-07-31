# TCP Server
from datetime import datetime
import json
from logging import raiseExceptions
from optparse import Values
import socket
from turtle import right

#from numpy import broadcast
import helper
import threading
from player import Player
from strings import *
import tokens as TKN
import values as VAL
import keys as KEY

#To generate a random game
import random

print("TCP Server")
BUFFER = 1024

class Server():
    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.players = []
        self.threads = [threading.Thread]
        self.bufferLength = BUFFER
        self.gameData = [[0 for i in range(5)] for j in range(6)]
        self.categories = []
        self.currentQuestion = {}
        self.currentQuestionValue = 0
        self.buzzedInPlayerNum = VAL.NON_PLAYER

    # Binds the server to the given address and start threading
    def start(self, address: tuple[str, int]) -> None:
        self.socket.bind(address)
        
        #Choose the categories and questions from the jeopardy data
        file = open("jeopardy database.json",encoding="utf8")
        data = json.load(file)
        game_number = random.randint(1,375)
        chosenData = [x for x in data if x["game_number"]==game_number]
        finalJepID = random.randint(1,74)
        for x in data:
            if x["category_number"]==finalJepID:
                finalJepQuestion = x
                break
        file.close()

        #Creating the 2D array of questions
        questionIndex = 0
        for category in range(6):
            self.categories.append(chosenData[questionIndex]["category"])
            for question in range(5):
                currentQuestion = chosenData[questionIndex]
                self.gameData[category][question] = currentQuestion
                questionIndex+=1
        self.listenForConnection()


    # Listens for a new connection
    def listenForConnection(self) -> None:
        self.socket.listen()
        connection = self.socket.accept()
        serverSocket = connection[0]
        print(helper.addTimestamp("Connection from " + str(connection[1])))

        # Sends connection confirmation 
        serverSocket.send(json.dumps({
            TKN.TKN:TKN.CLIENT_CONNECTED,
            KEY.SEND_TYPE:VAL.SERVER,
            KEY.STATUS:True,
            KEY.PLAYER_NUM:len(self.players)
        }).encode())

        # Listens for player name and starts a new thread to listen to this socket
        response = serverSocket.recv(self.bufferLength)
        helper.log(response)
        msgJSON = helper.loadJSON(response)
        if msgJSON[TKN.TKN] == TKN.PLAYER_JOIN:
            thread = threading.Thread(target=self.listeningThread,
                args=(serverSocket,))
            self.threads.append(thread)
            player = Player(msgJSON[KEY.PLAYER_NUM], msgJSON[KEY.PLAYER_NAME], serverSocket)
            self.players.append(player)

            self.sendPlayerInfo()
            thread.start()

        # Keeps listening for new connections until there are 3
        if (len(self.players) < 3):
            self.listenForConnection()

    # Listens to socket on the other end
    def listeningThread(self, serverSocket: socket.socket):
        connected = True

        #Send the different categories to the client
        serverSocket.send(json.dumps({
            TKN.TKN:TKN.SERVER_CATEGORY,
            KEY.SEND_TYPE:VAL.SERVER,
            KEY.CATEGORIES:self.categories,
        }).encode())

        while connected:
            isBroadcastEnabled = True
            response = serverSocket.recv(self.bufferLength)
            helper.log(response)
            msgJSON = helper.loadJSON(response)
            token = msgJSON[TKN.TKN]

            # Tells all clients of a closed client
            if token == TKN.CLIENT_CLOSED:
                self.broadcast(response.decode())
                self.players.remove(self.players[msgJSON[KEY.PLAYER_NUM]])
                self.reAssignPlayerNumbers()
                self.sendPlayerInfo()
                connected = False
            
            #Sends the chosen question to all clients
            if token == TKN.PLAYER_QUESTION_SELECT:
                questionJSON = {
                    TKN.TKN:TKN.SERVER_QUESTION_SELECT,
                    KEY.ROW:msgJSON[KEY.ROW],
                    KEY.COL:msgJSON[KEY.COL],
                    KEY.QUESTION:self.gameData[msgJSON[KEY.COL]][msgJSON[KEY.ROW]]["question"],
                    KEY.ANSWER:self.gameData[msgJSON[KEY.COL]][msgJSON[KEY.ROW]]["answer"],
                }
                self.broadcast(json.dumps(questionJSON))
                self.currentQuestion = questionJSON
                self.currentQuestionValue = (msgJSON[KEY.ROW]+1)*200

            if token == TKN.PLAYER_ANSWER:
                self.answerRespond(msgJSON)
                isBroadcastEnabled = False

            if token == TKN.PLAYER_UPDATE:
                self.sendPlayerInfo()

            if token == TKN.GUESS_TIMEOUT:
                self.noGuess(msgJSON)

            if token == TKN.PLAYER_BUZZ:
                if self.buzzedInPlayerNum != VAL.NON_PLAYER and msgJSON[KEY.STATUS]:
                    isBroadcastEnabled = False
                if self.buzzedInPlayerNum == msgJSON[KEY.PLAYER_NUM] and not msgJSON[KEY.STATUS]:
                    self.buzzedInPlayerNum = VAL.NON_PLAYER
                elif self.buzzedInPlayerNum == VAL.NON_PLAYER:
                    self.buzzedInPlayerNum = msgJSON[KEY.PLAYER_NUM]

            if msgJSON[KEY.SEND_TYPE] == VAL.BROADCAST and isBroadcastEnabled:
                self.broadcast(response.decode())
        
        self.listenForConnection()


    # Sends to all connected clients
    def broadcast(self, msg: str) -> None:
        msgJSON = json.loads(msg)
        msgJSON[KEY.SEND_TYPE] = VAL.BROADCAST
        
        for player in self.players:
            msgJSON[KEY.SELF_PLAYER_NUM] = player.num
            msg = json.dumps(msgJSON).encode()
            player.socket.send(msg)

    def noGuess(self, msg: dict):
        msgJSON = {}
        msgJSON = {
                TKN.TKN:TKN.ANSWER_RESPONSE,
                KEY.ANSWER:self.currentQuestion[KEY.QUESTION],
                KEY.STATUS:True,
                KEY.PLAYER_NUM:VAL.NON_PLAYER,
                KEY.ROW:self.currentQuestion[KEY.ROW],
                KEY.COL:self.currentQuestion[KEY.COL],
                KEY.CURRENT_PLAYER_TURN:msg[KEY.CURRENT_PLAYER_TURN]
            }
        self.broadcast(json.dumps(msgJSON))
    
    #def changeTurn(self, player_num:int):
    #    msgJSON = {
    #            TKN.TKN:TKN.PLAYER_TURN,
    #            KEY.CURRENT_PLAYER_TURN:player_num,
    #        }
    #    self.broadcast(json.dumps(msgJSON))

    def answerRespond(self, answer: dict):
        playerNum = answer[KEY.PLAYER_NUM]
        msgJSON = {}
        if (self.isCorrect(answer[KEY.ANSWER], self.currentQuestion[KEY.QUESTION])):
            self.players[playerNum].score += self.currentQuestionValue
            msgJSON = {
                TKN.TKN:TKN.ANSWER_RESPONSE,
                KEY.ANSWER:answer[KEY.ANSWER],
                KEY.STATUS:True,
                KEY.PLAYER_NUM:playerNum,
                KEY.ROW:self.currentQuestion[KEY.ROW],
                KEY.COL:self.currentQuestion[KEY.COL],
                KEY.CURRENT_PLAYER_TURN:playerNum
            }
            #self.changeTurn(playerNum)
        else:
            self.players[playerNum].score -= self.currentQuestionValue
            msgJSON = {
                TKN.TKN:TKN.ANSWER_RESPONSE,
                KEY.ANSWER:answer[KEY.ANSWER],
                KEY.STATUS:False,
                KEY.PLAYER_NUM:playerNum
            }
        self.broadcast(json.dumps(msgJSON))

    def sendPlayerInfo(self):
        msgJSON = {
            TKN.TKN:TKN.PLAYER_UPDATE,
            KEY.PLAYER_LIST:[]
        }
        for player in self.players:
            msgJSON[KEY.PLAYER_LIST].append(player.getJSON())
        self.broadcast(json.dumps(msgJSON))

    def reAssignPlayerNumbers(self):
        num = 0
        for player in self.players:
            player.num = num
            num += 1

    # Closes all of the client and joins all the threads
    def close(self):
        for player in self.players:
            player.socket.close()
        for thread in self.threads:
            thread.join()
        self.socket.close()
        
    def isCorrect(self, playerAnswer, correctAnswer) -> bool:
        answer = playerAnswer.lower().strip()
        rightAnswer = correctAnswer.lower().strip()
        
        # Remove 'the' or 'The'
        if (answer[0:4] == "the "):
            answer = answer[4:len(answer)]
        if (rightAnswer[0:4] == "the "):
            rightAnswer = rightAnswer[4:len(rightAnswer)]
            
        # Remove 'a' or 'A'
        if (answer[0:2] == "a "):
            answer = answer[2:len(answer)]
        if (rightAnswer[0:2] == "a "):
            rightAnswer = rightAnswer[2:len(rightAnswer)]
            
        # Remove 's'
        if (answer[len(answer) - 1] == 's'):
            answerWithoutPlural = answer[0:len(answer)-1]
        else:
            answerWithoutPlural = answer
        
        # Remove 'ing'
        if (answer[len(answer)-3 : len(answer)] == "ing"):
            answerWithoutING = answer[0:len(answer)-3]
        else:
            answerWithoutING = answer
            
        # Relaxing the answer
        if (rightAnswer[len(rightAnswer)-1] == 's') or (rightAnswer[len(rightAnswer)-1] == 'y'):
            correctAnswerWithoutPlural = rightAnswer[0:len(rightAnswer)-1] 
        else:
            correctAnswerWithoutPlural = rightAnswer
            
        if (rightAnswer[len(rightAnswer)-3: len(rightAnswer)] == "ing"):
            correctAnswerWithoutING = rightAnswer[0:len(rightAnswer)-3]
        else:
            correctAnswerWithoutING = rightAnswer
        
        wordsInRightAnswer = rightAnswer.split()
        isPlayerAnswerRight = False
            
        # Checking the answer
        if (answer == rightAnswer):
            return True
        elif (answer == correctAnswerWithoutPlural) or (answerWithoutPlural == rightAnswer):
            return True
        elif (answer == correctAnswerWithoutING) or (answerWithoutING == rightAnswer):
            return True
        for x in range(len(wordsInRightAnswer)):
            if (answer == wordsInRightAnswer[x]):
                isPlayerAnswerRight = True
        if (isPlayerAnswerRight):
            return True
        return False
        
if __name__ == "__main__":
    server = Server()
    server.start(VAL.ADDRESS)
    