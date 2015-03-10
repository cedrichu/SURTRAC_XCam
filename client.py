#client example
import socket

def parse_XCamheader(s):
	size = 0
	for x in range(0,4):
		size += ord(s[x])*(16**(2*x))
	return size 

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#client_socket.connect(('192.168.123.252', 20800))
client_socket.connect(('localhost', 9999))
fi = open('ReqConfig_ReqAnaEnum', 'r')
input_data = fi.readline()
print input_data
client_socket.send(input_data)

buf_size = 512
hsize = 4
index = 0
while 1:
    data = client_socket.recv(buf_size)
    data_size = len(data)
    while data_size != 0:
    	XML_size =  parse_XCamheader(data[index:index+hsize])
    	data_size -= hsize
    	index += hsize
    	if data_size > 0:
    		if data_size >= XML_size:
    			XML_message = data[index:index+XML_size]
    			data_size -= XML_size
    			index += XML_size
    		else:
    			XML_message = data[index:]
    			rest_XML_size = XML_size - len(XML_message)
    			while (rest_XML_size != 0):
    				data = client_socket.recv(buf_size)
    				data_size = len(data)
    				if data_size >= rest_XML_size:
    					XML_message += data[:rest_XML_size]
    					rest_XML_size = 0
    					data_size -= rest_XML_size
    					index += rest_XML_size
    				else:
    					XML_message += data[:]
    					rest_XML_size -= data_size
    					data_size = 0
    					index = 0
    	print XML_message
    					

    			
    			



    
    