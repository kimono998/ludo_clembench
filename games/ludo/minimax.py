"""
Comprised of a class which simulates a game at a given time step, then feeds
this to the minimax heuristic to calculate the optimal next move for the
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
            token_positions: dict,
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
        self.n_tokens: int = len(token_positions)
        self.token_positions: dict = token_positions
        self.rolls: list = rolls
        self.turn: int = turn

    def get_new_state(self, move: tuple[str, int], player: int) -> 'GameSim':
        """
        Gets the new state after the move. If player is True, it is the
        ProgrammaticPlayer, in which case the turn number is updated.

        Args:
            move (tuple[str, int]): the move to be made
            player (int): the player number -- 0 for player 1, 1 for player 2

        Returns:
            GameSim: the new game state after the move
        """
        new_token_positions: dict = self.token_positions.copy()
        new_token_positions[move[0]] = move[1]
        opponent_tokens: list[str] = self._get_tokens(1 - player)

        # Opponent not removed if token occupies the final position
        for opponent_token in opponent_tokens:
            if (
                new_token_positions[opponent_token] == move[1] and
                move[1] != self.n_fields
            ):
                new_token_positions[opponent_token] = 0

        return GameSim(
            self.n_fields,
            new_token_positions,
            self.rolls,
            (
                self.turn + 1
                if player == 1
                else self.turn
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
        roll: int = self.rolls[self.turn][player]
        tokens: list[str] = self._get_tokens(player)
        
        moves: list = []
        for token in tokens:
            # Calculates next move unless not possible
            move: tuple[str, int] = self.token_positions[token] + roll
            if (
                not self._is_taken(tokens, move) and
                move <= self.n_fields and
                self._is_out(token)
            ):
                moves.append((token, move))

            # If a token can be moved out, it is added to possible moves
            if (
                roll == 6 and
                self.token_positions[token] == 0 and
                not self._is_taken(tokens, 1)
            ):
                moves.append((token, 1))

        if not moves:
            for token in tokens:
                moves.append((token, self.token_positions[token]))

        return moves
    
    def is_terminal(self) -> bool:
        """
        Checks whether we have reached the terminal state (game is done).

        Returns:
            bool: True if the game is done, False otherwise.
        """
        return (
            (
                self.token_positions["X"] == self.n_fields and
                self.token_positions["Y"] == self.n_fields
            ) or (
                self.token_positions["A"] == self.n_fields and
                self.token_positions["B"] == self.n_fields
            )
        )
    
    def score(self) -> int:
        """
        Calculates the score of the game, which is 100 if we win or -100 if
        the oppononent wins. If the game is not yet at its terminal state, the
        progress of the players' tokens is calculated and returned.

        Returns:
            int: the score of the game
        """
        # if self.is_terminal():
        #     if (
        #         self.token_positions['X'] == self.n_fields and
        #         self.token_positions['Y'] == self.n_fields
        #     ):
        #         return -100

        #     elif (
        #         self.token_positions['A'] == self.n_fields and
        #         self.token_positions['B'] == self.n_fields
        #     ):
        #         return 100

        # TODO Fix -- does token_positions contain all two/four tokens?
        # If game is terminal, score according to player
        if self.is_terminal() and all(
            self.token_positions[token] == self.n_fields
            for token in self.token_positions
        ):      
            return -100 if self.token_positions["X"] else 100
            

        # Heuristic: Calculate the progress of each player's tokens
        progress: int = sum(
            self.token_positions[token]
            for token in ['A', 'B']
        )
        opponent_progress: int = sum(
            self.token_positions[token]
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
        match self.n_tokens:
            case 1:
                return ["A"] if player == 1 else ["X"]
            case 2:
                return ['A', 'B'] if player == 1 else ['X', 'Y']
        
    def _is_out(self, token: str) -> bool:
        """
        Checks if the token is out of the base.

        Args:
            token (str): the token to check

        Returns:
            bool: True if the token is out of the base, False otherwise
        """
        return self.token_positions[token] > 0
    
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
            if self.token_positions[token] == pos and pos != self.n_fields:
                return True

        return False


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
        maximizing_player (bool): True if the current player is the maximizing
                                  player, False otherwise
        alpha (float): the alpha value for alpha-beta pruning
        beta (float): the beta value for alpha-beta pruning

    Returns:
        tuple[int, tuple]: the score of the game and the best move
    """
    # If the game is at its terminal state, it is scored
    if (
        game_state.is_terminal() or
        game_state.turn > len(game_state.rolls) - 1
    ):
        return game_state.score(), None
    
    # Otherwise, the current game state is analyzed for the given player
    best_move_score: float = float('-inf')
    possible_moves: list = game_state.get_possible_moves(int(maximizing_player))
    
    for move in possible_moves:
        move_score: int = minimax(
                game_state.get_new_state(move, int(maximizing_player)),
                maximizing_player=not maximizing_player,
                alpha=alpha,
                beta=beta
            )[0]
        if maximizing_player:
            if move_score > best_move_score:
                best_move_score = move_score
                best_move: tuple[str, int] = move

            if best_move_score >= beta:
                break

            alpha = max(alpha, best_move_score)

        else:
            if move_score < best_move_score:
                best_move_score = move_score
                best_move: tuple[str, int] = move

            if best_move_score <= alpha:
                break

            beta = min(beta, best_move_score)

    return best_move_score, best_move


if __name__ == '__main__':
    pass
