"""
TODO Module description
"""

import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backends import Model
from clemgame.clemgame import Player
from player import HumanPlayer, ProgrammaticPlayer


class Game:
    """
    A class which handles the game behavior of Ludo, namely prompting the model
    to make its next move given the current game state.
    """
    def __init__(
        self,
        player_1: Player,
        player_2: HumanPlayer | ProgrammaticPlayer,
        initial_prompt: str
    ) -> None:
        """
        Initializes chat-based attributes.

        Args:
            player_1 (LudoPlayer): represents the LLM player
            player_1 (LudoPlayer): represents either the programmatic or human
                                   player, depending on the game variation
            initial_prompt (str): contains both the system prompt and the task
                                  description for Ludo, the latter of which
                                  details intructions and constraints for the
                                  gameplay, as well as examples
        """
        self.player_1: LudoPlayer = player_1
        self.player_2: LudoPlayer = player_2
        self.initial_prompt: str = initial_prompt
        self.context: list = []

    # TODO Adjust for player 2
    def make_move(
            self,
            turn: int,
            roll: int,
            current_state: str
    ) -> dict[str: int]:
        """
        Crafts a turn-dependent message, sends it to the model, receives a
        response, then parses the response in the form of a move dictionary.

        Args:
            turn (int): the current turn in the game
            roll (int): the die roll for the current turn
            current_state (str): a representation of the state of the board

        Returns:
            dict[str: int]: contains token-position pairs defining the model's
                            move
        """
        # Creates and sends turn-dependent prompts
        message: str = (
            f"Beginning state: {current_state}\n" if turn == 0
            else f"Current state: {current_state}\n"
        )
        message += (
            f"Turn: {turn}, Roll: {roll}\n" +
            "Where will you move your token? Let's think step by step."
        )
        self.add_message(message)

        # Generates and parses LLM's response
        _, _, output_text = self.player_1.model.generate_response(self.context)

        return self._parse_text(output_text), output_text
    
    # TODO Adjust for player 2
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
            self.context = [
                {
                    "role": "system",
                    "content": self.initial_prompt.partition("\n")[0]
                },
                {
                    "role": "user",
                    "content": "".join(self.initial_prompt.partition("\n")[2])
                }
            ]

        self.context.append({"role": role, "content": message})

    @staticmethod
    def _parse_text(text: str) -> dict[str: int]:
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
    
        
    # TODO Implement reprompting functionality
    def _reprompt(self) -> None:
        """
        TODO Method description
        """
        pass


def main() -> None:
    pass


if __name__ == "__main__":
    main()
