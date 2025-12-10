def is_solution_valid(solution):
    # Deve ter exatamente 81 caracteres
    if len(solution) != 81:
        return False

    # Só pode conter dígitos 1–9 (sem 0, sem letras)
    if any(c not in "123456789" for c in solution):
        return False

    # Converte para matriz 9x9
    grid = [solution[i*9:(i+1)*9] for i in range(9)]

    # Valida cada linha
    for row in grid:
        if len(set(row)) != 9:
            return False

    # Valida cada coluna
    for col in range(9):
        column = [grid[row][col] for row in range(9)]
        if len(set(column)) != 9:
            return False

    # Valida cada bloco 3x3
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            block = [
                grid[r][c]
                for r in range(br, br + 3)
                for c in range(bc, bc + 3)
            ]
            if len(set(block)) != 9:
                return False

    return True
