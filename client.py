#client example
import socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.123.252', 20800))
#client_socket.connect(('localhost', 9999))
fi = open("ReqVerInfo", "r")
input_data = fi.readline()
print input_data
client_socket.send(input_data)

while 1:
    data = client_socket.recv(512)
    print "Received" , data
