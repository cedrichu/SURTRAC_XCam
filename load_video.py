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
	enter_level = 0
	leave_level = 2
	enter_boundary = (np.array(range(num_x_grid))*num_y_grid + enter_level).tolist()# [0,3,6]
	leave_boundary = (np.array(range(num_x_grid))*num_y_grid + leave_level).tolist()# [2,5,8]


	fgbg = cv2.BackgroundSubtractorMOG2(-1, 200, True)
	#fgbg = cv2.BackgroundSubtractorMOG()
	fourcc = cv2.cv.CV_FOURCC('D','I','V','X')
	output_video = cv2.VideoWriter(video_filename,fourcc, 10.0, (320, 240))
	Threshold = 100
	Time_Gap = 1000
	prev_bits = np.zeros(num_x_grid * num_y_grid, dtype=bool)
	prev_timestamp = '0'
	
	count = 0
	track = cb.Track(grid)
	window_size = 5
	window_bins = {}
	window_queue = Queue.Queue(window_size)
	stable_window = cb.StableWindow(window_size)

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
					bits[num_y_grid*i + j] = 1
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
			
			if track.is_tracked():
				temp_grids = []
				for g1 in grid.adjacent_grids(track.grid_id):
					if diff_bits[g1] == 1:
						temp_grids.append(g1)
						for g2 in grid.adjacent_grids(g1):
							if diff_bits[g2] == 1 and not g2 in temp_grids:
								temp_grids.append(g2)
				track.update_track(diff_bits, temp_grids)
				for lb in leave_boundary: 
					if track.grid_id == lb:
						track.init_track()
						break

			#Update pedestrian counts
			if enter_grids:
				for eg in enter_grids:
					#count += 1
					if not track.is_tracked():
				 		count += 1
						track.grid_id, track.coord = eg, list(grid.mid_points[eg])
					else:
						if not grid.is_adjacent_in_boundary(track.grid_id, eg):
							track.grid_id, track.coord = eg, list(grid.mid_points[eg])
							count += 1
						else:
							track.update_track(diff_bits, [eg])
							
			#if leave_grids:
			#	count -= 1				
			if not sum(bits):
				count = 0
				track.init_track()

			fo2.write(timestamp+' '+bit_string+' ['+str(count)+'] '+str(prev_bits.astype(int))+'\n')
			prev_bits = bits
			prev_timestamp = timestamp

		if track.is_tracked():
			drawx, drawy = grid.id_to_coord(track.grid_id)
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