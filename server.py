# TCP Server
from datetime import datetime
import json
import socket
import threading
from strings import *
import tokens as TKN
import values as VAL
import keys as KEY

print("TCP Server")
ADDRESS = ("127.0.0.1", 8080)
BUFFER = 1024

def addTimestamp(msg: str) -> str:
    return datetime.now().strftime("<%H:%M:%S> ") + msg

def log(msg: bytes) -> str:
    print(addTimestamp(msg.decode()))

class Server():
    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
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
        print(addTimestamp("Connection from " + str(connection[1])))

        serverSocket.send(json.dumps({
            TKN.TKN:TKN.CLIENT_CONNECTED,
            KEY.SEND_TYPE:VAL.SERVER,
            KEY.STATUS:True,
            KEY.PLAYER_NUM:len(self.clients)
        }).encode())

        self.clients.append(serverSocket)
        response = serverSocket.recv(self.bufferLength)
        log(response)
        self.broadcast(response.decode())
        thread = threading.Thread(target=self.listeningThread, args=(serverSocket,))
        self.threads.append(thread)
        thread.start()

        if (len(self.clients) < 3):
            self.listenForConnection()

    # Listens to socket on the other end
    def listeningThread(self, serverSocket: socket.socket):
        connected = True
        while connected:
            response = serverSocket.recv(self.bufferLength)
            log(response)
            msg = json.loads(response.decode())
            token = msg[TKN.TKN]
            if token == TKN.CLIENT_CLOSED:
                serverSocket.close()
                self.clients.remove(serverSocket)
                connected = False


    # Sends to all connected clients
    def broadcast(self, msg: str) -> None:
        msgJson = json.loads(msg)
        msgJson[KEY.SEND_TYPE] = VAL.BROADCAST
        msg = json.dumps(msgJson).encode()
        for client in self.clients:
            client.send(msg)

    def close(self):
        for client in self.clients:
            client.close()
        for thread in self.threads:
            thread.join()
        self.socket.close()

if __name__ == "__main__":
    server = Server()
    server.start(ADDRESS)
