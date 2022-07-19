# TCP Client
from datetime import datetime
import json
import socket
import threading
from strings import *
import tokens as TKN
import values as VAL
import keys as KEY

print("TCP Client")
ADDRESS = ("127.0.0.1", 8080)
BUFFER = 1024

def addTimestamp(msg: str) -> str:
    return datetime.now().strftime("<%H:%M:%S> ") + msg

def log(msg: bytes) -> str:
    print(addTimestamp(msg.decode()))

def load(msg: bytes) -> dict:
    return json.loads(msg.decode())

class Client():
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bufferLength = BUFFER

    # Connects to the server, prints confirmation
    def connect(self, address: tuple[str, int]) -> None:
        self.socket.connect(address)
        response = self.socket.recv(self.bufferLength)
        log(response)
        responseJson = load(response)
        self.playerNum = responseJson[KEY.PLAYER_NUM]
        self.playerName = "TEMPUSERNAME"

        if responseJson[KEY.STATUS]:
            self.socket.send(json.dumps({
                TKN.TKN:TKN.PLAYER_JOIN,
                KEY.SEND_TYPE:VAL.CLIENT,
                KEY.PLAYER_NUM:self.playerNum,
                KEY.PLAYER_NAME:self.playerName
            }).encode())

        response = self.socket.recv(self.bufferLength)
        log(response)

    def send(self, msg: str) -> None:
        self.socket.send(msg.encode())

    def close(self) -> None:
        self.socket.close()

if __name__ == "__main__":
    client = Client()
    thread = threading.Thread(target=client.connect, args=(ADDRESS,))
    thread.start()

    msg = None
    while msg != "":
        msg = input()
        client.send(msg)
        if msg == "":
            client.close()

    thread.join()