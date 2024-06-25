"""
Comprises a class which simulates a game at a given time step, then feeds this
to the minimax heuristic to calculate the optimal next move for the
ProgrammaticPlayer.
"""


class GameSim:
    """
    Class that works to simulate a game for the ProgrammaticPlayer, ultimately
    serving to work to decide its next move.
    """
    def __init__(
            self,
            n_fields: int,
            player_tokens: dict,
            rolls: list[tuple],
            turn: int
    ) -> None:
        """
        Initializes a GameSim object.

        Args:
            n_fields (int): the number of fields in the game
            player_tokens (dict): the tokens associated with the player
            rolls (list[tuple]): the rolls for the game
            turn (int): the current turn number
        """
        self.n_fields: int = n_fields
        self.rolls: list = rolls
        self.token_state: dict = player_tokens
        self.current_turn: int = turn

    def get_new_state(self, move: tuple, player: int) -> 'GameSim':
        """
        Gets the new state after the move. If player is True, it is the
        ProgrammaticPlayer, in which case the turn number is updated.

        Args:
            move (tuple): the move to be made
            player (int): the player number

        Returns:
            GameSim: the new game state after the move
        """
        new_token_state: dict = self.token_state.copy()
        new_token_state[move[0]] = move[1]
        opponent_tokens: list[str] = self._get_tokens(1 - player)

        # Opponent not removed if token occupies the final position
        for opponent_token in opponent_tokens:
            if (
                new_token_state[opponent_token] == move[1] and
                move[1] != self.n_fields
            ):
                new_token_state[opponent_token] = 0

        return GameSim(
            self.n_fields,
            new_token_state,
            self.rolls,
            (
                self.current_turn + 1
                if player == 1
                else self.current_turn
            )
        )
    
    def get_possible_moves(self, player: int) -> list:
        """
        Gets the possible moves for the player.

        Args:
            player (int): the player number; 0 represents the minimizing player
                          and 1 represents the maximizing player

        Returns:
            list: the possible moves for the player
        """
        roll: int = self.rolls[self.current_turn][player]
        tokens: list[str] = self._get_tokens(player)
        
        moves: list = []
        for token in tokens:
            # Calculates next move unless not possible
            move: tuple[str, int] = self.token_state[token] + roll
            if (
                not self._is_taken(tokens, move) and
                move <= self.n_fields and
                self._is_out(token)
            ):
                moves.append((token, move))

            # If a token can be moved out, it is added to possible moves
            if (
                roll == 6 and
                self.token_state[token] == 0 and
                not self._is_taken(tokens, 1)
            ):
                moves.append((token, 1))

        if not moves:
            for token in tokens:
                moves.append((token, self.token_state[token]))

        return moves
    
    def score(self) -> int:
        """
        Calculates the score of the game, which is 100 if we win or -100 if
        the oppononent wins. If the game is not yet at its terminal state, the
        progress of the players' tokens is calculated and returned.

        Returns:
            int: the score of the game
        """
        if self.is_terminal():
            if (
                self.token_state['X'] == self.n_fields and
                self.token_state['Y'] == self.n_fields
            ):
                return -100

            elif (
                self.token_state['A'] == self.n_fields and
                self.token_state['B'] == self.n_fields
            ):
                return 100

        # Heuristic: Calculate the progress of each player's tokens
        progress: int = sum(
            self.token_state[token]
            for token in ['A', 'B']
        )
        opponent_progress: int = sum(
            self.token_state[token]
            for token in ['X', 'Y']
        )

        return progress - opponent_progress

    def _get_tokens(self, player: int) -> list[str]:
        """
        Determines player tokens.

        Args:
            player (int): the player number; 0 for player 1 and 1 for player 2

        Returns:
            list[str]: the tokens associated with the player
        """
        return ['A', 'B'] if player == 1 else ['X', 'Y']

    def _is_out(self, token: str) -> bool:
        """
        Checks if the token is out of the base.

        Args:
            token (str): the token to check

        Returns:
            bool: True if the token is out of the base, False otherwise
        """
        return self.token_state[token] > 0
    
    def _is_taken(self, tokens: list[str], pos: int) -> bool:
        """
        Checks if the position is occupied by any token.

        Args:
            tokens (list[str]): the tokens to check
            pos (int): the position to check

        Returns:
            bool: True if the position is occupied, False otherwise
        """
        for token in tokens:
            if self.token_state[token] == pos and pos != self.n_fields:
                return True

        return False

    def is_terminal(self) -> bool:
        """
        Checks whether we have reached the terminal state (game is done).

        Returns:
            bool: True if the game is done, False otherwise.
        """
        return (
            (
                self.token_state["X"] == self.n_fields and
                self.token_state["Y"] == self.n_fields
            ) or (
                self.token_state["A"] == self.n_fields and
                self.token_state["B"] == self.n_fields
            )
        )


def minimax(
    game_state: GameSim,
    maximizing_player : bool,
    alpha: float = float('-inf'),
    beta: float = float('inf')
) -> tuple[int, tuple]:
    """
    Implements the minimax algorithm to find the optimal move.

    Args:
        game_state (GameSim): the current game state
        maximizingPlayer (bool): True if the current player is the maximizing
                                 player, False otherwise
        alpha (float): the alpha value for alpha-beta pruning
        beta (float): the beta value for alpha-beta pruning

    Returns:
        tuple[int, tuple]: the score of the game and the best move
    """

    if (
        game_state.is_terminal() or
        game_state.current_turn > len(game_state.rolls)-1
    ):
        return game_state.score(), None

    if maximizing_player:
        value: float = float('-inf')

        # int 1 for maximizing player (our player)
        possible_moves: list = game_state.get_possible_moves(1)

        for move in possible_moves:
            child: GameSim = game_state.get_new_state(move, 1)
            temp: int = minimax(child, False, alpha, beta)[0]

            if temp > value:
                value = temp
                best_move: tuple[str, int] = move

            if value >= beta:
                break

            alpha = max(alpha, value)

    else:
        value: float = float('inf')

        # int 0 for minimizing player
        possible_moves: list = game_state.get_possible_moves(0)

        for move in possible_moves:
            child: GameSim = game_state.get_new_state(move, 0)
            temp: int = minimax(child, True, alpha, beta)[0]

            if temp < value:
                value = temp
                best_move: tuple[str, int] = move

            if value <= alpha:
                break

            beta = min(beta, value)

    return value, best_move


if __name__ == '__main__':
    pass