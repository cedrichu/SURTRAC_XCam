import numpy as np
import cv2
import base64

fgbg = cv2.BackgroundSubtractorMOG()

def parse_XCamheader(s):
    size = 0
    for x in range(0,4):
    	try:
    		size += ord(s[x])*(16**(2*x))
    	except IndexError:
    		print "Oops!  That was no valid number."
    		return -1
    return size 

def parse_StateVector(s):
	state_vector = '<StateVector>'
	time_stamp = 'timestamp="'
	num_bits_timestamp = 17
	num_bits_StateVector = 5

	sv_index = s.find(state_vector)
	ts_index = s.find(time_stamp)
	
	if (sv_index != -1) and (ts_index != -1):
		ts_index += len(time_stamp)
		sv_index += len(state_vector)
		return s[ts_index:ts_index+num_bits_timestamp]+' '+s[sv_index:sv_index+num_bits_StateVector]+'\n'
	else:
		return -1

def parse_LiveImage(s):
	live_image = 'Bits="'
	lv_index = s.find(live_image)
	end_index = s.find('" /></LiveImage>')
	if (lv_index != -1):
		return s[lv_index+6:end_index]+'\n\n'
	else:
		return -1


def output_image(s):
	output_data = base64.b64decode(s)
	array = np.frombuffer(output_data, dtype='uint8')
	img = cv2.imdecode(array, 1)
	#img = fgbg.apply(img)
	return img
    
            