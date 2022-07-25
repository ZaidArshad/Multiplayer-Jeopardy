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

print("TCP Server")
ADDRESS = ("127.0.0.1", 8080)
BUFFER = 1024

class Server():
    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.players = []
        self.threads = [threading.Thread]
        self.bufferLength = BUFFER

    # Binds the server to the given address and start threading
    def start(self, address: tuple[str, int]) -> None:
        self.socket.bind(address)

        # TEMP
        #self.listenForConnection()

        # Assumption: Player 1 goes first to choose a question
        currentPlayerTurn = TKN.PLAYER_1_TURN

        # Change to "while jeopardy board is not empty" here
        while True:
            # Show and update Jeopardy Board to player

            # Tell all client whose turn it is for selecting question
            self.broadcast(self, currentPlayerTurn)

            # Listen to that player question selection

            # Broadcast chosen question

            # Start timer to read question while denying any buzzer (and punishing them?)

            # After time to read ends, allow buzzer tokens and start another timer for buzzing time
            timeToBuzzInSeconds = 30
            startTime = time.time()
            threadQueue = queue.Queue()
            
            buzzTimerThread = threading.Thread(target=self.startBuzzerTimer, args=(timeToBuzzInSeconds, startTime, threadQueue))
            listenForBuzzThread = threading.Thread(target=self.listenForBuzz, args=(self.socket, threadQueue))
            
            buzzTimerThread.start()
            listenForBuzzThread.start()
            
            # Waits until one of the threads to finish
            tokenReceived = threadQueue.get()
            
            # DELETE THIS WHEN TESTING IS DONE
            print("Result: {}".format(tokenReceived))
            
            # Time to Buzz is over
            if (tokenReceived == TKN.TIMEOUT):
                print("Time to buzz is over\n")
                
                # Do not update currentPlayerTurn and continue to the next question selection
            
            # A player buzz
            else:
                # Pause buzzTimerThread
                
                # Broadcast to all who buzz first

                # Send signal to chosen player to allow that person to answer while 
                # sending a different signal to other players to wait

                # Analyze chosen player's response and react based on the answer. 
                return 0
                

        # Final jeopardy

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
            print(timeLimit - time.time())
        
        queue.put(TKN.TIMEOUT)
    
    def pauseBuzzerTimer(self, startTime: float):
        timeLeft = time.time() - startTime
        return timeLeft
    
    # Keeps on listening until TKN.PLAYER_BUZZ is received
    def listenForBuzz(self, serverSocket: socket.socket, queue):
        response = serverSocket.recv(self.bufferLength)
        helper.log(response)
        msgJSON = helper.loadJSON(response)
        
        if msgJSON[TKN.TKN] != TKN.PLAYER_BUZZ:
            response = serverSocket.recv(self.bufferLength)
            helper.log(response)
            msgJSON = helper.loadJSON(response)
        
        # Pause timer and broadcast who buzz to all client
        queue.put(TKN.PLAYER_BUZZ)

if __name__ == "__main__":
    server = Server()
    server.start(ADDRESS)
