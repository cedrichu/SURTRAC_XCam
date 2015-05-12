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
	fo = open(filename+'_bits.log','w')
	fo2 = open(filename+'_bits_diff.log','w')
	video_filename = filename+'_new_video.avi'

	x_coord = range(110,270,40)
	y_coord = range(110,270,40)
	#x_coord = range(110,270,40)
	#y_coord = range(120,280,40)
	
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

	fgbg = cv2.BackgroundSubtractorMOG2(-1, 100, True)
	#fgbg = cv2.BackgroundSubtractorMOG()
	fourcc = cv2.cv.CV_FOURCC('D','I','V','X')
	output_video = cv2.VideoWriter(video_filename,fourcc, 10.0, (320, 240))
	Threshold = 100
	prev_bits = np.zeros(x_size * y_size, dtype=bool)
	prev_timestamp = '0'
	count = 0

	for line in fi:
		message = xc.parse_LiveImage(line)
		timestamp = xc.parse_TimeStamp(line)
		raw_img = xc.output_image(message)
		img = fgbg.apply(raw_img)

		show_img = raw_img.copy()
		bits = np.zeros(x_size * y_size, dtype=bool)
		for i in range(x_size):
			for j in range(y_size):
				area = img[y_coord[j]:y_coord[j+1], x_coord[i]:x_coord[i+1]]
				#cv2.putText(show_img,str(i)+str(j), (x_coord[i],y_coord[j]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255))
				if int(np.sum(area)/255) > Threshold:
					cv2.polylines(show_img, np.int32([points[i][j]]), 1, (255,255,0), 5)
					bits[x_size*i + j] = 1
				else:
					cv2.polylines(show_img, np.int32([points[i][j]]), 1, (255,255,0), 1)
		
		bit_string = ''
		for bit in bits:
			if bit == True:
				bit_string += '1'
			else:
				bit_string += '0'
		fo.write(timestamp+' '+bit_string+'\n')
		
		diff_bits = bits ^ prev_bits
		if sum(diff_bits) != 0 and int(timestamp) - int(prev_timestamp) > 1000:
			# bit_string = ''
			# for bit in (diff_bits & bits):
			# 	if bit == True:
			# 		bit_string += '1'
			# 	else:
			# 		bit_string += '0'
			# prev_bit_string = ''
			# for bit in (diff_bits & prev_bits):
			# 	if bit == True:
			# 		prev_bit_string += '1'
			# 	else:
			# 		prev_bit_string += '0'
			# fo2.write(timestamp+' '+prev_bit_string+' '+bit_string+'\n')
			diff_bits = (diff_bits & bits).astype(int) - (diff_bits & prev_bits).astype(int)
			#diff_bits = diff_bits.astype(int)
			bit_string = ''
			for i,bit in enumerate(diff_bits):
				bit_string += str(bit)
				if i != len(diff_bits)-1:
					bit_string += ' '
			
			if diff_bits[0] == 1 or diff_bits[3] == 1  or diff_bits[6] == 1:
			#if diff_bits[0] == 1 or diff_bits[1] == 1  or diff_bits[2] == 1:
				count += 1
			if diff_bits[2] == -1 or diff_bits[5] == -1  or diff_bits[8] == -1:
				count -= 1
			if not sum(bits):
				count = 0

			fo2.write(timestamp+' '+bit_string+'\n')
			prev_bits = bits
			prev_timestamp = timestamp

		cv2.putText(show_img,'Enterzone: '+str(count), (30,60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255))
		cv2.putText(show_img,str(timestamp), (30,45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255))
		output_video.write(show_img)
		cv2.imshow('XCam-p', show_img)
		cv2.imshow('background', img)
		#if cv2.waitKey(50) & 0xFF == ord('q'):
			#break
		if cv2.waitKey(50) == 27:
			cv2.waitKey(-1)
		

if __name__ == "__main__":
	main(get_options())