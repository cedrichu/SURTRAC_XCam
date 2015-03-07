#client example
import socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.123.252', 20800))
#fi = open("input_1", "r")
#input_data = fi.readline()
#print input_data
#client_socket.send(input_data)
fi = open("ReqConfig_ReqAnaEnum", "r")
input_data = fi.readline()
print input_data
client_socket.send(input_data)

while 1:
    data = client_socket.recv(512)
    print "Received" , data
##    if ( data == 'q' or data == 'Q'):
##        client_socket.close()
##        break;
##    else:
##        print "RECIEVED:" , data
##        data = raw_input ( "SEND( TYPE q or Q to Quit):" )
##        if (data <> 'Q' and data <> 'q'):
##            client_socket.send(data)
##        else:
##            client_socket.send(data)
##            client_socket.close()
##            break;
