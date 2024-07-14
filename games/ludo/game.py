"""
Contains the main game behavior of Ludo.
"""

import sys
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backends import CustomResponseModel, HumanModel, Model
from clemgame import get_logger
from player import HumanPlayer, LudoPlayer, ProgrammaticPlayer


GAME_NAME: str = "ludo"

logger: logging.Logger = get_logger("games.ludo.game")


class Game:
    """
    A class which handles the game behavior of Ludo, namely prompting the model
    to make its next move given the current game state.
    """
    def __init__(
        self,
        initial_prompt: str,
        n_fields: int,
        n_tokens: int,
        rolls: list[tuple[int, int] | int],
        player_models: list[Model]
    ) -> None:
        """
        Initializes chat-based attributes.

        Args:
            initial_prompt (str): what is initially passed to the LLM
            n_fields (int): the size of the board
            n_tokens (int): the number of tokens given to each player
            rolls (list[tuple[int, int] | int]): contains the die rolls,
                                                 either in the form of tuples
                                                 of integers or as integers,
                                                 depending on the number of
                                                 players
            player_models (list[Model]): contains the player model(s) to be
                                         turned into LudoPlayer object(s)
        """
        # Board attributes
        self.n_fields: int = n_fields
        self.current_state: str = self._reset_board()

        # Conversation attributes
        self.initial_prompt: str = initial_prompt
        self.context: list[str] = []
        self.reprompt_attempts: int = 0
        self.total_retry_count: int = 0
        self.error_count: int = 0
        self.is_aborted: bool = False

        # Game mechanic attributes
        self.n_tokens: int = n_tokens
        self.turn_limit: int = len(rolls)
        self.turn: int = 0
        self.rolls: list[tuple[int, int] | int] = rolls

        # Initializes then loads in players
        self.player_1: LudoPlayer | None = None
        self.player_2: HumanPlayer | ProgrammaticPlayer | None = None
        self._load_players(player_models)

    def add_message(self, message: str, role: str = "user") -> None:
        """
        Adds a message to the conversation context. If it is the first message
        being added, the system prompt and the task description are added to
        the beginning.

        Args:
            message (str): to be added to the conversation context
            role (str): either 'system', 'assistant', or 'user'
        """
        if not self.context:
            split_prompt: list[str]  = self.initial_prompt.split("\n")
            self.context.append({"role": "system", "content": split_prompt[0]})
            self.context.append(
                {
                    "role": "user",
                    "content": ' '.join(split_prompt[2:])
                }
            )

        if self.context[-1]["role"] == role:
            self.context[-1]['content'] += f'\n{message}'
        
        else:
            self.context.append({"role": role, "content": message})

    def reprompt(self, error_type: str, msg, token: str | None = None) -> None:
        """
        Specifies the error, then asks the player to submit a new move.

        Args:
            error_type (str): one of four error types, specifying to the player
                              in which way they erred when making their move
        """
        message: str = "INVALID MOVE: "

        match error_type:
            case "parsing_failed":
                reason: str = (
                    "The response format is not correct.\n"
                    f"Please make sure you are using tokens assigned to you: {list(self.player_1.tokens.keys())}!"
                    "Please state your answer in this format\n"
                    "MY MOVE: X -> N ; Y -> N"
                )
            case "simultaneous_move":
                reason: str = (
                    "Both of your in-play tokens were moved simultaneously."
                    "Please re-count the positions and think this through! "
                )
            case "not_moved_to_board":
                reason: str = f"Token {token} can be played to the board but wasn't. "
            case "not_moved":
                reason: str =  f"Token {token} can be moved but wasn't. "
            case "incorrect_move":
                reason: str =  f"Token {token} was moved incorrectly. "

        message += reason
        message += "Please try again."
        message += msg

        self.add_message(message)
        logger.error(f"{GAME_NAME}: [MOVE ERROR] {reason}")

        self.reprompt_attempts += 1

    def update_board(self, player: LudoPlayer, move: dict[str: int]) -> None:
        """
        Given the current state of the board and the desired move, updates the
        board by moving the token to the new position and replacing the
        previous position with an empty field character.

        Args:
            player (LudoPlayer): the player who just made a move
            move (dict[str: int]): contains the desired position for all tokens
        """
        split_board: list[str] = self._reset_board().split()

        for token in move.keys():
            if player.tokens[token]["in_play"]:
                split_board[move[token] -1] = token

        self.current_state = " ".join(split_board).strip()

    def _load_players(self, player_models: list[Model]) -> None:
        """
        Given a list of player models, initializes the first player as a
        LudoPlayer, indicating it is the LLM player, and the second player as
        either a HumanPlayer or a ProgrammaticPlayer depending on the type of
        model passed.
        
        Args:
            player_models (list[Model]): contains a maximum of 2 player models
        """
        self.player_1 = LudoPlayer(player_models[0], self.n_tokens)

        if len(player_models) > 1:
            if type(player_models[1]) == CustomResponseModel:
                self.player_2 = ProgrammaticPlayer(
                    model=player_models[1],
                    n_tokens=self.n_tokens,
                    rolls=self.rolls
                )
            elif type(player_models[1]) == HumanModel:
                self.player_2 = HumanPlayer(
                    model=player_models[1],
                    n_tokens=self.n_tokens
                )

    def _reset_board(self) -> str:
        """
        Sets the board to its initial blank state.

        Returns:
            str: a representation of the board in its initial blank state
        """
        return " ".join(["□"] * self.n_fields).strip()


if __name__ == "__main__":
    pass