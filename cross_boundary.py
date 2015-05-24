import numpy as np
import cv2
import Queue
import operator

class StableWindow:
	def __init__(self, window_size):
		self._window_size = window_size
		self._window_bins = {}
		self._window_queue = Queue.Queue(window_size)

	def filter_stable_samples(self, bit_string):
		#grid signal filter
		self._window_queue.put(bit_string)
		if not bit_string in self._window_bins:
			self._window_bins[bit_string] = 1
		else:
			self._window_bins[bit_string] += 1
		if self._window_queue.qsize() == self._window_size:
		 	sorted_window_bins = sorted(self._window_bins.items(), key=operator.itemgetter(1), reverse=True)
		 	tail = self._window_queue.get()
		 	self._window_bins[tail] -= 1
		 	if self._window_bins[tail] == 0:
		 		self._window_bins.pop(tail)
		 	#print timestamp, sorted_window_bins
		 	return sorted_window_bins[0][0]

		return None

class Grid:
	def __init__(self, init_x_coord, init_y_coord, num_x_grid, num_y_grid, x_step, y_step):
		self._init_x_coord = init_x_coord
		self._init_y_coord = init_y_coord
		self._num_x_grid = num_x_grid
		self._num_y_grid = num_y_grid
		self._x_step = x_step
		self._y_step = y_step
		self._x_coord = range(init_x_coord,init_x_coord+x_step*(num_x_grid+1),x_step)
		self._y_coord = range(init_y_coord,init_y_coord+y_step*(num_y_grid+1),y_step)
		self._mid_points = self.init_mid_points()

	@property
	def mid_points(self):
		return self._mid_points
	@property
	def x_coord(self):
		return self._x_coord
	@property
	def y_coord(self):
		return self._y_coord
	@property
	def num_x_grid(self):
		return self._num_x_grid
	@property
	def num_y_grid(self):
		return self._num_y_grid

	def create_points(self):
		points = [[[] for j in range(self._num_y_grid)] for i in range(self._num_x_grid)]
		for i in range(self._num_x_grid):
			for j in range(self._num_y_grid):
				points[i][j].append([self._x_coord[i],self._y_coord[j]])
				points[i][j].append([self._x_coord[i],self._y_coord[j+1]])
				points[i][j].append([self._x_coord[i+1],self._y_coord[j+1]])
				points[i][j].append([self._x_coord[i+1],self._y_coord[j]])
		return np.array(points)
	
	def segment_image(self, img, i,j):
		return img[self._y_coord[j]:self._y_coord[j+1], self._x_coord[i]:self._x_coord[i+1]]

	def init_mid_points(self):
		id_list = range(self._num_x_grid*self._num_y_grid)
		mid_points = []
		for id in id_list:
			coord = self.id_to_coord(id)
			x = (float(self._x_coord[coord[0]])+ float(self._x_coord[coord[0]+1]))/2
			y = (float(self._y_coord[coord[1]])+ float(self._y_coord[coord[1]+1]))/2
			mid_points.append((x,y))
		return mid_points

	def id_to_coord(self, id):
		return id/self._num_y_grid, id-self._num_y_grid*(id/self._num_y_grid)

	def coord_to_id(self, x, y):
		return x*self._num_y_grid + y

	def is_adjacent_in_boundary(self, id1, id2):
		x1, y1 = self.id_to_coord(id1)
		x2, y2 = self.id_to_coord(id2)
		x = x2 - x1
		y = y2 - y1
		if abs(x) <= 1 and y == 0:
			return True
		return False

	def adjacent_grids(self, id):
		x,y = self.id_to_coord(id)
		adjacent = []
		if not x-1 < 0:
			adjacent.append(self.coord_to_id(x-1, y))
		if not y+1 > self._num_y_grid-1:
			adjacent.append(self.coord_to_id(x, y+1))
		if not x+1 > self._num_x_grid-1:
			adjacent.append(self.coord_to_id(x+1, y))

		return adjacent
	
	

class Track:
	def __init__(self, grid):
		self._grid_id = None
		self._coord = []
		self._grid = grid

	@property
	def grid(self):
		return self._grid
	@property
	def grid_id(self):
		return self._grid_id
	@property
	def coord(self):
		return self._coord
	@grid.setter
	def grid(self, grid):
		self._grid = grid
	@grid_id.setter
	def grid_id(self ,id):
		self._grid_id = id
	@coord.setter
	def coord(self, x, y):
		self._coord.append(x)
		self._coord.append(y)

	def update_track(self, diff_bits, subseq_grid):
		g = self.grid
		if diff_bits[self.grid_id] == -1 and subseq_grid:
			#print diff_bit, subseq_grid
			self._coord = list(g.mid_points[subseq_grid[0]])
			del subseq_grid[0]

		for sg in subseq_grid:
			x,y = list(g.mid_points[sg])
			self.coord[0] = (float(self.coord[0])+x)/2
			self.coord[1] = (float(self.coord[1])+y)/2

		
		for i in range(g.num_x_grid):
			if g.x_coord[i] <= self.coord[0] < g.x_coord[i+1]:
				x = i
				break
		for j in range(g.num_y_grid):
			if g.y_coord[j] <= self.coord[1] < g.y_coord[j+1]:
				y = j
				break

		self.grid_id = x*g.num_y_grid+y
		




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




# def update_track(track_point, diff_bit, subseq_grid, x_coord, y_coord, grid):
	
# 	if diff_bit == -1 and subseq_grid:
# 		#print diff_bit, subseq_grid
# 		track_point = grid.mid_points(subseq_grid[0])
# 		del subseq_grid[0]

# 	for sg in subseq_grid:
# 		x,y = grid.mid_points(sg)
# 		track_point[0] = (float(track_point[0])+x)/2
# 		track_point[1] = (float(track_point[1])+y)/2

# 	x_size = len(x_coord)-1
# 	y_size = len(y_coord)-1
	
# 	for i in range(x_size):
# 		if x_coord[i] <= track_point[0] < x_coord[i+1]:
# 			x = i
# 			break
# 	for j in range(y_size):
# 		if y_coord[j] <= track_point[1] < y_coord[j+1]:
# 			y = j
# 			break

# 	return x*y_size+y

