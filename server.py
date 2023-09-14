# TCP Server
import json
import socket
import re

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
import time

print("TCP Server")
BUFFER = 1024

class Server():
    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #players variable contains all player data in a player object from player.py
        self.players = []
        self.threads = [threading.Thread]
        self.bufferLength = BUFFER
        #Game Content: gameData contains all chosen questions for the game
        self.gameData = [[0 for i in range(5)] for j in range(6)]
        #Game Content: categories contain all categories for the questions for the game
        self.categories = []
        #currentQuestion is used for figuring out what question was completed and relaying it to the clients
        self.currentQuestion = {}
        #currentQuestionValue is used to update player score in players[player_num}.score
        self.currentQuestionValue = 0
        #buzzedInPlayerNum is used to know which player is currently buzzed in
        self.buzzedInPlayerNum = VAL.NON_PLAYER

    # Binds the server to the given address and start threading
    def start(self) -> None:
        self.socket.bind(("", VAL.PORT))
        
        #Choose the categories and questions from the jeopardy data by generating a random number from 1 to 375 and saving only those values in the jeopardy database file
        file = open("jeopardy database.json",encoding="utf8")
        data = json.load(file)
        game_number = random.randint(1,375)
        #chosenData is done by going through the entire jeopardy database file and finding the apropriate keys relating to the randomly generated number
        chosenData = [x for x in data if x["game_number"]==game_number]
        file.close()

        #Creating the 2D array of questions and saving it in gameData so it can accurately reflect the game board on the server.
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

#These are all the token responses for the server side that are sent by the client:

            # Tells all clients of a closed client
            if token == TKN.CLIENT_CLOSED:
                self.broadcast(response.decode())
                self.players.remove(self.players[msgJSON[KEY.PLAYER_NUM]])
                self.reAssignPlayerNumbers()
                self.sendPlayerInfo()
                connected = False
            
            #All questions have been answered, the server now calculates the winner and responds to the token
            if token == TKN.GAME_OVER:
                self.gameOverResponse()
            
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
                self.resetGuessBool()

            #Responds to the buzzed in players answer, and calculates if that answer is correct
            if token == TKN.PLAYER_ANSWER:
                self.answerRespond(msgJSON)
                isBroadcastEnabled = False

            #Handles players leaving/joining/updating
            if token == TKN.PLAYER_UPDATE:
                self.sendPlayerInfo()

            #If the buzzed in player does not answer the question within the time limit, the server deligates their answer as incorrect.
            if token == TKN.GUESS_TIMEOUT:
                self.noGuess(msgJSON)

            #Handles the player buzzing feature, the player that buzzes in first within the time limit is able to answer the question when the first buzz is recieved,
            #it locks the other clients from sending a buzz until the question is either answered incorrectly or correctly.
            if token == TKN.PLAYER_BUZZ:
                if self.buzzedInPlayerNum != VAL.NON_PLAYER and msgJSON[KEY.STATUS]:
                    isBroadcastEnabled = False
                if self.buzzedInPlayerNum == msgJSON[KEY.PLAYER_NUM] and not msgJSON[KEY.STATUS]:
                    self.buzzedInPlayerNum = VAL.NON_PLAYER
                elif self.buzzedInPlayerNum == VAL.NON_PLAYER:
                    self.buzzedInPlayerNum = msgJSON[KEY.PLAYER_NUM]

            #Broadcasts a message to all clients.
            if msgJSON[KEY.SEND_TYPE] == VAL.BROADCAST and isBroadcastEnabled:
                self.broadcast(response.decode())
        
        self.listenForConnection()

#Functions below are used by the response tokens as "helper" functions:

    # Sends to all connected clients
    def broadcast(self, msg: str) -> None:
        msgJSON = json.loads(msg)
        msgJSON[KEY.SEND_TYPE] = VAL.BROADCAST
        
        for player in self.players:
            msgJSON[KEY.SELF_PLAYER_NUM] = player.num
            msg = json.dumps(msgJSON).encode()
            player.socket.send(msg)

    #Used for the TKN.GUESS_TIMEOUT token
    #If no one guesses
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
    
    #Used in answerRespond()
    #If all players have guessed
    def noPlayersLeft(self, msg: dict):
        time.sleep(4)
        self.noGuess(msg)

    #Used in answerRespond()
    #If all players have guessed or not.
    def anyPlayersLeft(self):
        playersLeft = False
        for player in self.players:
            if player.hasGuessed == False:
                playersLeft = True
        return playersLeft
    
    #Used for the TKN.PLAYER_ANSWER token
    #When a player answers a question, it is responded by correct/incorrect and sending it to all clients and handling the flow of the game after the response
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
            self.broadcast(json.dumps(msgJSON))
        else:
            self.players[playerNum].score -= self.currentQuestionValue
            msgJSON = {
                TKN.TKN:TKN.ANSWER_RESPONSE,
                KEY.ANSWER:answer[KEY.ANSWER],
                KEY.STATUS:False,
                KEY.PLAYER_NUM:playerNum
            }
            self.broadcast(json.dumps(msgJSON))
            self.players[playerNum].hasGuessed = True
            if not self.anyPlayersLeft():
                threading.Thread(target=self.noPlayersLeft, args=(answer, )).start()

    #Used for the TKN.PLAYER_UPDATE token
    #Updates the player data for server and all clients
    def sendPlayerInfo(self):
        msgJSON = {
            TKN.TKN:TKN.PLAYER_UPDATE,
            KEY.PLAYER_LIST:[]
        }
        for player in self.players:
            msgJSON[KEY.PLAYER_LIST].append(player.getJSON())
        self.broadcast(json.dumps(msgJSON))

    #Used for the TKN.CLIENT_CLOSED token
    #If a client is closed, it updates the player numbers
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
        
    #Used in answerRespond()
    #Determins if the answer is correct that is calculated with some leniency
    def isCorrect(self, playerAnswer, correctAnswer) -> bool:
        playAnswer = playerAnswer.lower().strip()
        rightAnswer = correctAnswer.lower().strip()

        #If user did not input an answer
        if not playAnswer:
            return False
        
        # Remove 'the' or 'The'
        if (playAnswer[0:4] == "the "):
            playAnswer = playAnswer[4:len(playAnswer)]
        if (rightAnswer[0:4] == "the "):
            rightAnswer = rightAnswer[4:len(rightAnswer)]
            
        # Remove 'a' or 'A'
        if (playAnswer[0:2] == "a "):
            playAnswer = playAnswer[2:len(playAnswer)]
        if (rightAnswer[0:2] == "a "):
            rightAnswer = rightAnswer[2:len(rightAnswer)]
            
        # Remove 's'
        if (playAnswer[len(playAnswer) - 1] == 's'):
            answerWithoutPlural = playAnswer[0:len(playAnswer)-1]
        else:
            answerWithoutPlural = playAnswer
        
        # Remove 'ing'
        if (playAnswer[len(playAnswer)-3 : len(playAnswer)] == "ing"):
            answerWithoutING = playAnswer[0:len(playAnswer)-3]
        else:
            answerWithoutING = playAnswer
            
        # Remove "to" and "an"
        if (playAnswer[0:3] == "to ") or (playAnswer[0:3] == "an "):
            playAnswer = playAnswer[3:len(playAnswer)]
        if (rightAnswer[0:3] == "to ") or (rightAnswer[0:3] == "an "):
            rightAnswer = rightAnswer[3:len(rightAnswer)]
            
        # Removing player's punctuation
        delimiterSettings = ";", "," , "-", "_", ";", '"', "(", ")"
        delimiter = '|'.join(map(re.escape, delimiterSettings))
        tmpAnswer = re.split(delimiter, playAnswer)
        playerAnswerWithoutPunctuation = self.listToString(tmpAnswer, False)
        playerAnswerWithoutPunctuation = playerAnswerWithoutPunctuation.strip()
        
        tmpAnswer = playAnswer.split(",")
        playerAnswerWithoutComma = self.listToString(tmpAnswer, True)
        
        delimiterSettings = "'s", "s'"
        delimiter = '|'.join(map(re.escape, delimiterSettings))
        tmpAnswer = re.split(delimiter, playAnswer)
        playerAnswerWithoutApostropheS = self.listToString(tmpAnswer, True)
        
        # Relaxing the correct answer
        if (rightAnswer[len(rightAnswer)-1] == 's') or (rightAnswer[len(rightAnswer)-1] == 'y'):
            correctAnswerWithoutPlural = rightAnswer[0:len(rightAnswer)-1] 
        else:
            correctAnswerWithoutPlural = rightAnswer
            
        if (rightAnswer[len(rightAnswer)-3: len(rightAnswer)] == "ing"):
            correctAnswerWithoutING = rightAnswer[0:len(rightAnswer)-3]
        else:
            correctAnswerWithoutING = rightAnswer
        
        delimiterSettings = ";", "," , "-", "_", ";",'"', "(", ")"
        delimiter = '|'.join(map(re.escape, delimiterSettings))
        tmpAnswer = re.split(delimiter, rightAnswer)
        correctAnswerWithoutPunctuation = self.listToString(tmpAnswer, False)
        correctAnswerWithoutPunctuation = correctAnswerWithoutPunctuation.strip()
        
        tmpAnswer = rightAnswer.split(",")
        correctAnswerWithoutComma = self.listToString(tmpAnswer, True)
        
        delimiterSettings = "'s", "s'"
        delimiter = '|'.join(map(re.escape, delimiterSettings))
        tmpAnswer = re.split(delimiter, rightAnswer)
        correctAnswerWithoutApostropheS = self.listToString(tmpAnswer, True)
        
        wordsInRightAnswer = rightAnswer.split()
        isPlayerAnswerRight = False
            
        # Checking the answer
        if (playAnswer == rightAnswer):
            return True
        elif (playAnswer == correctAnswerWithoutPlural) or (answerWithoutPlural == rightAnswer):
            return True
        elif (playAnswer == correctAnswerWithoutING) or (answerWithoutING == rightAnswer):
            return True
        elif (playAnswer == correctAnswerWithoutPunctuation) or (playerAnswerWithoutPunctuation == rightAnswer):
            return True
        elif (playAnswer == correctAnswerWithoutComma) or (playerAnswerWithoutComma == rightAnswer):
            return True
        elif (playAnswer == correctAnswerWithoutApostropheS) or (playerAnswerWithoutApostropheS == rightAnswer):
            return True
        for x in range(len(wordsInRightAnswer)):
            if (playAnswer == wordsInRightAnswer[x]):
                isPlayerAnswerRight = True
        if (isPlayerAnswerRight):
            return True
        return False
    
    #Used in isCorrect()
    # Returns string with spaces in between each word
    def listToString(self, list, noSpaces: bool) -> str:
            newString = ""
            for x in range(len(list)):
                newString += list[x]
                if (not noSpaces):
                    newString += " "
            return newString
    
    #Used for the TKN.PLAYER_QUESTION_SELECT token
    #When a player selects a question, it resets the guessing values that were updated in previous questions
    def resetGuessBool(self):
        for player in self.players:
            player.hasGuessed = False

    #Used for the TKN.GAME_OVER token
    #Tells the clients if they are winners or losers for displaying the final screen
    def gameOverResponse(self):
        winnerPlayerNum = 0
        highestScore = -9999
        tieGame = False
        for player in self.players:
            if player.score == highestScore:
                tieGame = True
            if player.score > highestScore:
                highestScore = player.score
                winnerPlayerNum = player.num
        msgJSON = {}
        msgJSON = {
                TKN.TKN:TKN.GAME_OVER,
                KEY.PLAYER_NUM:winnerPlayerNum,
                KEY.STATUS:tieGame
            }
        self.broadcast(json.dumps(msgJSON))
        
if __name__ == "__main__":
    server = Server()
    server.start()
    