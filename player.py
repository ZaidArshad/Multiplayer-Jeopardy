import tokens as TKN
import keys as KEY
import socket

class Player():
    def __init__(self, num: int, name: str, socket: socket.socket) -> None:
        self.num = num
        self.name = name
        self.score = 0
        self.socket = socket
        self.hasGuessed = False

    def getJSON(self) -> dict:
        return {
            TKN.TKN:TKN.PLAYER_INFO,
            KEY.PLAYER_NUM:self.num,
            KEY.PLAYER_NAME:self.name,
            KEY.PLAYER_SCORE:self.score
        }