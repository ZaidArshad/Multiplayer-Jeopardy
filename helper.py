from datetime import datetime
import json 


def addTimestamp(msg: str) -> str:
    return datetime.now().strftime("<%H:%M:%S> ") + msg

def log(msg: bytes) -> str:
    print(addTimestamp(msg.decode()))

def loadJSON(msg: bytes) -> dict:
    return json.loads(msg.decode())