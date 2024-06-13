"""
TODO Module description
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backends import CustomResponseModel, HumanModel, Model
from clemgame.clemgame import GameBenchmark, GameMaster, Player
from game import Game
from instancegenerator import LudoInstanceGenerator
from player import HumanPlayer, ProgrammaticPlayer
from scoring import LudoGameScorer


GAME_NAME: str = "ludo"

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
        player_models: list[Model]
    ) -> None:
        """
        Initializes attributes from the passed in arguments, as well as
        attributes related to evaluation.

        Args:
            experiment (dict[str: dict]): id-instance pairs, each containing
                                          details for a game instance
            player_models (list[Model]): contains instantiated Model objects,
                                         representing each of the players
        """
        super().__init__(GAME_NAME, experiment, player_models)
        self.player_models: list[Model] = player_models

    # TODO Adjust for **kwargs
    # TODO Adjust for player 2
    def setup(self, **kwargs) -> None:
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
        # Logs and instantiates the player models
        self._load_players()
        self.log_players({"player_1": self.player_1, "player_2": self.player_2})

        self.game: Game = Game(
            self.player_1,
            self.player_2,
            kwargs.get("initial_prompt")
        )
        self.playing: bool = True # TODO Reconsider for loop
        
        # Board attributes
        self.rolls: list = kwargs.get("rolls")
        self.n_fields: int = kwargs.get("n_fields")
        self.current_state: str = self._reset_board()

        # Token attributes
        self.tokens: dict[str[dict]] = {
            "X": {"position": 0, "inplay": False},
            "Y": {"position": 0, "inplay": False}
        }
        
        # Turn attributes
        self.turn: int = 0
        self.turn_limit: int = kwargs.get("turn_limit")

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
                # TODO Allow for reprompting
                self.playing = False

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

    def _load_players(self) -> None:
        """
        Given the list of player models, loads the models according to their
        model type to appropriate player objects.

        Raises:
            TypeError: raised if player 2's model does not match one of the
                       two expected model types (HumanModel and 
                       CustomResponseModel)
        """
        # Loads player 1
        self.player_1: Player = Player(self.player_models[0])

        # Loads player 2 depending on player 2 model type
        player_2_type: str = type(player_2_model := self.player_models[1])
        
        if player_2_type is HumanModel:
            self.player_2: HumanPlayer = HumanPlayer(player_2_model)

        elif player_2_type is CustomResponseModel:
            self.player_2: ProgrammaticPlayer = ProgrammaticPlayer(player_2_model)

        else:
            raise TypeError(
                "Player 2 must be either a HumanModel or a " +
                f"CustomResponseModel, got {player_2_type} instead."
            )

    # TODO Finish
    def _restart_game(self) -> None:
        """
        TODO Method description
        """
        self.current_state = self._reset_board()
        self.turn = 0

        for token in self.tokens.keys():
            self.tokens[token]["inplay"] = False
            self.tokens[token]["current_position"] = 0

    def _reset_board(self) -> str:
        """
        Sets the board to its initial blank state.

        Returns:
            str: a representation of the board in its initial blank state
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
    def __init__(self):
        """
        Passes along the game name and allows for the creation of the game
        master.
        """
        super().__init__(GAME_NAME)

    # TODO
    def compute_scores(self) -> None:
        """
        TODO Method description
        
        Args:
            TODO
        
        Returns:
            TODO
        """
        pass

    def create_game_master(
        self,
        experiment: dict,
        player_models: list[Model]
    ) -> LudoGameMaster:
        """
        Instantiates a Ludo-specific GameMaster that handles the running and
        checking of the game on an instance level.

        Args:
            experiment (dict): contains the specifications for a number of game
                               instances
            player_models (list[Model]): contains two player models, being of
                                         different child classes depending on
                                         the game variant

        Returns:
            LudoGameMaster: instantiated LudoGameMaster object
        """
        return LudoGameMaster(experiment, player_models)

    def create_game_scorer(
        self,
        experiment: dict,
        game_instance: dict
    ) -> LudoGameScorer:
        """
        Instantiates a Ludo-specific GameScorer that handles the ultimate
        scoring of the game performance on an episodic and overall level.

        Args:
            experiment (dict): contains the specifications for a number of game
                               instances
            player_models (list[Model]): contains two player models, being of
                                         different child classes depending on
                                         the game variant

        Returns:
            LudoGameScorer: instantiated LudoGameScorer object
        """
        return LudoGameScorer(experiment, game_instance)

    def get_description(self) -> str:
        """
        Returns a short description of the Ludo game benchmark.

        Returns:
            str: a short description of the game 'Ludo' and what it seeks to
                 evaluate
        """
        return (
            "Benchmark for the Ludo game designed to challenge and " + 
            "evaluate strategic model behavior."
        )

    def is_single_player(self) -> bool:
        """
        An in-built function which determines if the game is single-player or
        not.

        Returns:
            bool: True if single-player, False otherwise
        """
        return False


def main() -> None:
    from clemgame import benchmark
    from scripts.cli import read_model_specs

    # TODO Test instance generator
    instance_generator: LudoInstanceGenerator = LudoInstanceGenerator()

    game_name: str = "ludo"
    model_specs: list[str] = ["gpt-3.5-turbo-1106", "programmatic"]
    gen_args: dict[str: str] = {"temperature": "0.0", "max_tokens": 400}
    experiment_name: str | None = None
    instances_name: str = "instances"
    results_dir: str = "results"

    benchmark.run(
        game_name=game_name,
        model_specs=read_model_specs(model_specs),
        gen_args=gen_args,
        experiment_name=experiment_name,
        instances_name=instances_name,
        results_dir=results_dir
    )
    benchmark.score(
        game_name=game_name,
        experiment_name=experiment_name,
        results_dir=results_dir
    )
    benchmark.transcripts(
        game_name=game_name,
        experiment_name=experiment_name,
        results_dir=results_dir
    )


if __name__ == "__main__":
    main()
