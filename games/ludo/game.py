"""
Contains the main game behavior of Ludo.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backends import CustomResponseModel, HumanModel, Model
from player import HumanPlayer, LudoPlayer, ProgrammaticPlayer


class Game:
    """
    A class which handles the game behavior of Ludo, namely prompting the model
    to make its next move given the current game state.
    """
    def __init__(
        self,
        initial_prompt: str,
        n_fields: int,
        rolls: list[tuple[int, int]],
        player_models: list[Model]
    ) -> None:
        """
        Initializes chat-based attributes.

        Args:
            initital_prompt (str): comprised of the system prompt, the task
                                   description, and relevant examples
            n_fields (int): the size of the board
            rolls (list[tuple[int, int]]): contains the die rolls for each
                                           player for each turn
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

        # Game mechanic attributes
        self.turn_limit: int = len(rolls)
        self.turn: int = 0
        self.rolls: list[tuple[int, int]] = rolls

        # Player attributes
        self._initialize_players(player_models)

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
            self.context.append({"role": "user", "content": split_prompt[2:]})

        self.context.append({"role": role, "content": message})

    def reprompt(self, error_type: str, token: str | None = None) -> None:
        """
        Specifies the error, then asks the player to submit a new move.

        Args:
            error_type (str): one of four error types, specifying to the player
                              in which way they erred when making their move
        """
        message: str = "INVALID MOVE: "

        match error_type:
            case "simultaneous_move":
                message += "Both of your in-play tokens were moved simultaneously. "
            case "not_moved_to_board":
                message += f"Token {token} can be played to the board but wasn't. "
            case "not_moved":
                message += f"Token {token} can be moved but wasn't. "
            case "incorrect_move":
                message += f"Token {token} was moved incorrectly. "

        message += "Please try again."

        self.add_message(message)
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
        split_board: list[str] = self.current_state.split()

        for token in move.keys():
            if player.tokens["in_play"]:
                split_board[player.tokens["position"] - 1] = "□"
                split_board[move[token]] = token

        self.current_state = " ".join(split_board).strip()

    def _initialize_players(self, player_models: list[Model]) -> None:
        """
        Given a list of player models, initializes the first player as a
        LudoPlayer, indicating it is the LLM player, and the second player as
        either a HumanPlayer or a ProgrammaticPlayer depending on the type of
        model passed.
        
        Args:
            player_models (list[Model]): contains a maximum of two player models
        """
        self.player_1: LudoPlayer = LudoPlayer(player_models[0])

        if len(player_models) > 1:
            match type(player_models[1]):
                case HumanModel():
                    self.player_2: LudoPlayer = HumanPlayer(player_models[1])
                case CustomResponseModel():
                    self.player_2: LudoPlayer = ProgrammaticPlayer(player_models[1], self.rolls)
                case _:
                    self.player_2: None = None

    def _reset_board(self) -> str:
        """
        Sets the board to its initial blank state.

        Returns:
            str: a representation of the board in its initial blank state
        """
        return " ".join(["□"] * self.n_fields).strip()


if __name__ == "__main__":
    pass
