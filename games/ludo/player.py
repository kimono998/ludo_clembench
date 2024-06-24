"""
Describes custom behavior for human and programmatic participants in 'Ludo'.
"""

import re
import sys
from pathlib import Path
from math import sqrt, log
from minimax import GameSim, minimax
import random

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


# TODO Determine if the HumanPlayer class is necessary; is the inbuilt _terminal_response method sufficient?
class HumanPlayer(LudoPlayer):
    """
    A human participant in the game 'Ludo'. Its custom response behavior is
    described in self._terminal_response.
    """
    def __init__(self, model: HumanModel, tokens: dict) -> None:
        """
        Passes along the input HumanModel object to the parent class.

        Args:
            model (HumanModel): the instantiated HumanModel
        """
        super().__init__(model, tokens)
        self.tokens['A'] = {
            "in_play": False,
            "position": 0}

        self.tokens['B'] = {
            "in_play": False,
            "position": 0}


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
        # should probably do all the verifications for user moves here.


        print(messages)
        print('What is your next move? Please write \nMY MOVE: A -> N ; B -> N')
        #this probably needs re-working. High likelyhood of user fucking it up.
        while True:
            user_input = input(f"Your response as {self.__class__.__name__}:\n")
            try:
                _ = parse_text(user_input)
            except ValueError:
                print('Input format not valid! Please try again with the proper format.')
                print('MY MOVE: A -> N ; B -> N')
            else:
                return user_input


class ProgrammaticPlayer(LudoPlayer):
    """
    A programmatic participant in the game 'Ludo'. Its custom response behavior
    is described in self._custom_response.
    """
    def __init__(self, model: CustomResponseModel, tokens: dict, rolls: list) -> None:
        """
        Passes along the input CustomResponseModel object to the parent class.

        Args:
            model (CustomResponseModel): the instantiated CustomResponseModel
        """
        super().__init__(model, tokens)
        self.tokens['A'] = {
            "in_play": False,
            "position": 0}

        self.tokens['B'] = {
            "in_play": False,
            "position": 0}

        self.rolls = rolls

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
        token_positions, turn_number, board_size = self._parse_messages(messages)

        move = self._make_move(token_positions, self.rolls, board_size, turn_number)
        resp = self._compose_response(move)

        return resp


    def _parse_messages(self, input_message: str) -> list[dict, int, int]:
        """
        Parse the input message to obtain the state of the board, as well as the current roll.
        
        Args:
            messages (str): contains all the messages in the
                                   conversation thus far
        
        Returns:
            list[dict, int]:  list with [Dictionary with token positions, rolled number, board size]

        """

        # Define the regex pattern
        pattern = r"Current state:\s*(.*?)\s*Turn number:\s*(\d+),\s*Roll:\s*(\d+)\."

        # Apply the regex pattern to extract the required information
        match = re.search(pattern, input_message, re.DOTALL)

        if match:
            current_state = match.group(1).strip()  # Extract the current state block
            turn_number = int(match.group(2))  # Extract the turn number (as integer)
            _ = int(match.group(3))  # Extract the roll (as integer)

            # Identify the positions of tokens (X, Y, A, B) in the current state
            token_positions = {}
            tokens = {"X", "Y", "A", "B"}
            board_size = len(current_state.split())

            for token in tokens:
                token_positions[token] = 0  # Initialize all tokens to 0

            for index, char in enumerate(current_state.split()):
                if char in tokens:
                    token_positions[char] = index + 1  # Store 1-based index

            return token_positions, turn_number, board_size

        else:
            raise Exception('No match found')


    def _compose_response(self, move):
        # format a response message
        token = move[0]
        pos = move[1]

        temp = self.tokens.copy()
        temp[token] = pos

        return f"MY MOVE: A -> {temp['A']} ; B -> {temp['B']}"


    # make a new move as a programmatic player based on the objective.
    def _make_move(self, token_positions, rolls, board_size, turn_number):

        game = GameSim(board_size, token_positions, rolls, turn_number)
        _, move = minimax(game, True)

        return move



def parse_text(text: str, player) -> dict[str: int]:
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

    tokens = ['X', 'Y'] if type(player) is LudoPlayer else ['A', 'B']
    matches: re.Match = re.search(rf"MY MOVE: {tokens[0]} -> (\d+) ; {tokens[1]} -> (\d+)", text)

    if not matches:
        raise ValueError(f"Invalid text format: {text[:20]}")
    
    return {"X": int(matches.group(1)), "Y": int(matches.group(2))}


# P2 will use MINIMAX, and have access to the instance rolls.
# 2 objectives to select -> win and eliminate P1. # to be done still
# once P1 is eliminated, the objective switches to win













def main() -> None:
    pass


if __name__ == '__main__':
    main()
