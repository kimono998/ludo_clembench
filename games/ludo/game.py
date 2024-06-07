"""
Module description
"""

import re
from backends import Model


class Game:
    """
    A class which handles the game behavior of Ludo, namely prompting the model
    to make its next move given the current game state.
    """
    def __init__(
            self,
            llm: Model,
            system_prompt: str,
            task_description: str
    ) -> None:
        """
        Initializes chat-based attributes.

        Args:
            llm (Model): a loaded LLM
            system_prompt (str): the loaded system prompt, which is the first
                                 message passed to the LLM
            task_description (str): the loaded task description, which is the
                                    second message passed to the LLM, both
                                    detailing the scope and constraints of the
                                    game and giving relevant expamples to
                                    gameplay mechanics
        """
        self.llm: Model = llm
        self.system_prompt: str = system_prompt
        self.task_description: str = task_description
        self.context: list = []

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
        _, _, output_text = self.llm.generate_response(self.context)

        return self._parse_text(output_text), output_text
    
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
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.task_description}
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
        Method description
        """
        pass


def main() -> None:
    pass


if __name__ == "__main__":
    main()
