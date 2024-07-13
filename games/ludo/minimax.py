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
            n_tokens: int,
            token_positions: dict,
            rolls: list[tuple],
            turn: int
    ) -> None:
        """
        Initializes a GameSim object.

        Args:
            n_fields (int): the number of fields in the game
            TODO n_tokens (int):
            player_tokens (dict): the tokens associated with the player
            rolls (list[tuple]): the rolls for the game
            turn (int): the current turn number
        """
        self.n_fields: int = n_fields
        self.n_tokens: int = n_tokens
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

        # Opponent not removed if token occupies the final position
        for opponent_token in self._get_tokens(1 - player):
            if (
                new_token_positions[opponent_token] == move[1] and
                move[1] != self.n_fields
            ):
                new_token_positions[opponent_token] = 0

        return GameSim(
            self.n_fields,
            self.n_tokens,
            new_token_positions,
            self.rolls,
            (
                self.turn + 1
                if player == 1
                else self.turn
            )
        )
    
    def get_possible_moves(self, player: int) -> list[tuple[str, int]]:
        """
        Gets the possible moves for the player.

        Args:
            player (int): the player number; 0 represents the minimizing player
                          and 1 represents the maximizing player

        Returns:
            list[tuple[str, int]]: possible moves for the player
        """
        roll: int = self.rolls[self.turn][player]
        tokens: list[str] = self._get_tokens(player)
        moves: list[tuple[str, int]] = []
        for token in tokens:
            # Calculates next move unless not possible
            destination: int = self.token_positions[token] + roll
            if (
                not self._is_taken(tokens, destination) and
                destination <= self.n_fields and
                self._is_out(token)
            ):
                moves.append((token, destination))

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

    def is_terminal(self) -> tuple[bool, int | None]:
        """
        Checks whether either player has all of their tokens in the end field,
        meaning that the game has reached its terminal state.

        Returns:
            tuple[bool, int | None]: contains a bool which is True if the game
                                     is over, False otherwise, and an
                                     indicator of which player won
        """
        # Checks if either player finished the game
        p1_terminal: bool = all(
            self.token_positions[token] == self.n_fields
            for token in self._get_tokens(0)
        )
        p2_terminal: bool = all(
            self.token_positions[token] == self.n_fields
            for token in self._get_tokens(0)
        )
        
        # Determines the winning player
        if p1_terminal:
            winner: int = 0
        elif p2_terminal:
            winner: int = 1
        else:
            winner: None = None

        return any((p1_terminal, p2_terminal)), winner
    
    def score(self) -> int:
        """
        Calculates the score of the game, which is 100 if we win or -100 if
        the oppononent wins. If the game is not yet at its terminal state, the
        progress of the players' tokens is calculated and returned.

        Returns:
            int: the score of the game
        """
        # If the game has finished, scores 100 if winner is p1, -100 if p2
        terminal, winner = self.is_terminal()
        if terminal:
            return -100 if winner else 100

        # Calculate the progress of each player's tokens otherwise
        progress: int = sum(
            self.token_positions[token]
            for token in self._get_tokens(0)
        )
        opponent_progress: int = sum(
            self.token_positions[token]
            for token in self._get_tokens(1)
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
    maximizing_player: bool,
    alpha: float = float('-inf'),
    beta: float = float('inf')
) -> tuple[int, tuple[str, int] | None]:
    """
    Implements the minimax algorithm to find the optimal move.

    Args:
        game_state (GameSim): the current game state
        maximizing_player (bool): True if the current player is the maximizing
                                  player, False otherwise
        alpha (float): the alpha value for alpha-beta pruning
        beta (float): the beta value for alpha-beta pruning

    Returns:
        tuple[int, tuple[str, int] | None]: score of the game and best move
    """
    # If the game is at its terminal state, it is scored
    if (
        game_state.is_terminal()[0] or
        game_state.turn > len(game_state.rolls) - 1
    ):
        return game_state.score(), None
    
    player: int = int(maximizing_player)
    best_move: tuple[str, int] | None = None
    best_score: float = float("-inf") if maximizing_player else float("inf")

    possible_moves: list[tuple[str, int]] = game_state.get_possible_moves(player)

    if maximizing_player:
        for move in possible_moves:
            child: GameSim = game_state.get_new_state(move, player)
            score: int = minimax(child, False, alpha, beta)[0]

            if score > best_score:
                best_score = score
                best_move = move

            if best_score >= beta:
                break

            alpha = max(alpha, best_score)

    else:
        for move in possible_moves:
            child: GameSim = game_state.get_new_state(move, player)
            score: int = minimax(child, True, alpha, beta)[0]

            if score < best_score:
                best_score = score
                best_move = move

            if best_score <= beta:
                break

            beta = min(alpha, best_score)

    return best_score, best_move


if __name__ == '__main__':
    pass
