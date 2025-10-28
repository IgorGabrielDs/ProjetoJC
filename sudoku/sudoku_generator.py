import random

class SudokuGenerator:
    """
    Gera um puzzle Sudoku garantindo solução única.
    """
    def __init__(self, num_clues: int): 
        self.num_clues = num_clues
        self.board = [[0] * 9 for _ in range(9)]
        self.solution = []
        self._generate_puzzle()

    def _find_empty(self, board):
        """Encontra a próxima célula vazia (0) em um tabuleiro específico."""
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    return (r, c)
        return None

    def _is_valid(self, board, r, c, num):
        """Verifica se um número é válido em uma determinada posição."""
        if num in board[r]:
            return False
        if num in [board[i][c] for i in range(9)]:
            return False
        start_row, start_col = 3 * (r // 3), 3 * (c // 3)
        for i in range(3):
            for j in range(3):
                if board[start_row + i][start_col + j] == num:
                    return False
        return True

    def _solve_board(self):
        """Preenche o tabuleiro self.board com uma solução aleatória."""
        find = self._find_empty(self.board)
        if not find:
            return True
        r, c = find
        
        numbers = list(range(1, 10))
        random.shuffle(numbers)

        for num in numbers:
            if self._is_valid(self.board, r, c, num):
                self.board[r][c] = num
                if self._solve_board():
                    return True
                self.board[r][c] = 0
        return False

    def _count_solutions(self, board):
        """Conta o número de soluções possíveis para um dado tabuleiro (limita a 2)."""
        find = self._find_empty(board)
        if not find:
            return 1 
        
        r, c = find
        count = 0
        
        for num in range(1, 10):
            if self._is_valid(board, r, c, num):
                board[r][c] = num
                count += self._count_solutions(board)
                board[r][c] = 0  
                if count >= 2:
                    return 2
        return count

    def _generate_puzzle(self):
        """Lógica principal para gerar um puzzle com solução única."""
        self.board = [[0] * 9 for _ in range(9)]
        self._solve_board()
        self.solution = [row[:] for row in self.board]

        cells = list(range(81))
        random.shuffle(cells)
        
        cells_to_remove = 81 - self.num_clues
        removed_count = 0
        
        for cell_index in cells:
            if removed_count >= cells_to_remove:
                break
                
            r = cell_index // 9
            c = cell_index % 9
            
            backup = self.board[r][c]
            self.board[r][c] = 0
            
            board_copy = [row[:] for row in self.board]
            
            if self._count_solutions(board_copy) != 1:
                self.board[r][c] = backup
            else:
                removed_count += 1

    def get_boards_as_strings(self):
        """Strings de 81 chars. Use '.' para vazio (ou troque por '0' se preferir)."""
        problem_str = "".join(str(c) if c != 0 else '.' for row in self.board for c in row)
        solution_str = "".join(str(c) for row in self.solution for c in row)
        return problem_str, solution_str


def generate_puzzle(difficulty: str):
    if difficulty == 'easy':
        clues = random.randint(33, 38)
    elif difficulty == 'medium':
        clues = random.randint(29, 32)
    elif difficulty == 'hard':
        clues = random.randint(24, 28)
    else:
        raise ValueError(f"Dificuldade '{difficulty}' inválida.")

    generator = SudokuGenerator(clues)
    return generator.get_boards_as_strings()