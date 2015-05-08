import socket
import parse_XCam as xc
import sys
import cv2
import logging
import numpy as np


#Client parameters
#SERVER_IP = 'surtrac.wv.cs.cmu.edu'
SERVER_IP = '192.168.100.2'
SERVER_PORT = 20800
STARTLIVE_FILE = 'StartLive'
buf_size = 512
hsize = 4
#Output files
output_filename = 'two_user_2_'
VIDEO_FILE = output_filename+'output_video.avi'
STATEVECTOR_FILE = output_filename+'state_vector.log'
IMAGE_FILE = output_filename+'image.log'
POLYGONS_FILE = output_filename+'osd.xml'

logging.basicConfig(filename='debug.log',level=logging.INFO)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, SERVER_PORT))
print "start client..."

fi = open(STARTLIVE_FILE, 'r')
state_vector = open(STATEVECTOR_FILE, 'w')
image_file = open(IMAGE_FILE, 'w')
osd_file = open(POLYGONS_FILE,'w')

input_data = fi.readline()
client_socket.send(input_data)
print 'send StartLive...'

residule_header = ''
fourcc = cv2.cv.CV_FOURCC('D','I','V','X')
output_video = cv2.VideoWriter(VIDEO_FILE,fourcc, 10.0, (320, 240))
OSD_imported = False
num_polygons = 9

while 1:
    client_socket.send(input_data)
    data = client_socket.recv(buf_size)
    if residule_header != '':
        logging.debug('residule: ' + residule_header)
        data = residule_header + data
        residule_header = ''
    data_size, index = len(data), 0

    while data_size != 0:        
        XML_size =  xc.parse_XCamheader(data[index:index+hsize])
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
        parsed_message = xc.parse_LiveImage(XML_message)
        if(parsed_message != -1):
            image_file.write(XML_message+'\n')
            img = xc.output_image(parsed_message)   
            if OSD_imported == True:
                cv2.putText(img,str(statebits_timestamp), (30,45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255))
                for i in range(num_polygons):
                    #print i
                    if statebits[i] == '0':
                        cv2.polylines(img, np.int32([points[i]]), 1, (0,0,255), 1)
                    else:
                        cv2.polylines(img, np.int32([points[i]]), 1, (255,0,0), 1)
            output_video.write(img)
            cv2.imshow('XCam-p', img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
       
        parsed_message = xc.parse_StateVector(XML_message, num_polygons)
        if(parsed_message != -1):
            statebits_timestamp = parsed_message[:parsed_message.find(' ')]
            statebits = parsed_message[parsed_message.find(' ')+1:-1]
            state_vector.write(parsed_message)

        if (xc.parse_OSD(XML_message) == 1) and (OSD_imported == False):
            osd_file.write(XML_message)
            osd_file.close()
            points = xc.parse_Polygons(POLYGONS_FILE)
            num_polygons =  points.size/(4*2)
            statebits = '0'*num_polygons
            statebits_timestamp = '0'
            OSD_imported = True


video_write.release()
cv2.destroyAllWindows()                      

                
                



    
    
