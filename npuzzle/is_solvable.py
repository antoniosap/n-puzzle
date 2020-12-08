EMPTY_TILE = 0


def count_inversions(puzzle, solved, size_rows, size_cols):
	res = 0
	for i in range(size_rows * size_cols - 1):
		for j in range(i + 1, size_rows * size_cols):
			vi = puzzle[i]
			vj = puzzle[j]
			if solved.index(vi) > solved.index(vj):
				res += 1
	return res


def is_solvable(puzzle, solved, size_rows, size_cols):
	return True
	#
	# il criterio non funziona per n * m
	#
	inversions = count_inversions(puzzle, solved, size_rows, size_cols)
	puzzle_zero_row = puzzle.index(EMPTY_TILE) // (size_rows * size_cols)
	puzzle_zero_column = puzzle.index(EMPTY_TILE) % (size_rows * size_cols)
	solved_zero_row = solved.index(EMPTY_TILE) // (size_rows * size_cols)
	solved_zero_column = solved.index(EMPTY_TILE) % (size_rows * size_cols)
	taxicab = abs(puzzle_zero_row - solved_zero_row) + abs(puzzle_zero_column - solved_zero_column)
	if taxicab % 2 == 0 and inversions % 2 == 0:
		return True
	if taxicab % 2 == 1 and inversions % 2 == 1:
		return True
	return False
