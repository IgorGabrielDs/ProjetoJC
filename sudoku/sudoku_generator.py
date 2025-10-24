# sudoku/sudoku_generator.py (Lógica Definitiva e Garantida)

import random
import sys

# Aumenta o limite de recursão para o Backtracking
sys.setrecursionlimit(4000) 

class SudokuGenerator:
    def __init__(self, num_clues):
        self.num_clues = num_clues
        self.board = [[0] * 9 for _ in range(9)]
        self.solution = None
        self.problem_board = None
        
        attempts = 0
        max_attempts = 50 
        
        # O construtor tenta gerar um puzzle com solução única
        while attempts < max_attempts:
            self.board = [[0] * 9 for _ in range(9)]
            
            # 1. Tenta gerar a solução base 100% válida
            if self._solve_full_board():
                self.solution = [row[:] for row in self.board]
                
                # 2. Gera o problema removendo células, garantindo unicidade
                self.problem_board = self._generate_problem()

                if self.problem_board is not None:
                    # Sucesso: puzzle válido e único
                    return 
            
            attempts += 1
            
        raise Exception(f"Falha CRÍTICA: Não foi possível gerar um Sudoku válido e único após {max_attempts} tentativas.")


    def _find_empty(self, board):
        """Encontra a próxima célula vazia (0)."""
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    return (r, c)
        return None

    def _is_valid(self, board, r, c, num):
        """
        Verifica se 'num' é válido na posição (r, c).
        Função CRÍTICA: Garante que o tabuleiro não tem repetições.
        """
        
        # 1. Checagem de Linha
        for val in board[r]:
            if val == num:
                return False
        
        # 2. Checagem de Coluna
        for i in range(9):
            if board[i][c] == num:
                return False
        
        # 3. Checagem de Bloco 3x3
        box_r, box_c = r - r % 3, c - c % 3
        for i in range(box_r, box_r + 3):
            for j in range(box_c, box_c + 3):
                if board[i][j] == num:
                    return False
        
        return True

    def _solve_full_board(self):
        """
        Gera o tabuleiro completamente resolvido (SOLUÇÃO FINAL).
        """
        find = self._find_empty(self.board) 
        
        if not find:
            return True # O tabuleiro está completo (sem '0's)
        
        r, c = find
        numbers = list(range(1, 10))
        random.shuffle(numbers) 
        
        for num in numbers:
            if self._is_valid(self.board, r, c, num):
                self.board[r][c] = num
                
                if self._solve_full_board():
                    return True
                
                self.board[r][c] = 0 # Backtrack
        
        return False # Falha ao encontrar solução para esta célula

    def _count_solutions(self, board_problem, limit=2):
        """
        Conta o número de soluções. Usado para garantir unicidade.
        Retorna 0 (insolúvel), 1 (única) ou 2 (múltipla).
        """
        solutions_count = 0
        
        def solve_count(board):
            nonlocal solutions_count
            
            if solutions_count >= limit:
                return
            
            find = self._find_empty(board)
            if not find:
                solutions_count += 1
                return
            
            r, c = find
            # Tenta números de 1 a 9 em ordem, pois o objetivo é apenas contar
            for num in range(1, 10): 
                if self._is_valid(board, r, c, num):
                    board[r][c] = num
                    solve_count(board)
                    board[r][c] = 0 # Backtrack
        
        temp_board = [row[:] for row in board_problem]
        solve_count(temp_board)
        return solutions_count

    def _generate_problem(self):
        """
        Remove células garantindo que o puzzle tenha uma solução única, 
        respeitando o limite de pistas do nível de dificuldade.
        """
        
        problem = [row[:] for row in self.solution]
        all_coords = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(all_coords)
        
        cells_removed = 0
        cells_to_remove_target = 81 - self.num_clues

        # Tenta remover o número de células necessárias, mantendo a unicidade
        for r, c in all_coords:
            
            # Se já atingimos o objetivo de remoção, paramos.
            if cells_removed >= cells_to_remove_target:
                break
            
            original_value = problem[r][c]
            
            # 1. Tenta remover
            problem[r][c] = 0
            
            # 2. Checa se o puzzle tem solução única
            if self._count_solutions(problem) == 1:
                # Remoção bem-sucedida: Unicidade mantida
                cells_removed += 1 
            else:
                # Remoção falhou: Unicidade quebrada ou insolúvel. Restaura.
                problem[r][c] = original_value
        
        # Retorna o puzzle, que é garantido de ter solução única.
        return problem

    def get_boards_as_strings(self):
        """Converte a lista de listas para strings de 81 caracteres."""
        
        if not self.problem_board or not self.solution:
            raise Exception("Tabuleiro não gerado corretamente.")
            
        problem_str = "".join(str(c) for row in self.problem_board for c in row)
        solution_str = "".join(str(c) for row in self.solution for c in row)
        return problem_str, solution_str

# --- Função de fachada para uso no Django (LIMITES ORIGINAIS) ---

def generate_puzzle(difficulty):
    # Retornando aos limites originais de pistas, mas agora com a lógica de unicidade garantida:
    if difficulty == 'easy':
        clues = random.randint(33, 38)
    elif difficulty == 'medium':
        clues = random.randint(29, 32)
    elif difficulty == 'hard' or difficulty == 'difficult':
        clues = random.randint(24, 28)
    else:
        clues = 35 
        
    generator = SudokuGenerator(clues)
    return generator.get_boards_as_strings()