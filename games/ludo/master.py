"""
Module description
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backends import Model, get_model_for, load_model_registry
from clemgame.clemgame import GameBenchmark, GameMaster
from game import Game
from instancegenerator import LudoInstanceGenerator, GAME_NAME
from player import LudoPlayer
from scoring import LudoGameScorer


THIS_MODEL: dict = {
    "model_id": "gpt-3.5-turbo-1106",
    "backend": "openai",
    "model_name": "gpt-3.5-turbo-1106"
}

# TODO Add in logger functionality for each stage of the game
class LudoGameMaster(GameMaster):
    """
    In carrying out the game 'Ludo' with a LLM, this class controls the general
    gameplay loop, including setting up the relevant attributes, passing along
    necessary information to the Game object, checking the validity of the
    resulting decisions made by the LLM, and adjusting the game state
    accordingly. Once the game has come to a close, this class also handles the
    evaluation procedures.
    """
    def __init__(
        self,
        experiment: dict[str: dict],
        player_models: list[Model] | None = None
    ) -> None:
        """
        Initializes attributes from the passed in arguments, as well as
        attributes related to evaluation.

        Args:
            experiment (dict[str: dict]): id-instance pairs, each containing
                                          details for a game instance
            TODO player_models (list[Model] | None): 
        """
        super().__init__(GAME_NAME, experiment)
        self.player_models: list[Model] | None = None # TODO Adjust to allow for player model(s)

    # TODO Adjust for **kwargs
    def setup(**kwargs) -> None:
        """
        Reads the specifications of a game instance, then initializes the
        attributes related to the game, the board, the tokens, and the turns.

        Args:
            game_id (str): an identifying string for each game instance
            initial_prompt (str): the first message sent to the LLM
            n_fields (int): the number of fields on the board
            rolls (list[int]): the specific die rolls for each turn
            turn_limit (int): the maximum number of allowed turns
        """
        self.game: Game = Game(self.llm, initial_prompt) # TODO Adjust to allow for player model(s)
        self.playing: bool = True # TODO Reconsider for loop
        
        # Board attributes
        self.rolls: list = rolls
        self.n_fields: int = n_fields
        self.current_state: str = self._set_up_board()

        # Token attributes
        self.tokens: dict[str[dict]] = {
            "X": {"position": 0, "inplay": False},
            "Y": {"position": 0, "inplay": False}
        }
        
        # Turn attributes
        self.turn: int = 0
        self.turn_limit: int = turn_limit

    # TODO Adapt to allow for iterating over experiment
    def play(self) -> None:
        """
        Handles the basic gameplay loop.
        """
        while self.playing and self.turn < self.turn_limit:
            # Makes move, then storess move for later evaluation
            move, output_text = self.game.make_move(
                self.turn,
                self.rolls[self.turn],
                self.current_state
            )
            self.history[self.turn] = move

            # Checks if move is valid
            if self._check_move(move, self.rolls[self.turn]):
                self.game.add_message(output_text, role="assistant")
                for token in move.keys():
                    self.tokens[token]["inplay"] = move[token] > 0
                    self.tokens[token]["current_position"] = move[token]
                self._update_board(move)
                self.turn += 1
            
            # Ends game if not
            else:
                self.playing = False

    # TODO Implement evaluation procedure, decide on metrics, consider GameScorer
    def compute_score(self, results_directory: str | None = None) -> None:
        """
        Method description
        """
        self.scorer

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

    # TODO Finish
    def _restart_game(self) -> None:
        """
        Method description
        """
        self.current_state = self._set_up_board()
        self.turn = 0

        for token in self.tokens.keys():
            self.tokens[token]["inplay"] = False
            self.tokens[token]["current_position"] = 0

    def _set_up_board(self) -> str:
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
    """
    Organizes the running of an experiment of the game 'Ludo'.
    """
    def __init__(
        self,
        experiment_filename: str = 'instances.json',
        initial_prompt_filename: str = 'initial_prompt.template',
        is_single_player: bool = False
    ):
        """
        Passes along the game name and allows for the creation of the game
        master.

        Args:
            experiment_filename (str): name of the experiment file, set to
                                       'instances.json' by default
            is_single_player (bool): True if the game is set in single-player
                                     mode, False otherwise; set by default to
                                     False
        """
        super().__init__(GAME_NAME)
        self.experiment: dict = self.load_json(experiment_filename)
        self.is_single_player: bool = is_single_player

        # Include filenames to be used, others will be ignored
        self.filter_experiment: list = []

    def get_description(self) -> str:
        """
        Returns a short description of the Ludo game benchmark.

        Returns:
            str: benchmark description
        """
        return (
            "Benchmark for the Ludo game designed to challenge and " + 
            "evaluate strategic model behavior."
        )

    def create_game_master(self, llm: Model) -> LudoGameMaster:
        """
        Given an instantiated LLM Model object, creates a custom GameMaster.

        Args:
            llm (Model): loaded LLM which will participate in the game

        Returns:
            LudoGameMaster: instantiated LudoGameMaster object
        """
        return LudoGameMaster(llm, self.experiment)

    def is_single_player(self) -> bool:
        """
        An in-built function which determines if the game is single-player or
        not.

        Returns:
            bool: True if single-player, False otherwise
        """
        return self.is_single_player


def main() -> None:
    # Instantiates and configures model
    load_model_registry()
    llm: Model = get_model_for(THIS_MODEL)
    llm.set_gen_args(temperature=0.0, max_tokens=400)

    # Generates game instances
    instance_generator: LudoInstanceGenerator = LudoInstanceGenerator() # TODO
    
    # Locates game instances and resources
    experiment_filename: str = "in/instances.json"

    # Instantiates game master
    game_benchmark: LudoGameBenchmark = LudoGameBenchmark(experiment_filename)
    game_master: LudoGameMaster = game_benchmark.create_game_master(llm)
    game_master.setup()

    # Begins gameplay loop
    game_master.play() # TODO

    # Evaluates LLM performance
    game_master.compute_score() # TODO


if __name__ == "__main__":
    main()
