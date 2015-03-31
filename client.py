import socket
import parse_XCam
import sys
import cv2
import logging


logging.basicConfig(filename='debug.log',level=logging.INFO)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.123.252', 20800))
print "start client..."

fi = open('StartLive', 'r')
state_vector = open('state_vector.log', 'w')
image_file = open('image.log', 'w')

input_data = fi.readline()
client_socket.send(input_data)
print 'send StartLive...'

buf_size = 512
hsize = 4
residule_header = ''
fourcc = cv2.cv.CV_FOURCC('D','I','V','X')
output_video = cv2.VideoWriter('output_video.avi',fourcc, 10.0, (320, 240))

while 1:
    client_socket.send(input_data)
    data = client_socket.recv(buf_size)
    
    if residule_header != '':
        logging.debug('residule: ' + residule_header)
        data = residule_header + data
        residule_header = ''
    
    data_size, index = len(data), 0
    
    while data_size != 0:
        
        XML_size =  parse_XCam.parse_XCamheader(data[index:index+hsize])
        if XML_size == -1:
            break
        
        data_size, index = data_size-hsize, index+hsize
        
        if data_size >= XML_size:
                XML_message = data[index:index+XML_size]
                data_size, index = data_size - XML_size , index + XML_size
                
                if data_size < hsize and data_size > 0:
                    logging.debug('residule 1 data_size: ' + str(data_size))
                    residule_header = data[index:]
                    data_size = 0
        else:
                XML_message = data[index:]
                rest_XML_size = XML_size - len(XML_message)
                while (rest_XML_size != 0):
                        data = client_socket.recv(buf_size)
                        
                        data_size, index = len(data), 0

                        if data_size >= rest_XML_size:
                                XML_message += data[:rest_XML_size]
                                data_size, index = data_size - rest_XML_size , index + rest_XML_size
                                rest_XML_size = 0
                                
                                if data_size < hsize and data_size > 0:
                                    logging.debug('residule 2 data_size: ' + str(data_size))
                                    residule_header = data[index:]
                                    data_size = 0

                        else:
                                XML_message += data[:]
                                rest_XML_size, data_size = rest_XML_size - data_size, 0

        logging.debug('parsed_message: '+XML_message)
        
        parsed_message = parse_XCam.parse_LiveImage(XML_message)
        if(parsed_message != -1):
            image_file.write(XML_message+'\n\n')
            video_timestamp = parse_XCam.parse_TimeStamp(XML_message)
            img = parse_XCam.output_image(parsed_message)
            cv2.putText(img,str(video_timestamp), (30,45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255))
            output_video.write(img)
            cv2.imshow('XCam-p', img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
       
        parsed_message = parse_XCam.parse_StateVector(XML_message)
        if(parsed_message != -1):
            state_vector.write(parsed_message)



print 'leave client...'
video_write.release()
cv2.destroyAllWindows()                      

                
                



    
    
