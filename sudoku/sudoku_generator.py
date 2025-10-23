import random

class SudokuGenerator:
    def __init__(self, num_clues):
        self.num_clues = num_clues
        self.board = [[0] * 9 for _ in range(9)]
        self.solution = None
        self._generate()

    def _find_empty(self):
        for r in range(9):
            for c in range(9):
                if self.board[r][c] == 0:
                    return (r, c)
        return None

    def _is_valid(self, r, c, num):
        if num in self.board[r]:
            return False
        
        if num in [self.board[i][c] for i in range(9)]:
            return False
        
        start_row, start_col = 3 * (r // 3), 3 * (c // 3)
        for i in range(start_row, start_row + 3):
            for j in range(start_col, start_col + 3):
                if self.board[i][j] == num:
                    return False
        return True

    def _solve(self):
        find = self._find_empty()
        if not find:
            return True
        
        r, c = find
        numbers = list(range(1, 10))
        random.shuffle(numbers)
        
        for num in numbers:
            if self._is_valid(r, c, num):
                self.board[r][c] = num
                
                if self._solve():
                    return True
                
                self.board[r][c] = 0
        return False

    def _generate(self):
        self._solve()
        self.solution = [row[:] for row in self.board]

        cells = list(range(81))
        random.shuffle(cells)
        cells_to_remove = 81 - self.num_clues
        
        for i in range(cells_to_remove):
            r = cells[i] // 9
            c = cells[i] % 9
            self.board[r][c] = 0

    def get_boards_as_strings(self):
        problem_str = "".join(str(c) for row in self.board for c in row)
        solution_str = "".join(str(c) for row in self.solution for c in row)
        return problem_str, solution_str

def generate_puzzle(difficulty):
    if difficulty == 'easy':
        clues = random.randint(33, 38)
    elif difficulty == 'medium':
        clues = random.randint(29, 32)
    elif difficulty == 'difficult':
        clues = random.randint(24, 28)
    else:
        raise ValueError("Dificuldade inválida")
        
    generator = SudokuGenerator(clues)
    return generator.get_boards_as_strings()