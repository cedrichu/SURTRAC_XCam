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

	init_x_coord, init_y_coord  = 110, 110
	x_step, y_step = 40, 40
	num_x_grid, num_y_grid = 3, 3
	grid = cb.Grid(init_x_coord, init_y_coord, num_x_grid, num_y_grid, x_step, y_step)
	points = grid.create_points()
	enter_boundary = [0,3,6]
	leave_boundary = [2,5,8]

	fgbg = cv2.BackgroundSubtractorMOG2(-1, 200, True)
	#fgbg = cv2.BackgroundSubtractorMOG()
	fourcc = cv2.cv.CV_FOURCC('D','I','V','X')
	output_video = cv2.VideoWriter(video_filename,fourcc, 10.0, (320, 240))
	Threshold = 100
	Time_Gap = 1000
	prev_bits = np.zeros(num_x_grid * num_y_grid, dtype=bool)
	prev_timestamp = '0'
	
	count = 0
	track = None
	window_size = 5
	stable_window = cb.StableWindow(window_size)

	x_coord = grid.x_coords()
	y_coord = grid.y_coords() 

	for frame_num, line in enumerate(fi):
		message = xc.parse_LiveImage(line)
		timestamp = xc.parse_TimeStamp(line)
		raw_img = xc.output_image(message)
		img = fgbg.apply(raw_img)

		show_img = raw_img.copy()
		bits = np.zeros(num_x_grid * num_y_grid, dtype=bool)
		for i in range(num_x_grid):
			for j in range(num_y_grid):
				area = grid.segment_image(img,i,j)
				if int(np.sum(area)/255) > Threshold:
					cv2.polylines(show_img, np.int32([points[i][j]]), 1, (255,255,0), 5)
					bits[num_x_grid*i + j] = 1
				else:
					cv2.polylines(show_img, np.int32([points[i][j]]), 1, (255,255,0), 1)
		
		bit_string = cb.bits_to_string(bits)
		output_bit_string = stable_window.filter_stable_samples(bit_string)
		if output_bit_string:
			cb.string_to_bits(output_bit_string, bits)
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
				for g1 in grid.adjacent_grids(track[0]):
					if diff_bits[g1] == 1:
					#if bits[g1] == True:
						temp_grids.append(g1)
						for g2 in grid.adjacent_grids(g1):
							if diff_bits[g2] == 1 and not g2 in temp_grids:
							#if bits[g2] == True:
								temp_grids.append(g2)
				#print timestamp, track[0], track[1], temp_grids
				track[0] = cb.update_track(track[1], diff_bits[track[0]], temp_grids, x_coord, y_coord, grid)
				track[1] = grid.mid_points(track[0])
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
						track = [eg, grid.mid_points(eg)]
						#print 'hush'
					else:
						#print 'haha', track[0]
						if not grid.is_adjacent_in_boundary(track[0], eg):
							track = [eg, grid.mid_points(eg)]
							count += 1
							#print 'hush1'
							#break
						else:
							temp_grids = [eg]
							track[0] = cb.update_track(track[1], diff_bits[track[0]], temp_grids, x_coord, y_coord, grid)
							track[1] = grid.mid_points(track[0])
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
			drawx, drawy = grid.id_to_coord(track[0])
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