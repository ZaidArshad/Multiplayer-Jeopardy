# TCP Server
import socket

print("TCP Server")

# Generating server
message = "from server"
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    	
address = ("127.0.0.1", 8080)		
serverSocket.bind(address)	
bufferLength = 500

serverSocket.listen()		
while True:
    clientSocket = serverSocket.accept()[0]
    response = clientSocket.recv(bufferLength)
    print(response.decode())
    clientSocket.send(message.encode())
    break
