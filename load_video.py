import parse_XCam as xc
import optparse
import numpy as np
import cv2

def get_options(args=None):
    optParser = optparse.OptionParser()
    optParser.add_option("-i", "--video-log", dest="inputfile",
                            help="import live image log")
    (options, args) = optParser.parse_args(args=args)
    return options

def main(options):
	
	filename = options.inputfile
	filename = filename[:filename.find('_image')]
	fi = open(filename+'_image.log', 'r')
	fo = open(filename+'_bits_test.log','w')
	video_filename = filename+'_new_video.avi'

	x_coord = range(110,270,40)
	y_coord = range(110,270,40)
	x_size = len(x_coord)-1
	y_size = len(y_coord)-1
	points = [[[] for j in range(y_size)] for i in range(x_size)]
	
	for i in range(x_size):
	 	for j in range(y_size):
	 		points[i][j].append([x_coord[i],y_coord[j]])
	 		points[i][j].append([x_coord[i],y_coord[j+1]])
	 		points[i][j].append([x_coord[i+1],y_coord[j+1]])
	 		points[i][j].append([x_coord[i+1],y_coord[j]])
	points = np.array(points)

	fgbg = cv2.BackgroundSubtractorMOG()
	fourcc = cv2.cv.CV_FOURCC('D','I','V','X')
	output_video = cv2.VideoWriter(video_filename,fourcc, 10.0, (320, 240))

	for line in fi:
		message = xc.parse_LiveImage(line)
		timestamp = xc.parse_TimeStamp(line)
		raw_img = xc.output_image(message)
		img = fgbg.apply(raw_img)

		show_img = raw_img.copy()
		bits = np.zeros(x_size * y_size, dtype=int)
		for i in range(x_size):
			for j in range(y_size):
				area = img[y_coord[j]:y_coord[j+1], x_coord[i]:x_coord[i+1]]
				#cv2.putText(show_img,str(i)+str(j), (x_coord[i],y_coord[j]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255))
				if int(np.sum(area)/255) > 20:
					cv2.polylines(show_img, np.int32([points[i][j]]), 1, (255,255,0), 5)
					bits[x_size*i + j] = 1
				else:
					cv2.polylines(show_img, np.int32([points[i][j]]), 1, (255,255,0), 1)
		
		bit_string = ''
		for bit in bits:
			if bit == 1:
				bit_string += '1'
			else:
				bit_string += '0'
		fo.write(timestamp+' '+bit_string+'\n')

		cv2.putText(show_img,str(timestamp), (30,45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255))
		output_video.write(show_img)
		cv2.imshow('XCam-p', show_img)
		if cv2.waitKey(50) & 0xFF == ord('q'):
			break
		

if __name__ == "__main__":
	main(get_options())