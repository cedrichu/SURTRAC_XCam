import numpy as np
import cv2
import Queue
import operator

def detect_enter_boundary(diff_list, enter_boundary):
	activated_boundary = []
	for eb in enter_boundary:
		if diff_list[eb] == 1:
			activated_boundary.append(eb)

	if not activated_boundary:
		return None
	else:
		return activated_boundary

def detect_leave_boundary(diff_list, leave_boundary):
	activated_boundary = []
	for lb in leave_boundary:
		if diff_list[lb] == -1:
			activated_boundary.append(lb)
	if not activated_boundary:
		return None
	else:
		return activated_boundary

#TODO when changing grids
def adjacent_grids(id):
	adjacent_list = [[1,3],[2,4],[5],[0,4,6],[1,5,7],[2,8],[3,7],[4,8],[5]]
	for i, adj in enumerate(adjacent_list):
		if id == i:
			return adj

#TODO when changing grids
def id_to_coord(id):
	return id/3, id-3*(id/3)

def bits_to_string(bits):
	bit_string = ''
	for bit in bits:
		if bit == True:
			bit_string += '1'
		else:
			bit_string += '0'
	return bit_string

def string_to_bits(bit_string, bits):
	for i in range(len(bits)):
		if bit_string[i] == '1':
			bits[i] = True
		else:
			bits[i] = False

def calc_midpoint(id, x_coord, y_coord):
	coord = id_to_coord(id)
	x = (float(x_coord[coord[0]])+ float(x_coord[coord[0]+1]))/2
	y = (float(y_coord[coord[1]])+ float(y_coord[coord[1]+1]))/2
	return [x,y]

def update_track(track_point, diff_bit, subseq_grid, x_coord, y_coord):
	
	if diff_bit == -1 and subseq_grid:
		#print diff_bit, subseq_grid
		track_point = calc_midpoint(subseq_grid[0], x_coord,y_coord)
		del subseq_grid[0]

	for sg in subseq_grid:
		x,y = calc_midpoint(sg, x_coord,y_coord)
		track_point[0] = (float(track_point[0])+x)/2
		track_point[1] = (float(track_point[1])+y)/2

	x_size = len(x_coord)-1
	y_size = len(y_coord)-1
	
	for i in range(x_size):
		if x_coord[i] <= track_point[0] < x_coord[i+1]:
			x = i
			break
	for j in range(y_size):
		if y_coord[j] <= track_point[1] < y_coord[j+1]:
			y = j
			break

	return x*y_size+y

def is_adjacent(id1, id2):
	
	x1, y1 = id_to_coord(id1)
	x2, y2 = id_to_coord(id2)
	x = x2 - x1
	y = y2 - y1
	if abs(x) <= 1 and y == 0:
		return True
	return False