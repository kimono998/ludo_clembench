"""
Describes custom behavior for human and programmatic participants in 'Ludo'.
"""

import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backends import CustomResponseModel, HumanModel, Model
from clemgame.clemgame import Player
from minimax import GameSim, minimax


GM_PATTERN: re.Pattern = re.compile(
    pattern=r"Current state:\s*(.*?)\s*Turn number:\s*(\d+),\s*Roll:\s*(\d+)\.",
    flags=re.DOTALL
)


class LudoPlayer(Player):
    """
    Custom child class of Player which adds player-specific gameplay attributes.
    """
    def __init__(
            self,
            model: CustomResponseModel | HumanModel | Model,
            n_tokens: int
    ) -> None:
        """
        Passes along the Model object to the parent class and initializes
        player-specific attributes.
        
        Args:
            model (Model): associated Model object, or a child class thereof
            n_tokens (int): the number of tokens assigned to the player
        """
        super().__init__(model)
        self.n_tokens: int = n_tokens
        self.tokens: dict = self._initialize_tokens()

    def _create_token_dictionary(self, tokens: list[str]) -> dict[str: dict]:
        """
        Creates a token dictionary according to the specified token number and
        names.
        
        Args:
            tokens (list[str]): contains the name or names of the tokens
        
        Returns:
            dict[str: dict]: for each token, contains the name and a
                             dictionary which details its in-play status and
                             its position on the board
        """
        match self.n_tokens:
            case 1:
                return {tokens[0]: {"in_play": False, "position": 0}}
            case 2:
                return {
                    tokens[0]: {"in_play": False, "position": 0},
                    tokens[1]: {"in_play": False, "position": 0}
                }
    
    def _initialize_tokens(self) -> dict[str: dict]:
        """
        Creates the appropriate token dictionary depending on the type of the
        input model.
        
        Returns:
            dict[str: dict]: for each token, contains the name and a
                             dictionary which details its in-play status and
                             its position on the board
        """
        if type(self.model) == Model:
            return self._create_token_dictionary(["X", "Y"])
        elif (
            type(self.model) == CustomResponseModel or
            type(self.model) == HumanModel
        ):
            return self._create_token_dictionary(["A", "B"])


class HumanPlayer(LudoPlayer):
    """
    A human participant in the game 'Ludo'. Its custom response behavior is
    described in self._terminal_response.
    """
    def __init__(self, model: HumanModel, n_tokens: int) -> None:
        """
        Passes along the input HumanModel object to the parent class.

        Args:
            model (HumanModel): the instantiated HumanModel
            n_tokens (int): the number of tokens assigned to the player
        """
        super().__init__(model, n_tokens)

    # TODO Adapt to single token
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

        examples: list[str] = [f"{token} -> N" for token in self.tokens]
        
        print('What is your next move? Please write:')
        print(f"MY MOVE: {' ; '.join(examples)}")
        
        while True:
            user_input: str = input(f"Your response as {self.__class__.__name__} (turn: {turn_idx}):\n")
            try:
                _ = parse_text(user_input)
            except ValueError:
                print('Input format not valid! Please try again with the proper format.')
                print(f"MY MOVE: {' ; '.join(examples)}")
            else:
                return user_input


class ProgrammaticPlayer(LudoPlayer):
    """
    A programmatic participant in the game 'Ludo'. Its custom response behavior
    is described in self._custom_response.
    """
    def __init__(
            self,
            model: CustomResponseModel,
            n_tokens: int,
            rolls: list[tuple]
    ) -> None:
        """
        Passes along the input CustomResponseModel object to the parent class.

        Args:
            model (CustomResponseModel): the instantiated CustomResponseModel
            n_tokens (int): the number of tokens assigned to the player
            rolls (list[tuple[int, int]]): the roll sequence list from the
                                           game instance
        """
        super().__init__(model, n_tokens)
        self.rolls: list[tuple[int, int]] = rolls

    def _compose_response(self, move: tuple[str, int]) -> str:
        """
        Composes a response message based on the move.

        Args:
            move (tuple[str, int]): the move to be made

        Returns:
            str: the response message
        """
        # Creates and updates local token dictionary
        tokens: dict = self.tokens.copy()
        tokens[move[0]]["position"] = move[1]

        # Composes response
        prefix: str = "MY MOVE: "
        move_messages: list[str] = [
            f"{key} -> {value['position']}"
            for key, value in tokens.items()
        ]

        return prefix + " ; ".join(move_messages)

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
        move: tuple[str, int] = self._make_move(
            token_positions=token_positions,
            rolls=self.rolls,
            n_fields=n_fields,
            turn_number=turn_number
        )

        return self._compose_response(move)
    
    def _make_move(
        self,
        token_positions: dict,
        rolls: list[tuple],
        n_fields: int,
        turn_number: int
    ) -> tuple[str, int]:
        """
        Makes a new move as a programmatic player based on the objective.

        Args:
            token_positions (dict): the positions of the tokens
            rolls (list[tuple]): the rolls for the game
            n_fields (int): the size of the board
            turn_number (int): the current turn number

        Returns:
            tuple[str, int]: the move to be made
        """
        game: GameSim = GameSim(n_fields, token_positions, rolls, turn_number)
        _, move = minimax(game, True)

        return move

    def _parse_messages(
            self,
            input_message: str
    ) -> tuple[dict[str: int], int, int]:
        """
        Parses the input message to obtain the state of the board, as well as
        the current roll.
        
        Args:
            messages (str): contains all the messages in the conversation thus
                            far
        
        Returns:
            tuple[dict[str: int], int, int]: contains a dictionary with token
                                             positions, rolled number, and
                                             board size

        Raises:
            Exception: raised if no matching pattern is found
        """
        pattern_match: re.Match | None = GM_PATTERN.search(input_message)

        if not pattern_match:
            raise Exception('No match found.')
        
        match self.n_tokens:
            case 1:
                tokens: list[str] = ["X", "A"]
            case 2:
                tokens: list[str] = ["X", "Y", "A", "B"]

        token_positions: dict[str: int] = {token: 0 for token in tokens}
        current_state: str = pattern_match.group(1).strip()
        
        for index, char in enumerate(current_state.split()):
            if char in token_positions.keys():
                token_positions[char] = index + 1

        return (
            token_positions,
            int(pattern_match.group(2)),
            len(current_state.split())
        )


def parse_text(text: str, player: LudoPlayer) -> dict[str: int]:
    """
    Parses the input text according to an expected input format in order to
    extract per token moves.

    Args:
        text (str): raw input text
        player (LudoPlayer): the player who produced the text

    Returns:
        dict[str: int]: contains token-position pairs
    """
    tokens: list[str] = list(player.tokens.keys())
    
    match player.n_tokens:
        case 1:
            matches: re.Match = re.search(
                rf"MY MOVE: {tokens[0]} -> (\d+)",
                text
            )
            token_dict: dict[str: int] = {tokens[0]: int(matches.group(1))}
        
        case 2:
            matches: re.Match = re.search(
                rf"MY MOVE: {tokens[0]} -> (\d+) ; {tokens[1]} -> (\d+)",
                text
            )
            token_dict: dict[str: int] = {
                tokens[0]: int(matches.group(1)),
                tokens[1]: int(matches.group(2))
            }

    return token_dict if matches else False


if __name__ == '__main__':
    pass
