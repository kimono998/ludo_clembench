class GameSim:
    def __init__(self, num_fields: int, player_tokens: dict, rolls: list[tuple], turn: int):
        """
        Initializes a GameSim object.

        Args:
            num_fields (int): The number of fields in the game.
            player_tokens (dict): The tokens associated with the player.
            rolls (list[tuple]): The rolls for the game.
            turn (int): The current turn number.
        """

        self.num_fields: int = num_fields
        self.rolls: list = rolls
        self.token_state: dict = player_tokens
        self.current_turn: int = turn

    def _get_tokens(self, player: int) -> list[str]:
        """
        Determines player tokens.

        Args:
            player (int): The player number.

        Returns:
            list[str]: The tokens associated with the player.
        """

        # determins player tokens
        player_tokens = ['A', 'B'] if player == 1 else ['X', 'Y']
        return player_tokens

    def _is_taken(self, tokens: list[str], pos: int) -> bool:
        """
        Checks if the position is occupied by any token.

        Args:
            tokens (list[str]): The tokens to check.
            pos (int): The position to check.

        Returns:
            bool: True if the position is occupied, False otherwise.
        """

        # checks if the position is occupied by any token
        # counts as occupied unless it's the last position.
        for token in tokens:
            if self.token_state[token] == pos and pos != self.num_fields:
                return True

        return False

    def _is_out(self, token: str) -> bool:
        """
        Checks if the token is out of the base.

        Args:
            token (str): The token to check.

        Returns:
            bool: True if the token is out of the base, False otherwise.
        """

        if self.token_state[token] > 0:
            return True

        return False

    def is_terminal(self) -> bool:
        """
        Checks whether we have reached the terminal state (game is done).

        Returns:
            bool: True if the game is done, False otherwise.
        """

        # checks whether we have reacehd the terminal state (game is done)
        if self.token_state['X'] == self.num_fields and self.token_state['Y'] == self.num_fields:
            return True
        elif self.token_state['A'] == self.num_fields and self.token_state['B'] == self.num_fields:
            return True
        else:
            return False

    def get_possible_moves(self, player: int) -> list:
        """
        Gets the possible moves for the player.

        Args:
            player (int): The player number.

        Returns:
            list: The possible moves for the player.
        """

        moves: list = []
        roll: int = self.rolls[self.current_turn][player]
        tokens: list[str] = self._get_tokens(player)

        for token in tokens:
            # next move is current_pos + rolled number, unless position is occupied and/or token not on board
            move: tuple[str, int] = self.token_state[token] + roll
            if not self._is_taken(tokens, move) and move <= self.num_fields and self._is_out(token):
                moves.append((token, move))

            # if we roll a 6, and token is in base, we add the move to the list of possibilities.
            if roll == 6:
                # if position not occupied by our token, we can move there
                if self.token_state[token] == 0 and not self._is_taken(tokens, 1):
                    moves.append((token, 1))

        if not moves:
            for token in tokens:
                moves.append((token, self.token_state[token]))

        # print(roll, self.current_turn)
        # print(self.token_state)
        # print(moves)
        return moves

    # if player is True, it means it's our programmatic Player. If so, we can update the turn number.
    def get_new_state(self, move: tuple, player: int) -> 'GameSim':
        """
        Gets the new state after the move.

        Args:
            move (tuple): The move to be made.
            player (int): The player number.

        Returns:
            GameSim: The new game state after the move.
        """

        new_token_state: dict = self.token_state.copy()
        new_token_state[move[0]] = move[1]
        opponent_tokens: list[str] = self._get_tokens(1 - player)
        # opponent not removed if token occupies the final position
        for opponent_token in opponent_tokens:
            if new_token_state[opponent_token] == move[1] and move[1] != self.num_fields:
                new_token_state[opponent_token] = 0

        new_turn = self.current_turn + 1 if player == 1 else self.current_turn
        return GameSim(self.num_fields, new_token_state, self.rolls, new_turn)

    def score(self) -> int:
        """
        Calculates the score of the game.

        Returns:
            int: The score of the game.
        """

        # 100 if we win
        # -100 if we lose
        # intermediate score is the progress of our tokens.

        if self.is_terminal():
            if self.token_state['X'] == self.num_fields and self.token_state['Y'] == self.num_fields:
                return -100  # Opponent wins
            elif self.token_state['A'] == self.num_fields and self.token_state['B'] == self.num_fields:
                return 100  # Our player wins

        # Heuristic: Calculate the progress of each player's tokens
        progress: int = sum(self.token_state[token] for token in ['A', 'B'])
        opponent_progress: int = sum(self.token_state[token] for token in ['X', 'Y'])
        return progress - opponent_progress



def minimax(
    game_state: GameSim,
    maximizingPlayer : bool,
    alpha=float('-inf'),
    beta=float('inf')
) -> tuple[int, tuple]:
    """
    Implements the minimax algorithm to find the optimal move.

    Args:
        game_state (GameSim): The current game state.
        maximizingPlayer (bool): True if the current player is the maximizing player, False otherwise.
        alpha (float, optional): The alpha value for alpha-beta pruning. Defaults to float('-inf').
        beta (float, optional): The beta value for alpha-beta pruning. Defaults to float('inf').

    Returns:
        tuple[int, tuple]: The score of the game and the best move.
    """

    if game_state.is_terminal() or game_state.current_turn > len(game_state.rolls)-1:
        return game_state.score(), None

    if maximizingPlayer:
        value: float = float('-inf')
        possible_moves: list = game_state.get_possible_moves(1) # int 1 for maximizing player (our player)

        for move in possible_moves:
            child: GameSim = game_state.get_new_state(move, 1)
            temp: int = minimax(child, False, alpha, beta)[0]

            if temp > value:
                value = temp
                best_move = move

            if value >= beta:
                break

            alpha = max(alpha, value)

    else:
        value: float = float('inf')
        possible_moves: list = game_state.get_possible_moves(0) # int 0 for minimizing player

        for move in possible_moves:
            child: GameSim = game_state.get_new_state(move, 0)
            temp: int = minimax(child, True, alpha, beta)[0]

            if temp < value:
                value = temp
                best_move = move

            if value <= alpha:
                break

            beta = min(beta, value)

    return value, best_move







