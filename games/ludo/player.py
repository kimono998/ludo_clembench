"""
Describes custom behavior for human and programmatic participants in 'Ludo'.
"""

import re
import sys
from pathlib import Path
from minimax import GameSim, minimax

sys.path.append(str(Path(__file__).parent.parent.parent))

from backends import CustomResponseModel, HumanModel, Model
from clemgame.clemgame import Player


class LudoPlayer(Player):
    """
    Custom child class of Player which adds player-specific gameplay attributes.
    """
    def __init__(self, model: Model) -> None:
        """
        Passes along the Model object to the parent class and initializes
        player-specific attributes.
        
        Args:
            model (Model): associated Model object, or a child class thereof
        """
        super().__init__(model)
        self.tokens: dict[str: dict] = {
            "X": {
                "in_play": False,
                "position": 0
            },
            "Y": {
                "in_play": False,
                "position": 0
            }
        }


class HumanPlayer(LudoPlayer):
    """
    A human participant in the game 'Ludo'. Its custom response behavior is
    described in self._terminal_response.
    """
    def __init__(self, model: HumanModel) -> None:
        """
        Passes along the input HumanModel object to the parent class.

        Args:
            model (HumanModel): the instantiated HumanModel
        """
        super().__init__(model)
        self.tokens['A'] = {
            "in_play": False,
            "position": 0
        }
        self.tokens['B'] = {
            "in_play": False,
            "position": 0
        }

    # TODO Test HumanPlayer
    def _terminal_response(self, messages: list[dict], turn_idx: int) -> str:
        """
        Describes the behavior of the human second player, given the
        conversation history and the current turn index, ultimately producing
        and returning its response.

        Args:
            messages (list[dict]): contains the conversation history up to and
                                   including the current turn
            turn_idx (int): the current turn index

        Returns:
            str: human player's response

        Raises:
            ValueError: raised if the user input is not given in the correct
                        format
        """
        # TODO Write something to verify moves
        latest_response: str = "Nothing has been said yet."

        if messages:
            latest_response = messages[-1]["content"]

        print(f"\n{latest_response}")
        print('What is your next move? Please write:\nMY MOVE: A -> N ; B -> N')
        
        while True:
            user_input: str = input(f"Your response as {self.__class__.__name__} (turn: {turn_idx}):\n")
            try:
                _ = parse_text(user_input)
            except ValueError:
                print('Input format not valid! Please try again with the proper format.')
                print('MY MOVE: A -> N ; B -> N')
            else:
                return user_input


# TODO 2 objectives to select -> (1) win and (2) eliminate P1; implement functionality to eliminate P1
# TODO Set that the objective switches to win once P1 is eliminated
class ProgrammaticPlayer(LudoPlayer):
    """
    A programmatic participant in the game 'Ludo'. Its custom response behavior
    is described in self._custom_response.
    """
    def __init__(self, model: CustomResponseModel, rolls: list[tuple]) -> None:
        """
        Passes along the input CustomResponseModel object to the parent class.

        Args:
            model (CustomResponseModel): the instantiated CustomResponseModel
            rolls (list[tuple[int, int]]): the roll sequence list from the
                                           game instance
        """
        super().__init__(model)
        self.tokens['A'] = {
            "in_play": False,
            "position": 0
        }
        self.tokens['B'] = {
            "in_play": False,
            "position": 0
        }
        self.rolls: list[tuple[int, int]] = rolls

    def _compose_response(self, move: tuple) -> str:
        """
        Composes a response message based on the move.

        Args:
            move (tuple): the move to be made

        Returns:
            str: the response message
        """
        temp: dict = self.tokens.copy()
        temp[move[0]]['position'] = move[1]

        return f"MY MOVE: A -> {temp['A']['position']} ; B -> {temp['B']['position']}"

    # TODO Determine if turn_idx is expected in the output
    def _custom_response(self, messages: list[dict], turn_idx: int) -> str:
        """
        Describes the behavior of the programmatic second player, given the
        conversation history and the current turn index, ultimately producing
        and returning its response.

        Args:
            messages (list[dict]): contains the conversation history up to and
                                   including the current turn
            turn_idx (int): the current turn index

        Returns:
            str: programmatic player's response
        """
        token_positions, turn_number, n_fields = self._parse_messages(messages)
        move: tuple = self._make_move(
            token_positions,
            self.rolls,
            n_fields,
            turn_number
        )

        return self._compose_response(move)
    
    def _make_move(
        self,
        token_positions: dict,
        rolls: list[tuple],
        n_fields: int,
        turn_number: int
    ) -> tuple:
        """
        Makes a new move as a programmatic player based on the objective.

        Args:
            token_positions (dict): the positions of the tokens
            rolls (list[tuple]): the rolls for the game
            n_fields (int): the size of the board
            turn_number (int): the current turn number

        Returns:
            tuple: the move to be made
        """
        game: GameSim = GameSim(n_fields, token_positions, rolls, turn_number)
        _, move = minimax(game, True)

        return move

    def _parse_messages(self, input_message: str) -> list[dict, int, int]:
        """
        Parses the input message to obtain the state of the board, as well as
        the current roll.
        
        Args:
            messages (str): contains all the messages in the conversation thus
                            far
        
        Returns:
            list[dict, int]: list with [dictionary with token positions, rolled
                             number, board size]

        Raises:
            Exception: raised if no matching pattern is found
        """
        pattern: re.Pattern = r"Current state:\s*(.*?)\s*Turn number:\s*(\d+),\s*Roll:\s*(\d+)\."
        pattern_match: re.Match = re.search(pattern, input_message, re.DOTALL)

        if pattern_match:
            current_state: str = pattern_match.group(1).strip()
            turn_number: int = int(pattern_match.group(2))

            # Identifies the positions of tokens (X, Y, A, B) in the current state
            tokens: list = ["X", "Y", "A", "B"]
            n_fields = len(current_state.split())
            token_positions = {token: 0 for token in tokens}

            for index, char in enumerate(current_state.split()):
                if char in tokens:
                    token_positions[char] = index + 1

            return token_positions, turn_number, n_fields

        else:
            raise Exception('No match found.')


def parse_text(text: str, player: LudoPlayer) -> dict[str: int]:
    """
    Parses the input text according to an expected input format in order to
    extract per token moves.

    Args:
        text (str): raw input text
        player (LudoPlayer): the player who the text was produced by

    Returns:
        dict[str: int]: contains token-position pairs

    Raises:
        ValueError: raises when the text does not match the expected
                    format; prints a preview of the non-conforming text
    """

    tokens: list[str] = ['X', 'Y'] if type(player) is LudoPlayer else ['A', 'B']
    matches: re.Match = re.search(
        rf"MY MOVE: {tokens[0]} -> (\d+) ; {tokens[1]} -> (\d+)",
        text
    )

    if not matches:
        raise ValueError(f"Invalid text format: {text[:20]}")

    return {f"{tokens[0]}": int(matches.group(1)), f"{tokens[1]}": int(matches.group(2))}


if __name__ == '__main__':
    pass
