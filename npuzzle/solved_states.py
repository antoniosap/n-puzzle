def zero_first(size_rows, size_cols):
	return tuple([x for x in range(size_rows * size_cols)])


def zero_last(size_rows, size_cols):
	lst = [x for x in range(1, size_rows * size_cols)]
	lst.append(0)
	return tuple(lst)


def snail(size_rows, size_cols):
	lst = [[0 for x in range(size_rows * size_cols)] for y in range(size_rows * size_cols)]
	moves = [(0, 1), (1, 0), (0, -1), (-1, 0)]
	row = 0
	col = 0
	i = 1
	final = size_rows * size_cols
	size = size_rows * size_cols
	size -= 1
	while i is not final and size > 0:
		for move in moves:
			if i is final: break
			for _ in range(size):
				lst[row][col] = i
				row += move[0]
				col += move[1]
				i += 1
				if i is final: break
		row += 1
		col += 1
		size -= 2
	res = []
	for row in lst:
		for i in row:
			res.append(i)
	return tuple(res)


KV = {
	'zero_first': zero_first,
	'zero_last': zero_last,
	'snail': snail
}
