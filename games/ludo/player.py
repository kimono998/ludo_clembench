"""
Describes custom behavior for human and programmatic participants in 'Ludo'.
"""

import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backends import CustomResponseModel, HumanModel
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


# TODO Determine if the HumanPlayer class is necessary; is the inbuilt _terminal_response method sufficient?
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

    # TODO Determine human player behavior
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
        """
        pass


class ProgrammaticPlayer(LudoPlayer):
    """
    A programmatic participant in the game 'Ludo'. Its custom response behavior
    is described in self._custom_response.
    """
    def __init__(self, model: CustomResponseModel) -> None:
        """
        Passes along the input CustomResponseModel object to the parent class.

        Args:
            model (CustomResponseModel): the instantiated CustomResponseModel
        """
        super().__init__(model)

    # TODO Determine programmatic player behavior
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
        parsed_messages: list[dict[str: int]] = self._parse_messages(messages)

    def _parse_messages(self, messages: list[dict]) -> list[dict[str: int]]:
        """
        Given a list of player-message pairs detailing all interactions that
        have occured thus far, parses each of the messages at each time step,
        stores them in a dictionary of player name-parsed message pairs, then
        returns a list of all the turns.
        
        Args:
            messages (list[dict]): contains all the messages in the
                                   conversation thus far
        
        Returns:
            list[dict[str: int]]: contains dictionaries containing turn number
                                  -parsed message pairs
        """
        return {
            turn: self._parse_turn(message)
            for turn, message in enumerate(messages)
        }

    # TODO Replace "player_1" and "player_2" with real keys
    @staticmethod
    def _parse_turn(self, turn: dict) -> dict[dict[str: int]]:
        """
        Parses the input text according to an expected input format in order to
        extract per token moves.

        Args:
            turn (dict): contains raw input messages in player-message pairs

        Returns:
            dict[dict[str: int]]: contains parsed messages in the form of
                                  token-position pairs for each player
        """
        return {
            "player_1": parse_text(turn["player_1"]),
            "player_2": parse_text(turn["player_2"])
        }


def parse_text(text: str) -> dict[str: int]:
    """
    Parses the input text according to an expected input format in order to
    extract per token moves.

    Args:
        text (str): raw input text

    Returns:
        dict[str: int]: contains token-position pairs

    Raises:
        ValueError: raises when the text does not match the expected
                    format; prints a preview of the non-conforming text
    """
    matches: re.Match = re.search(r"MY MOVE: X -> (\d+) ; Y -> (\d+)", text)

    if not matches:
        raise ValueError(f"Invalid text format: {text[:20]}")
    
    return {"X": int(matches.group(1)), "Y": int(matches.group(2))}


def main() -> None:
    pass


if __name__ == '__main__':
    main()
