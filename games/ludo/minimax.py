class GameSim:
    def __init__(self, num_fields: int, player_tokens: dict, rolls: list[tuple], turn: int):

        self.num_fields = num_fields
        self.rolls = rolls
        self.token_state = player_tokens
        self.current_turn = turn

    def is_terminal(self):

        if self.token_state['X'] == self.num_fields and self.token_state['Y'] == self.num_fields:
            return True
        elif self.token_state['A'] == self.num_fields and self.token_state['B'] == self.num_fields:
            return True
        else:
            return False

    def get_tokens(self, player):
        player_tokens = ['A', 'B'] if player == 1 else ['X', 'Y']
        return player_tokens

    def is_taken(self, tokens, pos):
        # checks if the position is occupied by any token
        # counts as occupied unless it's the last position.
        for token in tokens:
            if self.token_state[token] == pos and pos != self.num_fields:
                return True

        return False

    def is_out(self, token):
        if self.token_state[token] > 0:
            return True

        return False

    def get_possible_moves(self, player: int):
        moves = []
        roll = self.rolls[self.current_turn][player]
        tokens = self.get_tokens(player)

        # cannot remove token if at last position on the board.
        # can move it there if it's at last position and occupied

        for token in tokens:
            move = self.token_state[token] + roll
            if not self.is_taken(tokens, move) and move <= self.num_fields and self.is_out(token):
                moves.append((token, move))


            if roll == 6:
                # if position not occupied by our token, we can move there
                if self.token_state[token] == 0 and not self.is_taken(tokens, 1):
                    moves.append((token, 1))

        if not moves:
            for token in tokens:
                moves.append((token, self.token_state[token]))

        print(roll, self.current_turn)
        print(self.token_state)
        print(moves)
        return moves

    # if player is True, it means it's our programmatic Player. If so, we can update the turn number.
    def get_new_state(self, move, player: int):

        new_token_state = self.token_state.copy()
        new_token_state[move[0]] = move[1]
        opponent_tokens = self.get_tokens(1 - player)
        # opponent not removed if token occupies the final position
        for opponent_token in opponent_tokens:
            if new_token_state[opponent_token] == move[1] and move[1] != self.num_fields:
                new_token_state[opponent_token] = 0

        new_turn = self.current_turn + 1 if player == 1 else self.current_turn
        return GameSim(self.num_fields, new_token_state, self.rolls, new_turn)

    def score(self):
        # 100 if we win
        # -100 if we lose
        # intermediate score is the progress of our tokens.

        if self.is_terminal():
            if self.token_state['X'] == self.num_fields and self.token_state['Y'] == self.num_fields:
                return -100  # Opponent wins
            elif self.token_state['A'] == self.num_fields and self.token_state['B'] == self.num_fields:
                return 100  # Our player wins

        # Heuristic: Calculate the progress of each player's tokens
        progress = sum(self.token_state[token] for token in ['A', 'B'])
        opponent_progress = sum(self.token_state[token] for token in ['X', 'Y'])
        return progress - opponent_progress



def minimax(game_state : GameSim, maximizingPlayer : bool, alpha=float('-inf'), beta=float('inf')):

    if game_state.is_terminal() or game_state.current_turn > len(game_state.rolls)-1:
        return game_state.score(), None

    if maximizingPlayer:
        value = float('-inf')
        possible_moves = game_state.get_possible_moves(1) # int 1 for maximizing player (our player)

        for move in possible_moves:
            child = game_state.get_new_state(move, 1)
            temp = minimax(child, False, alpha, beta)[0]

            if temp > value:
                value = temp
                best_move = move

            if value >= beta:
                break

            alpha = max(alpha, value)

    else:
        value = float('inf')
        possible_moves = game_state.get_possible_moves(0) # int 0 for minimizing player

        for move in possible_moves:
            child = game_state.get_new_state(move, 0)
            temp = minimax(child, True, alpha, beta)[0]

            if temp < value:
                value = temp
                best_move = move

            if value <= alpha:
                break

            beta = min(beta, value)

    return value, best_move







