import socket
import parse_XCam
import sys
import cv2

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.123.252', 20800))
print "start client..."


fi = open('StartLive', 'r')
live_image = open('live_image.txt', 'w')
state_vector = open('state_vector.txt', 'w')

input_data = fi.readline()
client_socket.send(input_data)
print 'send StartLive...'

buf_size = 512
hsize = 4
while 1:
    data = client_socket.recv(buf_size)
    data_size = len(data)
    index = 0
    while data_size != 0:
        XML_size =  parse_XCam.parse_XCamheader(data[index:index+hsize])
        if XML_size == -1:
            break
        data_size -= hsize
        index += hsize
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
                        index = 0
                        if data_size >= rest_XML_size:
                                XML_message += data[:rest_XML_size]
                                data_size -= rest_XML_size
                                index += rest_XML_size
                                rest_XML_size = 0
                        else:
                                XML_message += data[:]
                                rest_XML_size -= data_size
                                data_size = 0
        
        parsed_message = parse_XCam.parse_LiveImage(XML_message)
        if(parsed_message != -1):
            parse_XCam.output_image(parsed_message)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            live_image.write(parsed_message)

        parsed_message = parse_XCam.parse_StateVector(XML_message)
        if(parsed_message != -1):
            state_vector.write(parsed_message)
            
	    
                                

                
                



    
    
