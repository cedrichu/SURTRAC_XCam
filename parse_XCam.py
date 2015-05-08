import numpy as np
import cv2
import base64
import xml.etree.ElementTree as ET

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

def parse_StateVector(s, num_bits_StateVector):
	state_vector = '<StateVector>'
	
	sv_index = s.find(state_vector)
	ts_return = parse_TimeStamp(s)
	
	if (sv_index != -1) and (ts_return != -1):
		sv_index += len(state_vector)
		return ts_return+' '+s[sv_index:sv_index+num_bits_StateVector]+'\n'
	else:
		return -1

def parse_TimeStamp(s):
	time_stamp = 'timestamp="'
	num_bits_timestamp = 17
	ts_index = s.find(time_stamp)
	if(ts_index != -1):
		ts_index += len(time_stamp)
		return s[ts_index:ts_index+num_bits_timestamp]
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

def parse_OSD(s):
	osd = 'LiveOSD'
	osd_index = s.find(osd)
	if(osd_index != -1):
		return 1
	else:
		return -1


def output_image(s):
	output_data = base64.b64decode(s)
	array = np.frombuffer(output_data, dtype='uint8')
	img = cv2.imdecode(array, 1)
	#img = fgbg.apply(img)
	return img

def parse_Polygons(filename):
	tree = ET.parse(filename)
	root = tree.getroot()
	points = np.zeros(shape=(1,2))
	for neighbor in root.iter('P'):
		points = np.append(points,[[int(neighbor.attrib['y'])/2, int(neighbor.attrib['x'])/2 ]],0)
	points = np.delete(points ,0 ,0)
	ret = np.zeros(shape=(4,2))
	ret = np.array([ret])
	for  i  in range(points.size/(4*2)):
		ret = np.append(ret,[points[4*i:4*(i+1)]],0)
	ret = np.delete(ret ,0 ,0)
	return ret
	


    
            