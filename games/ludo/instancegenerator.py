import numpy as np

class GenerateSequences:
    RANDOM_SEED = 42
        
    def check_sequence(self, board_size, rolls):
        N = board_size  # Total number of fields
        memo = {}  # Memorized moves

        def dp(posX, posY, roll_index):
            if posX == N and posY == N:
                return 0, []
            if roll_index >= len(rolls):
                return float('inf'), []
            if (posX, posY, roll_index) in memo:
                return memo[(posX, posY, roll_index)]

            roll = rolls[roll_index]
            next_roll_index = roll_index + 1
            moves = float('inf')
            best_move_seq = []

            if posX != 0:
                new_posX = posX + roll if posX + roll <= N else posX
                if new_posX != posY or new_posX == N:
                    next_moves, move_seq = dp(new_posX, posY, next_roll_index)
                    if 1 + next_moves < moves:
                        moves = 1 + next_moves
                        best_move_seq = [f"Move X from {posX} to {new_posX}"] + move_seq

            if posY != 0:
                new_posY = posY + roll if posY + roll <= N else posY
                if new_posY != posX or new_posY == N:
                    next_moves, move_seq = dp(posX, new_posY, next_roll_index)
                    if 1 + next_moves < moves:
                        moves = 1 + next_moves
                        best_move_seq = [f"Move Y from {posY} to {new_posY}"] + move_seq

            if roll == 6:
                if posX == 0 and 1 != posY:
                    next_moves, move_seq = dp(1, posY, next_roll_index)
                    if 1 + next_moves < moves:
                        moves = 1 + next_moves
                        best_move_seq = ["Place X on 1"] + move_seq
                if posY == 0 and 1 != posX:
                    next_moves, move_seq = dp(posX, 1, next_roll_index)
                    if 1 + next_moves < moves:
                        moves = 1 + next_moves
                        best_move_seq = ["Place Y on 1"] + move_seq

            memo[(posX, posY, roll_index)] = (moves, best_move_seq)
            return moves, best_move_seq

        initial_posX, initial_posY = 0, 0
        result, move_sequence = dp(initial_posX, initial_posY, 0)
        if result == float('inf'):
            return -1, []
        return result, move_sequence

    def generate_instance(self, board_size, m, n):
        np.random.seed(self.RANDOM_SEED)
        instances = {}
        i = 0
        while i < m:
            rolls = [np.random.randint(1, 7) for _ in range(n)]
            min_moves, _ = self.check_sequence(board_size, rolls)
            if min_moves != -1:
                instances[i] = {'sequence': rolls, 'min': min_moves}
                i += 1
        return instances

if __name__ == "__main__":
    generator = GenerateSequences()
    move_dict = generator.generate_instance(23, 10, 50)  # Generate 10 instances with 50 rolls each
    print(move_dict)
