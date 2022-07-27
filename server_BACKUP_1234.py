# TCP Server
from datetime import datetime
import json
import socket

#from numpy import broadcast
import helper
import threading
from player import Player
from strings import *
import tokens as TKN
import values as VAL
import keys as KEY

# Buzzer and timer
import time
import queue

#To generate a random game
import random

print("TCP Server")
ADDRESS = ("127.0.0.1", 8080)
BUFFER = 1024

class Server():
    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.players = []
        self.threads = [threading.Thread]
        self.bufferLength = BUFFER
        self.gameData = [[0 for i in range(5)] for j in range(6)]
        self.categories = []

    # Binds the server to the given address and start threading
    def start(self, address: tuple[str, int]) -> None:
        self.socket.bind(address)
        # TEMP
<<<<<<< Updated upstream

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
=======
        #self.listenForConnection()
>>>>>>> Stashed changes

        # Assumption: Player 1 goes first to choose a question
        currentPlayerTurn = TKN.PLAYER_1_TURN

        # Change to "while jeopardy board is not empty" here
        while True:
            # Show and update Jeopardy Board to player

            # Tell all client whose turn it is for selecting question
            #self.broadcast(self, currentPlayerTurn)

            # Listen to that player question selection - THIS HAS BEEN DONE!

            # Broadcast chosen question - THIS HAS BEEN DONE!

            # Start timer to read question while denying any buzzer 

            # After time to read ends, allow buzzer tokens and start another timer for buzzing time
            timeToBuzzInSeconds = 1
            startTime = time.time()
            threadQueue = queue.Queue()
            
            buzzTimerThread = threading.Thread(target=self.startBuzzerTimer, args=(timeToBuzzInSeconds, startTime, threadQueue))
            listenForBuzzThread = threading.Thread(target=self.listenForBuzz, args=(self.socket, threadQueue))
            
            buzzTimerThread.start()
            listenForBuzzThread.start()
            
            # Waits until one of the two threads to finish
            tokenReceived = threadQueue.get()
            
            # DELETE THIS WHEN TESTING IS DONE
            print("Result: {}".format(tokenReceived))
            
            # Time to Buzz is over
            if (tokenReceived[TKN.TKN] == TKN.TIMEOUT):
                 # DELETE THIS WHEN TESTING IS DONE
                print("Time to buzz is over\n")
                return 0
            
                # Broadcast "time to buzz is over" to all clients here
                # Do not update currentPlayerTurn and continue to the next question selection
            
            # A player buzz
            else:
                # Pause buzzTimerThread
                
                # Broadcast to all who buzz first

                # Send signal to chosen player to allow that person to answer while 
                # sending a different signal to other players to wait

                # Analyze chosen player's response and react based on the answer. 
                return 0
                

        # Final jeopardy (Optional)

        # Broadcast winner

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
                    #KEY.QUESTION:"Question "+str(msgJSON[KEY.ROW])+","+str(msgJSON[KEY.COL]),
                    KEY.QUESTION:self.gameData[msgJSON[KEY.COL]][msgJSON[KEY.ROW]]["question"],
                    KEY.ANSWER:self.gameData[msgJSON[KEY.COL]][msgJSON[KEY.ROW]]["answer"],
                }
                self.broadcast(json.dumps(questionJSON))



            if msgJSON[KEY.SEND_TYPE] == VAL.BROADCAST:
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

    def startBuzzerTimer(self, timeToBuzzInSeconds: int, startTime: float, queue):
        # Timer Settings
        timeLimit = startTime + timeToBuzzInSeconds
        
        # Timer Countdown Process
        while (timeLimit - time.time()) > 0:
            pass
        
        timeoutOccurred = {"token" : "timeout"}
        queue.put(timeoutOccurred)
    
    # Keeps on listening until TKN.PLAYER_BUZZ is received
    def listenForBuzz(self, serverSocket: socket.socket, queue):
        buzzNotReceived = True
        
        while buzzNotReceived:
            # Listen for buzz
            response = serverSocket.recv(self.bufferLength)
            helper.log(response)
            msgJSON = helper.loadJSON(response)
            
            if (msgJSON[TKN.TKN] == TKN.PLAYER_BUZZ):
                queue.put(msgJSON)
                buzzNotReceived = False
        
if __name__ == "__main__":
    server = Server()
    #server.start(ADDRESS)
    tokEN = '{"Hello": "123"}'
    
