"""
Module description
"""

import re
import sys

sys.path.append('../../clemgame')  # Path to clemgame module
sys.path.append('../../')  # Path to the parent directory which contains backends

from clemgame.clemgame import GameBenchmark, GameMaster


GAME_NAME: str = "ludo"

class LudoGameMaster(GameMaster):
    """
    Class description
    """
    def __init__(
            self,
            experiment: dict,
            system_prompt: str,
            task_description: str
    ) -> None:
        """
        Method description

        Args:
            experiment (dict):
            system_prompt (str):
            task_description (str):
        """
        super().__init__(GAME_NAME)
        self.experiment: dict = experiment
        self.system_prompt: str = system_prompt
        self.task_description: str = task_description

    def setup(self) -> None:
        """
        Initializes all relevant conversation, board, token, and turn
        attributes.
        """
        # Conversation attributes
        self.context: list = []
        
        # Board attributes
        self.rolls: list = self.experiment["rolls"]
        self.n_fields: int = self.experiment["n_fields"]
        self.board: str = self._setup_board()
        self.current_state: str = self._setup_board()

        # Token attributes
        self.tokens: dict[str[dict]] = {
            "X": {"position": 0, "inplay": False},
            "Y": {"position": 0, "inplay": False}
        }
        
        # Turn attributes
        self.turn: int = 0
        self.turn_limit: int = self.experiment["turn_limit"]

    # TODO Implement gameplay loop
    def play(self) -> None:
        """
        Method description
        """
        while self.turn < self.turn_limit:
            pass

    # TODO Implement evaluation procedure -- metrics TBD
    def compute_score(self) -> None:
        """
        Method description
        """
        pass

    def _add_message(self, message: str, role: str = "user") -> None:
        """
        Adds a message to the conversation context. If it is the first message
        being added, the system prompt is added to the beginning.

        Args:
            message (str): to be added to the conversation context
            role (str): either 'system', 'assistant', or 'user'
        """
        if not self.context:
            self.context = [{"role": "system", "content": self.system_prompt}]

        self.context.append({"role": role, "content": message})

    # TODO Implement check_move function
    def _check_move(self, move: dict[str: int], roll: int) -> bool:
        """
        Checks the validity of the move, given the current state of the board
        and the number rolled.

        Args:
            move (dict[str: int]): contains token-position pairs
            roll (int): the die roll

        Returns:
            bool: True if the move is valid

        Raises:
            ValueError: raised if the move is invalid, explaining why
        """
        if self._check_both_tokens_moved(move):
            raise ValueError("Both in-play tokens were moved simultaneously.")
        
        moved_token: str = self._get_moved_token(self._check_token_moved(move))

        check_list: list = []
        for token in move.keys():
            current_position: int = self.tokens[token]["position"]
            match [token == moved_token, self.tokens[token]["inplay"]]:
                # Token wasn't moved and hasn't been played to the board
                case [False, False]:
                    if roll != 6:
                        check_list.append(True)
                        continue
                    else:
                        raise ValueError(f"Token {token} can be played to the board but wasn't.")

                # Token wasn't moved but has been played to the board
                case [False, True]:
                    if (roll + current_position > self.n_fields):
                        check_list.append(True)
                        continue
                    else:
                        raise ValueError(f"Token {token} can be moved but wasn't.")

                # Token was played and has been played to the board
                case [True, True]:
                    if roll == 6 and move[token] == 1:
                        check_list.append(True)
                        continue
                    elif current_position + roll == move[token]:
                        check_list.append(True)
                        continue
                    else:
                        raise ValueError(f"Token {token} was not moved appropriately.")
                    
        if all(check_list):
            return True

    def _check_both_tokens_moved(self, move: dict[str: int]) -> bool:
        """
        Given a move, checks if both tokens have been moved.

        Args:
            move (dict[str: int]): contains token-position pairs

        Returns:
            bool: True if both tokens have been moved, False otherwise
        """
        return (
            True if all(
                [value for value in self._check_token_moved(move).values()]
            ) else False
        )

    def _check_token_moved(self, move: dict[str: int]) -> dict[str: bool]:
        """
        Given a move, checks for both tokens to see if they have been moved.

        Args:
            move (dict[str: int]): contains token-position pairs

        Returns:
            dict[str: bool]: contains token-bool pairs, which are True if said
                             token has been moved, False otherwise
        """
        return {
            token: self.tokens[token]["position"] != position
            for token, position in move.items()
        }
    
    @staticmethod
    def _get_moved_token(tokens_moved: dict[str: bool]) -> str | None:
        """
        Given token-bool pairs, where the boolean value is True if the token
        was moved, retrieves the token if it was moved.

        Args:
            tokens_moved (dict[str: bool]): contains token-bool pairs, which
                                            are True if said token has been
                                            moved, False otherwise

        Returns:
            str | None: name of the token that was moved
        """
        for token in tokens_moved.keys():
            if tokens_moved[token]:
                return token
            else:
                return None

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

    def _setup_board(self) -> str:
        """
        Sets the board to its initial blank state.
        """
        return " ".join(["□"] * self.n_fields).strip()

    def _update_board(self, move: dict[str: int]) -> None:
        """
        Given the current state of the board and the desired move, updates the
        board by moving the token to the new position and replacing the
        previous position with an empty field character.

        Args:
            move (dict[str: int]): contains the desired position for all tokens
        """
        split_board: list[str] = self.current_state.split()

        for token in move.keys():
            if self.tokens_inplay[token]:
                split_board[self.current_position[token] - 1] = "□"
                split_board[move[token]] = token

        self.current_state = " ".join(split_board).strip()


class LudoGameBenchmark(GameBenchmark):
    def __init__(self, game_instance, player_models):
        super().__init__("ludo")
        self.game_master = LudoGameMaster(player_models[0])

    def get_description(self):
        return "Benchmark for the Ludo game designed to challenge and evaluate strategic model behavior."


def register_benchmark():
    return {'ludo': LudoGameBenchmark}


def main() -> None:
    pass


if __name__ == "__main__":
    main()
