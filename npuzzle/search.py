import sys
from itertools import count
from heapq import heappush, heappop
from collections import deque
from math import inf
import ray
from npuzzle.colors import color

EMPTY_TILE = 0

def clone_and_swap(data,y0,y1):
	clone = list(data)
	tmp = clone[y0]
	clone[y0] = clone[y1]
	clone[y1] = tmp
	return tuple(clone)

def possible_moves(data, size_rows, size_cols):
	res = []
	y = data.index(EMPTY_TILE)
	if y % size_cols > 0:
		left = clone_and_swap(data,y,y-1)
		res.append(left)
	if y % size_cols + 1 < size_cols:
		right = clone_and_swap(data,y,y+1)
		res.append(right)
	if y - size_cols >= 0:
		up = clone_and_swap(data,y,y-size_cols)
		res.append(up)
	if y + size_cols < len(data):
		down = clone_and_swap(data,y,y+size_cols)
		res.append(down)
	return res


def ida_star_search_ray(puzzle, solved, size_rows, size_cols, HEURISTIC, TRANSITION_COST):
	@ray.remote
	def search(path, g, bound, evaluated):
		evaluated += 1
		node = path[0]
		f = g + HEURISTIC(node, solved, size_rows, size_cols)
		if f > bound:
			return f, evaluated
		if node == solved:
			return True, evaluated
		if evaluated % 500000 == 0:
			print(color('yellow', "bound: {} evaluated: {}".format(bound, evaluated)))
		ret = inf
		moves = possible_moves(node, size_rows, size_cols)
		for m in moves:
			if m not in path:
				path.appendleft(m)
				t, evaluated = ray.get(search.remote(path, g + TRANSITION_COST, bound, evaluated))
				if t is True:
					return True, evaluated
				if t < ret:
					ret = t
				path.popleft()
		return ret, evaluated

	bound = HEURISTIC(puzzle, solved, size_rows, size_cols)
	path = deque([puzzle])
	evaluated = 0
	while path:
		t, evaluated = ray.get(search.remote(path, 0, bound, evaluated))
		if t is True:
			path.reverse()
			return True, path, {'space': len(path), 'time': evaluated}
		elif t is inf:
			return False, [], {'space': len(path), 'time': evaluated}
		else:
			bound = t


def ida_star_search_seq(puzzle, solved, size_rows, size_cols, HEURISTIC, TRANSITION_COST):
	def search(path, g, bound, evaluated):
		evaluated += 1
		node = path[0]
		f = g + HEURISTIC(node, solved, size_rows, size_cols)
		if f > bound:
			return f, evaluated
		if node == solved:
			return True, evaluated
		if evaluated % 500000 == 0:
			print(color('yellow', "bound: {} evaluated: {}".format(bound, evaluated)))
		ret = inf
		moves = possible_moves(node, size_rows, size_cols)
		for m in moves:
			if m not in path:
				path.appendleft(m)
				t, evaluated = search(path, g + TRANSITION_COST, bound, evaluated)
				if t is True:
					return True, evaluated
				if t < ret:
					ret = t
				path.popleft()
		return ret, evaluated

	bound = HEURISTIC(puzzle, solved, size_rows, size_cols)
	path = deque([puzzle])
	evaluated = 0
	while path:
		t, evaluated = search(path, 0, bound, evaluated)
		if t is True:
			path.reverse()
			return True, path, {'space': len(path), 'time': evaluated}
		elif t is inf:
			return False, [], {'space': len(path), 'time': evaluated}
		else:
			bound = t

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
			return (True, steps, {'space':len(open_set), 'time':len(closed_set)})
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
	return (False, [], {'space':len(open_set), 'time':len(closed_set)})
