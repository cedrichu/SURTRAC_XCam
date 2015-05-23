import parse_XCam as xc
import optparse
import numpy as np
import cv2
import Queue
import operator
import cross_boundary as cb

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

	init_coord = 110
	step = 40
	num_grid = 3

	x_coord = range(init_coord,init_coord+step*(num_grid+1),step)
	y_coord = range(init_coord,init_coord+step*(num_grid+1),step)
	#x_coord = range(110,270,40)
	#y_coord = range(120,280,40)
	
	x_size = num_grid
	y_size = num_grid
	points = [[[] for j in range(y_size)] for i in range(x_size)]
	
	for i in range(x_size):
	 	for j in range(y_size):
	 		points[i][j].append([x_coord[i],y_coord[j]])
	 		points[i][j].append([x_coord[i],y_coord[j+1]])
	 		points[i][j].append([x_coord[i+1],y_coord[j+1]])
	 		points[i][j].append([x_coord[i+1],y_coord[j]])
	points = np.array(points)
	enter_boundary = [0,3,6]
	leave_boundary = [2,5,8]

	fgbg = cv2.BackgroundSubtractorMOG2(-1, 200, True)
	#fgbg = cv2.BackgroundSubtractorMOG()
	fourcc = cv2.cv.CV_FOURCC('D','I','V','X')
	output_video = cv2.VideoWriter(video_filename,fourcc, 10.0, (320, 240))
	Threshold = 100
	Time_Gap = 1000
	prev_bits = np.zeros(x_size * y_size, dtype=bool)
	prev_timestamp = '0'
	
	count = 0
	track = None
	
	window_size = 5
	window_bins = {}
	window_queue = Queue.Queue(window_size)

	for frame_num, line in enumerate(fi):
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
		
		bit_string = cb.bits_to_string(bits)
		#fo.write(timestamp+' '+bit_string+'\n')

		#grid signal filter
		window_queue.put(bit_string)
		if not bit_string in window_bins:
			window_bins[bit_string] = 1
		else:
			window_bins[bit_string] += 1
		if window_queue.qsize() == window_size:
		 	sorted_window_bins = sorted(window_bins.items(), key=operator.itemgetter(1), reverse=True)
		 	tail = window_queue.get()
		 	window_bins[tail] -= 1
		 	if window_bins[tail] == 0:
		 		window_bins.pop(tail)
		 	#print timestamp, sorted_window_bins
		 	cb.string_to_bits(sorted_window_bins[0][0], bits)
		
		bit_string = cb.bits_to_string(bits)
		fo.write(timestamp+' '+bit_string+'\n')
		 	
		diff_bits = bits ^ prev_bits
		if sum(diff_bits) != 0:
			#if int(timestamp) - int(prev_timestamp) > Time_Gap:
			diff_bits = (diff_bits & bits).astype(int) - (diff_bits & prev_bits).astype(int)
			bit_string = ''
			for i,bit in enumerate(diff_bits):
				bit_string += str(bit)
				if i != len(diff_bits)-1:
					bit_string += ' '	
			
			enter_grids = cb.detect_enter_boundary(diff_bits, enter_boundary)
			leave_grids = cb.detect_leave_boundary(diff_bits, leave_boundary)
			#update track
			if track:
				temp_grids = []
				for g1 in cb.adjacent_grids(track[0]):
					if diff_bits[g1] == 1:
					#if bits[g1] == True:
						temp_grids.append(g1)
						for g2 in cb.adjacent_grids(g1):
							if diff_bits[g2] == 1 and not g2 in temp_grids:
							#if bits[g2] == True:
								temp_grids.append(g2)
				#print timestamp, track[0], track[1], temp_grids
				track[0] = cb.update_track(track[1], diff_bits[track[0]], temp_grids, x_coord, y_coord)
				track[1] = cb.calc_midpoint(track[0], x_coord, y_coord)
				#print timestamp, track[0], temp_grids
				for lb in leave_boundary: 
					if track[0] == lb:
						track = None
						break

			#Update pedestrian counts
			if enter_grids:
				#print enter_grids
				#count += 1
				for eg in enter_grids:
					if not track:
				 		count += 1
						track = [eg, cb.calc_midpoint(eg, x_coord,y_coord)]
						#print 'hush'
					else:
						#print 'haha', track[0]
						if not cb.is_adjacent(track[0], eg):
							track = [eg, cb.calc_midpoint(eg, x_coord,y_coord)]
							count += 1
							#print 'hush1'
							#break
						else:
							temp_grids = [eg]
							track[0] = cb.update_track(track[1], diff_bits[track[0]], temp_grids, x_coord, y_coord)
							track[1] = cb.calc_midpoint(track[0], x_coord, y_coord)
							#print 'hush2'
					#print timestamp, track[0]

			#if leave_grids:
			#	count -= 1				
			if not sum(bits):
				count = 0
				track = None

			fo2.write(timestamp+' '+bit_string+' ['+str(count)+'] '+str(prev_bits.astype(int))+'\n')
			prev_bits = bits
			prev_timestamp = timestamp

		if track:
			drawx, drawy = cb.id_to_coord(track[0])
			cv2.polylines(show_img, np.int32([points[drawx][drawy]]), 1, (255,125,0), 5)
		
		cv2.putText(show_img,'EnterZone: '+str(count), (30,60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255))
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