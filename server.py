# TCP Server
from datetime import datetime
import json
import socket
import helper
import threading
from player import Player
from strings import *
import tokens as TKN
import values as VAL
import keys as KEY

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
        #TEMP
        self.listenForConnection()

    # Listens for a new connection
    def listenForConnection(self) -> None:
        self.socket.listen()
        connection = self.socket.accept()
        serverSocket = connection[0]
        print(helper.addTimestamp("Connection from " + str(connection[1])))

        serverSocket.send(json.dumps({
            TKN.TKN:TKN.CLIENT_CONNECTED,
            KEY.SEND_TYPE:VAL.SERVER,
            KEY.STATUS:True,
            KEY.PLAYER_NUM:len(self.players)
        }).encode())

        response = serverSocket.recv(self.bufferLength)
        helper.log(response)
        
        msgJSON = helper.loadJSON(response)
        if msgJSON[TKN.TKN] == TKN.PLAYER_JOIN:
            thread = threading.Thread(target=self.listeningThread,
                args=(len(self.players),serverSocket,))
            self.threads.append(thread)
            player = Player(msgJSON[KEY.PLAYER_NUM], msgJSON[KEY.PLAYER_NAME], serverSocket)
            self.players.append(player)

            for player in self.players:
                self.broadcast(json.dumps(player.getJSON()))
            thread.start()

        if (len(self.players) < 3):
            self.listenForConnection()

    # Listens to socket on the other end
    def listeningThread(self, playerNum: int, serverSocket: socket.socket):
        connected = True
        while connected:
            response = serverSocket.recv(self.bufferLength)
            helper.log(response)
            msgJSON = helper.loadJSON(response)
            token = msgJSON[TKN.TKN]

            if token == TKN.CLIENT_CLOSED:
                self.broadcast(response.decode())
                serverSocket.close()
                self.players.remove(self.players[playerNum])
                connected = False
        
        self.listenForConnection()


    # Sends to all connected clients
    def broadcast(self, msg: str) -> None:
        msgJson = json.loads(msg)
        msgJson[KEY.SEND_TYPE] = VAL.BROADCAST
        msg = json.dumps(msgJson).encode()
        for player in self.players:
            player.socket.send(msg)

    # Closes all of the client and joins all the threads
    def close(self):
        for player in self.players:
            player.socket.close()
        for thread in self.threads:
            thread.join()
        self.socket.close()

if __name__ == "__main__":
    server = Server()
    server.start(ADDRESS)
