from npuzzle import solved_states
# import ray


def uniform_cost(puzzle, solved, size_rows, size_cols):
	return 0


def hamming(candidate, solved, size_rows, size_cols):  # aka tiles out of place
	res = 0
	for i in range(size_rows * size_cols):
		if candidate[i] != 0 and candidate[i] != solved[i]:
			res += 1
	return res


def gaschnig(candidate, solved, size_rows, size_cols):
	res = 0
	candidate = list(candidate)
	solved = list(solved)
	while candidate != solved:
		zi = candidate.index(0)
		if solved[zi] != 0:
			sv = solved[zi]
			ci = candidate.index(sv)
			candidate[ci], candidate[zi] = candidate[zi], candidate[ci]
		else:
			for i in range(size_rows * size_cols):
				if solved[i] != candidate[i]:
					candidate[i], candidate[zi] = candidate[zi], candidate[i]
					break
		res += 1
	return res


def manhattan(candidate, solved, size_rows, size_cols):
	res = 0
	size = size_rows * size_cols
	for i in range(size_rows * size_cols):
		if candidate[i] != 0 and candidate[i] != solved[i]:
			ci = solved.index(candidate[i])
			y = (i // size) - (ci // size)
			x = (i % size) - (ci % size)
			res += abs(y) + abs(x)
	return res


def linear_conflicts(candidate, solved, size_rows, size_cols):
	def count_conflicts(candidate_row, solved_row, size_rows, size_cols, ans=0):
		size = size_rows * size_cols
		counts = [0 for x in range(size)]
		for i, tile_1 in enumerate(candidate_row):
			if tile_1 in solved_row and tile_1 != 0:
				for j, tile_2 in enumerate(candidate_row):
					if tile_2 in solved_row and tile_2 != 0:
						if tile_1 != tile_2:
							if (solved_row.index(tile_1) > solved_row.index(tile_2)) and i < j:
								counts[i] += 1
							if (solved_row.index(tile_1) < solved_row.index(tile_2)) and i > j:
								counts[i] += 1
		if max(counts) == 0:
			return ans * 2
		else:
			i = counts.index(max(counts))
			candidate_row[i] = -1
			ans += 1
			return count_conflicts(candidate_row, solved_row, size_rows, size_cols, ans)

	res = manhattan(candidate, solved, size_rows, size_cols)
	size = size_rows * size_cols
	candidate_rows = [[] for y in range(size_rows)]
	candidate_columns = [[] for x in range(size_cols)]
	solved_rows = [[] for y in range(size_rows)]
	solved_columns = [[] for x in range(size_cols)]
	for y in range(size_rows):
		for x in range(size_cols):
			idx = (y * size_cols) + x
			candidate_rows[y].append(candidate[idx])
			candidate_columns[x].append(candidate[idx])
			solved_rows[y].append(solved[idx])
			solved_columns[x].append(solved[idx])
	for i in range(size_rows):
		res += count_conflicts(candidate_rows[i], solved_rows[i], size_rows, size_cols)
	for i in range(size_cols):
		res += count_conflicts(candidate_columns[i], solved_columns[i], size_rows, size_cols)
	return res


KV = {
	'hamming': hamming,
	'gaschnig': gaschnig,
	'manhattan': manhattan,
	'conflicts': linear_conflicts
}
