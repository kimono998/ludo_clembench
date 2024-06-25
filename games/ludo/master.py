"""
TODO Module description
"""

import sys
from logging import Logger
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backends import Model
from clemgame.clemgame import GameBenchmark, GameMaster
from game import Game
from instancegenerator import LudoInstanceGenerator
from player import LudoPlayer, parse_text
from scoring import LudoGameScorer
from clemgame import get_logger


GAME_NAME: str = "ludo"
logger: Logger = get_logger(__name__)

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
        self.error: str | None = None

    def setup(self, **kwargs) -> None:
        """
        Reads the specifications of a game instance, then passes them, along
        with the player models, to the instance-specific Game object.
        Additionally, sets up and logs the player dictionary.

        Args:
            game_id (str): an identifying string for each game instance
            initial_prompt (str): the first message sent to the LLM
            n_fields (int): the number of fields on the board
            rolls (list[int]): the specific die rolls for each turn
        """
        self.game: Game = Game(
            kwargs.get("initial_prompt"),
            kwargs.get("n_fields"),
            kwargs.get("rolls"),
            self.player_models
        )
        self.players_dic: dict[str: LudoPlayer] = {
            "GM": 'Game Master for Ludo',
            "player_1": self.game.player_1
        }

        if self.game.player_2:
            self.players_dic["player_2"] = self.game.player_2

        self.log_players(self.players_dic)
        del self.players_dic['GM']

    # TODO Write something for when the reprompting limit is exceeded -- e.g., failure/game aborting message
    def play(self) -> None:
        """
        Handles the basic gameplay loop. While the game is not finished, for
        each turn that does not exceed the turn limit, each player is given
        their roll as well as a prompting message. They produce their
        responses, which are then parsed and verified. If the move is valid,
        the board and the game are updated to reflect this. If the move is not
        valid, the player is reprompted up to a maximum of three times, after
        which time, the game is aborted.
        """
        while self.game.turn < self.game.turn_limit or not self._check_if_done:
            logger.info(f"Game turn: {self.game.turn}")
            self.log_next_turn()

            for index, player in enumerate(self.players_dic.keys()):
                roll: int = self.game.rolls[self.game.turn][index]

                # Composes and logs the message sent to player 1
                message: str = f"Current state: {self.game.current_state}\n"
                message += f"Turn number: {self.game.turn}, Roll: {roll}. "
                message += "Where will you move your token?"
                self.game.add_message(message)
                self.log_event(
                    from_="GM",
                    to="Player 1",
                    action={
                        "type": "send message",
                        "content": message
                    }
                )

                # Gameplay loop until player is reprompted too many times
                while self.game.reprompt_attempts < 3:
                    # Gets the player's response and logs it
                    _, _, response_text = self.players_dic[player](
                        self.game.context
                        if type(self.players_dic[player]) is LudoPlayer()
                        else message,
                        self.game.turn
                    )
                    self.log_event(
                        from_=f"{player}",
                        to="GM",
                        action={
                            'type': 'get message',
                            'content': response_text
                        },
                        call=(message, response_text)
                    )

                    # Parses the player's move from their response
                    move: dict[str: int] = parse_text(response_text)
                    self.log_event(
                        from_="GM",
                        to="GM",
                        action={
                            'type': 'parse',
                            'content': response_text,
                            'expression': move
                        }
                    )

                    # Updates game attributes if move is valid
                    if self._check_move(
                        self.players_dic[player].tokens,
                        move,
                        roll,
                        self.game.n_fields
                    ):
                        # Sends and logs the player's response
                        self.game.add_message(
                            response_text,
                            role=(
                                "assistant"
                                if type(self.players_dic[player]) is LudoPlayer()
                                else "user"
                            )
                        )
                        self.log_event(
                            from_=f"GM",
                            to="GM",
                            action={
                                'type': 'update board state',
                                'content': response_text
                            }
                        )

                        # Updates status and position of player tokens
                        for token in move.keys():
                            self.players_dic[player].tokens["in_play"] = move[token] > 0
                            self.players_dic[player].tokens["position"] = move[token]

                        self.game.update_board(self.players_dic[player], move)
                        self.game.reprompt_attempts = 0

                    # Reprompt the player if not
                    else:
                        self.log_event(
                            from_=f"GM",
                            to="GM",
                            action={
                                'type': f'{self.error[0]}',
                                'content': (
                                    f'Reprompting attempt: {self.game.reprompt_attempts}'
                                    if self.game.reprompt_attempts < 3
                                    else 'Aborting'
                                )
                            }
                        )
                        self.game.reprompt(self.error[0], self.error[1])
                        self.error = None

            self.game.turn += 1

    def _check_both_tokens_moved(
        self,
        tokens: dict[str: dict],
        move: dict[str: int]
    ) -> bool:
        """
        Given a move, checks if both tokens have been moved.

        Args:
            tokens (dict[str: dict]): specifies the positions of the player's
                                      token and whether or not they are on the
                                      board
            move (dict[str: int]): contains token-position pairs

        Returns:
            bool: True if both tokens have been moved, False otherwise
        """
        return bool(all(value for value in self._check_token_moved(tokens, move).values()))

    def _check_if_done(self) -> bool:
        """
        Checks if the game is done by looking at the position of each players'
        tokens and seeing if, for either player, both tokens have reached the
        final field.

        Returns:
            bool: True if the game has finished, False otherwise
        """
        for player in self.players_dic.values():
            tokens: list[str] = (
                ['X', 'Y']
                if type(player) is LudoPlayer()
                else ['A', 'B']
            )
            if (
                player.tokens[tokens[0]]['position'] == self.game.n_fields and
                player.tokens[tokens[1]]['position'] == self.game.n_fields
            ):
                return True

        return False

    def _check_move(
        self,
        tokens: dict[str: dict],
        move: dict[str: int],
        roll: int,
        n_fields: int
    ) -> bool:
        """
        Checks the validity of the move, given the current state of the board
        and the number rolled.

        Args:
            tokens (dict[str: dict]): specifies the positions of the player's
                                      token and whether or not they are on the
                                      board
            move (dict[str: int]): contains token-position pairs
            roll (int): the die roll for the current turn
            n_fields (int): indicates the size of the board

        Returns:
            bool: True if the move is valid

        Raises:
            ValueError: raised if the move is invalid, explaining why
        """
        if self._check_both_tokens_moved(tokens, move):
            self.error: str = "simultaneous_move"
            return False

        moved_token: str = self._get_moved_token(self._check_token_moved(tokens, move))

        check_list: list = []
        for token in move.keys():
            current_position: int = tokens[token]["position"]
            match [token == moved_token, tokens[token]["in_play"]]:
                # Token wasn't moved and hasn't been played to the board
                case [False, False]:
                    if roll != 6:
                        check_list.append(True)
                        continue
                    self.error: tuple = ("not_moved_to_board", token)
                    return False

                # Token wasn't moved but has been played to the board
                case [False, True]:
                    if roll + current_position > n_fields:
                        check_list.append(True)
                        continue
                    self.error: tuple = ("not_moved", token)
                    return False

                # Token was played and has been played to the board
                case [True, True]:
                    if roll == 6 and move[token] == 1:
                        check_list.append(True)
                        continue
                    if current_position + roll == move[token]:
                        check_list.append(True)
                        continue
                    self.error: tuple = ("incorrect_move", token)
                    return False

        if all(check_list):
            return True

    def _check_token_moved(
        self,
        tokens: dict[str: dict],
        move: dict[str: int]
    ) -> dict[str: bool]:
        """
        Given a move, checks for both tokens to see if they have been moved.

        Args:
            tokens (dict[str: dict]): specifies the positions of the player's
                                      token and whether or not they are on the
                                      board
            move (dict[str: int]): contains token-position pairs

        Returns:
            dict[str: bool]: contains token-bool pairs, which are True if said
                             token has been moved, False otherwise
        """
        return {
            token: tokens[token]["position"] != position
            for token, position in move.items()
        }

    def _get_moved_token(self, tokens_moved: dict[str: bool]) -> str | None:
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
            return None


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


if __name__ == "__main__":
    from clemgame import benchmark
    from scripts.cli import read_model_specs

    game_name: str = "ludo"
    model_specs: list[str] = ["gpt-3.5-turbo-1106", "programmatic"]
    gen_args: dict[str: str] = {"temperature": 0.0, "max_tokens": 400}
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
    # benchmark.score(
    #     game_name=game_name,
    #     experiment_name=experiment_name,
    #     results_dir=results_dir
    # )
    # benchmark.transcripts(
    #     game_name=game_name,
    #     experiment_name=experiment_name,
    #     results_dir=results_dir
    # )
