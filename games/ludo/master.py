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
            llm: Model,
            experiment: dict[str: dict],
            system_prompt: str,
            task_description: str
    ) -> None:
        """
        Initializes attributes from the passed in arguments, as well as
        attributes related to evaluation.

        Args:
            llm (Model): the LLM partaking in the game
            experiment (dict[str: dict]): contains multiple game instances
            system_prompt (str): the loaded system prompt, which is the first
                                 message passed to the LLM
            task_description (str): the loaded task description, which is the
                                    second message passed to the LLM, both
                                    detailing the scope and constraints of the
                                    game and giving relevant expamples to
                                    gameplay mechanics
        """
        super().__init__(GAME_NAME, experiment)
        self.llm: Model = llm
        self.experiment: dict[str: dict] = experiment
        self.system_prompt: str = system_prompt
        self.task_description: str = task_description
        self.history: dict[str: dict] = {}

    # TODO Adapt to allow for iterating over experiment
    def setup(self) -> None:
        """
        Initializes all relevant game, board, token, and turn attributes.
        """
        self.game: Game = Game(
            self.llm,
            self.system_prompt,
            self.task_description
        )
        self.playing: bool = True
        
        # Board attributes
        self.rolls: list = self.experiment["rolls"] # TODO Adapt to set of instances
        self.n_fields: int = self.experiment["n_fields"] # TODO Adapt to set of instances
        self.board: str = self._set_up_board()
        self.current_state: str = self._set_up_board()

        # Token attributes
        self.tokens: dict[str[dict]] = {
            "X": {"position": 0, "inplay": False},
            "Y": {"position": 0, "inplay": False}
        }
        
        # Turn attributes
        self.turn: int = 0
        self.turn_limit: int = self.experiment["turn_limit"] # TODO Adapt to set of instances

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

    # TODO Implement evaluation procedure -- metrics TBD
    def compute_score(self) -> None:
        """
        Method description
        """
        pass

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
    Organizes the running of an experiment of the game Ludo.
    """
    def __init__(
        self,
        instance_filepath: Path,
        resource_filepath: Path,
        is_single_player: bool = False
    ):
        """
        Passes along the game name, then loads the experiment, the system
        prompt, and the task description.

        Args:
            instance_filepath (Path): points to the directory containing the
                                      instances
            resource_directory_filepath (Path): points to the directory
                                                containing the resources
            is_single_player (bool): True if the game is set in single-player
                                     mode, False otherwise; set by default to
                                     False
        """
        super().__init__(GAME_NAME)
        self.experiment: dict = self._load_experiment(instance_filepath)
        self.system_prompt: str = self._load_file(
            resource_filepath / "system_prompts" / "system_prompt.txt"
        )
        self.task_description: str = self._load_file(
            resource_filepath / "task_descriptions" / "multitoken_v1_pace.txt"
        )

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
        Given an instantiated LLM Model object, creates a custom GameMaster
        using the loaded experiment, system prompt, and task description.

        Args:
            llm (Model): loaded LLM which will participate in the game

        Returns:
            LudoGameMaster: instantiated LudoGameMaster object with loaded
                            experiment, system prompt, and task description
        """
        return LudoGameMaster(
            llm,
            self.experiment,
            self.system_prompt,
            self.task_description
        )

    def is_single_player(self) -> bool:
        """
        An in-built function which determines if the game is single-player or
        not.

        Returns:
            bool: True if single-player, False otherwise
        """
        return self.is_single_player

    def _load_experiment(self, filepath: Path) -> dict[dict]:
        """
        Given a filepath leading to the directory containing the instance .json
        files, iterates through the directory and loads the instances into
        dictionaries and loads all dictionaries into one dictionary.

        Args:
            filepath (Path): points to the instance directory

        Returns:
            dict[dict]: contains id-instance pairs
        """
        experiment: dict = {}
        for instance in filepath.iterdir():
            experiment[instance.stem[-3:]] = self._load_file(instance)

        return experiment

    @staticmethod
    def _load_file(filepath: Path) -> str | dict:
        """
        Loads the specified file, intended to be either a .json or .txt file,
        to either a string or a dictionary.

        Args:
            filepath (Path): points to the file to be loaded

        Returns:
            str | dict: contents of the loaded file

        Raises:
            TypeError: raised if an invalid filepath is introduced
        """
        if not filepath.exists():
            raise TypeError(f"The following file could not be found: {filepath}")

        with open(filepath, "r") as file:
            match filepath.suffix:
                case ".json":
                    return json.load(file)

                case ".txt":
                    return file.read()

                case _:
                    raise TypeError(f"Attempted to load an invalid file type: {filepath.suffix}")


def register_benchmark():
    return {'ludo': LudoGameBenchmark}


def main() -> None:
    # Instantiates and configures model
    load_model_registry()
    llm: Model = get_model_for(THIS_MODEL)
    llm.set_gen_args(temperature=0.0, max_tokens=400)

    # Generates game instances
    instance_generator: LudoInstanceGenerator = LudoInstanceGenerator()
    
    # Locates game instances and resources
    instance_filepath: Path = Path(__file__).parent / "in" / "basic"
    resource_filepath: Path = Path(__file__).parent / "resources"

    # Instantiates game master
    game_benchmark: LudoGameBenchmark = LudoGameBenchmark(instance_filepath, resource_filepath)
    game_master: LudoGameMaster = game_benchmark.create_game_master(llm)
    game_master.setup()

    # Begins gameplay loop
    game_master.play()

    # Evaluates LLM performance
    game_master.compute_score()


if __name__ == "__main__":
    main()
