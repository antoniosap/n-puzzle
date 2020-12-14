import sys
from itertools import count
from heapq import heappush, heappop
from collections import deque
from math import inf
import ray
from ray.util import ActorPool
from npuzzle.colors import color

EMPTY_TILE = 0


def clone_and_swap(data, y0, y1):
	clone = list(data)
	tmp = clone[y0]
	clone[y0] = clone[y1]
	clone[y1] = tmp
	return tuple(clone)


def possible_moves(data, size_rows, size_cols):
	res = []
	y = data.index(EMPTY_TILE)
	if y % size_cols > 0:
		left = clone_and_swap(data, y, y - 1)
		res.append(left)
	if y % size_cols + 1 < size_cols:
		right = clone_and_swap(data, y, y + 1)
		res.append(right)
	if y - size_cols >= 0:
		up = clone_and_swap(data, y, y - size_cols)
		res.append(up)
	if y + size_cols < len(data):
		down = clone_and_swap(data, y, y + size_cols)
		res.append(down)
	return res


# ray site:
# https://github.com/ray-project/ray/issues/3644
# info site:
# https://en.wikipedia.org/wiki/Iterative_deepening_A*
# https://github.com/asarandi/n-puzzle
#
MAX_ACTORS = 4
DELAY_BEFORE_NEW_ACTOR = 4


@ray.remote
class IdaGlobals:
	def __init__(self):
		self.search_actors = []
		self.search_actors_index = 0

	def set_search_actors(self, search_actors):
		self.search_actors = search_actors

	def get_search_actors_idx(self, i):
		return self.search_actors[i]

	def set_search_actors_index(self, i):
		self.search_actors_index = i

	def get_search_actors_index(self):
		return self.search_actors_index

	def inc_search_actors_index(self):
		self.search_actors_index += 1
		return self.search_actors_index


@ray.remote
class IdaStar:
	def __init__(self, solved, HEURISTIC, TRANSITION_COST, size_rows, size_cols):
		self.solved = solved
		self.HEURISTIC = HEURISTIC
		self.TRANSITION_COST = TRANSITION_COST
		self.size_rows = size_rows
		self.size_cols = size_cols
		self.saved_path = None
		self.new_actor_request = 0
		self.bound_min = inf
		self.ig = None

	def get_path(self):
		return self.saved_path

	def set_ig(self, ig):
		self.ig = ig

	def search(self, path, g, bound, evaluated):
		self.saved_path = path
		evaluated += 1
		node = path[0]
		f = g + self.HEURISTIC(node, self.solved, self.size_rows, self.size_cols)
		if f > bound:
			return f, evaluated
		if node == self.solved:
			return True, evaluated
		if evaluated % 500000 == 0:
			print("1. bound_min: {} evaluated: {}".format(self.bound_min, evaluated))
			self.new_actor_request += 1
			if self.new_actor_request > DELAY_BEFORE_NEW_ACTOR:
				self.new_actor_request = 0
				search_actors_index = ray.get(self.ig.inc_search_actors_index.remote())
				print("3. new actor request on index: {}".format(search_actors_index))
				if search_actors_index > MAX_ACTORS:
					print("4. actors pool full: {}".format(search_actors_index))
				else:
					print(search_actors, search_actors_index)
					search_actors[search_actors_index].search.remote(path, g, bound, evaluated)
		ret = inf
		moves = possible_moves(node, self.size_rows, self.size_cols)
		for m in moves:
			if m not in path:
				path.appendleft(m)
				t, evaluated = self.search(path, g + self.TRANSITION_COST, bound, evaluated)
				if t is True:
					return True, evaluated
				if t < ret:
					ret = t
					if ret < self.bound_min:
						self.bound_min = ret
						print("2. bound_min: {} evaluated: {}".format(self.bound_min, evaluated))
				path.popleft()
		return ret, evaluated


def pida_star_search(puzzle, solved, size_rows, size_cols, HEURISTIC, TRANSITION_COST):
	ig = IdaGlobals.remote()
	sa = [IdaStar.remote(solved, HEURISTIC, TRANSITION_COST, size_rows, size_cols)] * MAX_ACTORS
	for ac in sa:
		ac.set_ig.remote(ig)
	ig.set_search_actors.remote(sa)
	search_actors_index = ray.get(ig.get_search_actors_index.remote())
	bound = HEURISTIC(puzzle, solved, size_rows, size_cols)
	path = deque([puzzle])
	evaluated = 0
	while path:
		print(color('green', "search_actors_index: {}".format(search_actors_index)))
		t, evaluated = ray.get(sa[search_actors_index].search.remote(path, 0, bound, evaluated))
		if t is True:
			path = ray.get(sa[search_actors_index].get_path.remote())
			path.reverse()
			return True, path, {'space': len(path), 'time': evaluated}
		elif t is inf:
			return False, [], {'space': len(path), 'time': evaluated}
		else:
			bound = t
		search_actors_index += 1
		if search_actors_index >= MAX_ACTORS:
			search_actors_index = 0


def a_star_search(puzzle, solved, size_rows, size_cols, HEURISTIC, TRANSITION_COST):
	c = count()
	queue = [(0, next(c), puzzle, 0, None)]
	open_set = {}
	closed_set = {}
	while queue:
		_, _, node, node_g, parent = heappop(queue)
		if node == solved:
			steps = [node]
			while parent is not None:
				steps.append(parent)
				parent = closed_set[parent]
			steps.reverse()
			return (True, steps, {'space': len(open_set), 'time': len(closed_set)})
		if node in closed_set:
			continue
		closed_set[node] = parent
		tentative_g = node_g + TRANSITION_COST
		# print(color('yellow', "tentative_g: {} queue len: {}".format(tentative_g, len(queue))))
		moves = possible_moves(node, size_rows, size_cols)
		for m in moves:
			if m in closed_set:
				continue
			if m in open_set:
				move_g, move_h = open_set[m]
				if move_g <= tentative_g:
					continue
			else:
				move_h = HEURISTIC(m, solved, size_rows, size_cols)
			open_set[m] = tentative_g, move_h
			heappush(queue, (move_h + tentative_g, next(c), m, tentative_g, node))
	return (False, [], {'space': len(open_set), 'time': len(closed_set)})
