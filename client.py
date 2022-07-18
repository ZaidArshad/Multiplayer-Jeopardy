# TCP Client
import socket
import time
print("TCP Client")           
 
# Generating socket stream
message = "from client"
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
address = ("127.0.0.1", 8080)
bufferLength = 500

clientSocket.connect(address)
clientSocket.send(message.encode())
response = clientSocket.recv(bufferLength)
print(response.decode())
clientSocket.close()
     