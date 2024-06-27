"""
Contains custom GameMaster and GameBenchmark child classes to handle the game
of 'Ludo', describing intended behavior.
"""

import sys
from logging import Logger
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backends import Model
from clemgame.clemgame import GameBenchmark, GameMaster
from game import Game
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
            "Player 1": self.game.player_1
        }
        self.player_log: dict ={
            "GM": 'Game Master for Ludo',
            "Player 1": self.game.player_1.get_description()
        }

        if self.game.player_2:
            self.players_dic["Player 2"] = self.game.player_2
            self.player_log["Player 2"] = self.game.player_2.get_description()

        self.log_players(self.player_log)

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
        while not self._check_game_status():
            logger.info("Game turn: %d", self.game.turn)
            self.log_next_turn()
            self.log_event(
                from_="GM",
                to="GM",
                action={
                    'type': 'current state',
                    'content': self.game.current_state
                }
            )
            logger.info(f"current_state: {self.game.current_state}")
            
            for index, player in enumerate(self.players_dic.keys()):
                roll: int = (
                    self.game.rolls[self.game.turn][index]
                    if len(self.players_dic.keys()) > 1
                    else self.game.rolls[self.game.turn]
                )

                message: str = self._build_message(roll, player)
                logger.info(f"message_to_llm: {message}")
                
                # Checks if we can proceed with the game and logs Player to GM
                can_proceed, response_text, move = self._does_game_proceed(player, message, roll)
                logger.info(f'resp = {response_text}, move = {move}')

                # If so, the move is logged and we continue to next player
                if can_proceed:
                    self.log_event(
                        from_="GM",
                        to="GM",
                        action={'type': 'accepted move', 'content': move}
                    )
                    continue

                # If not, game is aborted, logged, and the inner loop breaks
                else:
                    self.log_event(
                        from_="GM",
                        to="GM",
                        action={'type': 'invalid format', 'content': 'abort game'}
                    )
                    self.game.is_aborted = True
                    break

            # If the game is aborted, breaks the outer loop
            if self.game.is_aborted:
                break

            else:
                self.game.turn += 1

        # Once game is complete, we exit the loop and log the result
        self.log_event(
            from_="GM",
            to="GM",
            action={
                'type': 'metadata',
                'content': f'game_result = {self._check_game_status()}'
            }
        )
        self._log_assets()

    def _build_message(self, roll: int, player: str) -> str:
        """
        Constructs a message for the player with the current game state, turn
        number, and roll. The message is then logged as an event.

        Args:
            roll (int): the roll of the dice for the current turn
            player (str): the name of the player for whom the message is being
                          built

        Returns:
            str: the constructed message
        """
        message: str = f"Current state: {self.game.current_state}\n"
        message += f"Turn number: {self.game.turn}, Roll: {roll}. "
        message += "Where will you move your token?"
        self.game.add_message(message)

        self.log_event(
            from_="GM",
            to=f"{player}",
            action={'type': 'send message', 'content': message}
        )

        return message

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
    
    def _check_game_status(self) -> str | bool:
        """
        Performs various checks to acertain the current status of the game,
        being either 'ABORTED', 'DRAW', 'WIN' 'LOSE', or False.

        Returns:
            str | bool: the game status or False if the game is still in
                        progress
        """
        if self.game.is_aborted:
            return 'ABORTED'
        
        if self.game.turn == self.game.turn_limit:
            return 'DRAW'
        
        elif self._is_done():
            if self._is_won():
                return 'WIN'
            
            else:
                return 'LOSE'
        
        else:
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
            if not moved_token:
                if not tokens[token]["in_play"]:
                    if roll != 6:
                        check_list.append(True)
                        continue
                    self.error: tuple = ("not_moved_to_board", token)
                    return False
                else:
                    if roll + current_position > n_fields:
                        check_list.append(True)
                        continue
                    self.error: tuple = ("not_moved", token)
                    return False
            else:

                if not tokens[token]["in_play"]:
                    if (
                        token == moved_token
                        and roll == 6
                        and move[token] == 1
                        and not self._is_taken(tokens, 1)
                    ):

                        check_list.append(True)
                        continue
                    elif token != moved_token:
                        check_list.append(True)
                        continue
                    else:
                        self.error: tuple = ("incorrect_move", token)
                        return False
                else:
                    if (
                        token == moved_token
                        and current_position + roll == move[token]
                        and not self._is_taken(tokens, move[token])
                    ):
                        check_list.append(True)
                        continue
                    elif token != moved_token:
                        check_list.append(True)
                    else:
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
    
    def _does_game_proceed(
            self,
            player: str,
            message: str,
            roll: int
    ) -> tuple[bool, str, dict]:
        """
        Checks if the game can proceed. If the player's move is valid, the
        game proceeds. If the move is not valid, the player is reprompted up
        to a maximum of three times. If the player still doesn't provide a
        valid move after three attempts, the game is aborted.

        Args:
            player (str): the name of the player whose move is being checked
            message (str): the message to be sent to the player
            roll (int): the roll of the dice for the current turn

        Returns:
            tuple: contains a boolean (True if the game can proceed and False
                   otherwise), a string (the response text from the player),
                   and a dictionary detailing the resulting move
        """
        while self.game.reprompt_attempts < 3:
            # Gets the player's response and logs it
            move, response_text = self._get_response(player, message)

            # Updates game attributes if move is valid
            if self._check_move(
                self.players_dic[player].tokens,
                move,
                roll,
                self.game.n_fields
            ):
                self.game.add_message(
                    response_text,
                    role="assistant"
                    if type(self.players_dic[player]) is LudoPlayer
                    else "user"
                )
                self.log_event(
                    from_=f"GM",
                    to="GM",
                    action={
                        'type': 'metadata',
                        'content': 'update board state'
                    }
                )

                self._update_player_dict(move, player)
                self.game.update_board(self.players_dic[player], move)
                self.game.reprompt_attempts = 0

                return True, response_text, move

            # Reprompt the player if not
            else:
                self.log_event(
                    from_=f"GM",
                    to="GM",
                    action={'type': f'error', 'content': self.error[0]}
                )
                self.game.reprompt(self.error[0], self.error[1])
                self.error = None
                message = self.game.context[-1]
                self.game.total_retry_count +=1

        return False, response_text, move
    
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
    
    def _get_response(self, player: str, message: str) -> tuple[dict, str]:
        """
        Gets the player's response and logs it. The response is then parsed
        into a move.

        Args:
            player (str): the name of the player producing the response
            message (str): the message to be sent to the player

        Returns:
            tuple: contains the parsed move and the response text
        """
        _, _, response_text = self.players_dic[player](
            self.game.context
            if type(self.players_dic[player]) is LudoPlayer
            else message,
            self.game.turn
        )
        self.log_event(
            from_=f"{player}",
            to="GM",
            action={'type': 'get message', 'content': response_text},
            call=(
                (self.game.context, response_text)
                if type(self.players_dic[player]) is LudoPlayer
                else None
            )
        )
        move: dict[str: int] = parse_text(response_text, self.players_dic[player])

        print()
        print(self.players_dic[player].tokens)
        print(message)
        print(response_text)
        print(move)

        self.log_event(
            from_="GM",
            to="GM",
            action={'type': 'parse', 'content': move}
        )

        return move, response_text

    def _is_done(self) -> bool:
        """
        Checks if the game has been completed.

        Returns:
            bool: True if the game is done, False otherwise
        """
        for player in self.players_dic.values():
            token_list: list[str] = (
                ['X', 'Y']
                if type(player) is LudoPlayer
                else ['A', 'B']
            )
            if (
                player.tokens[token_list[0]]['position'] == self.game.n_fields and
                player.tokens[token_list[1]]['position'] == self.game.n_fields
            ):
                return True

        return False
    
    def _is_taken(self, tokens: dict[str: dict], pos: int) -> bool:
        """
        Checks if the position is occupied by any token.

        Args:
            tokens (dict[str: dict]): the tokens to check
            pos (int): the position to check

        Returns:
            bool: True if the position is occupied, False otherwise
        """

        for token in tokens.keys():
            if tokens[token]["position"] == pos and pos != self.game.n_fields:
                return True

        return False

    def _is_won(self) -> bool:
        """
        Checks if player 1 has won the game.

        Returns:
            bool: True if player 1 has won the game, False otherwise
        """
        if (
            self.game.player_1.tokens['X']['position'] == self.game.n_fields and
            self.game.player_1.tokens['Y']['position'] == self.game.n_fields
        ):
            return True

        else:
            return False
    
    def _log_assets(self) -> None:
        """
        Logs the key game assets.
        """
        self.log_key('Board size', self.game.n_fields)
        self.log_key('Number of players', len(self.players_dic))
        self.log_key('Rolls', self.game.rolls)
        self.log_key('Played turns', self.game.turn)
        self.log_key('Turn limit', self.game.turn_limit)
        self.log_key('Reprompt attempts', self.game.total_retry_count)
        self.log_key('Final status', self._check_game_status())
    
    def _update_player_dict(self, move, player) -> None:
        """
        Updates the player's tokens' positions in the players dictionary based
        on the provided move.

        Args:
            move (dict): contains the desired position for all tokens
            player (str): the name of the player whose tokens' positions are
                          to be updated
        """
        for token in move.keys():
            self.players_dic[player].tokens[token]["in_play"] = move[token] > 0
            self.players_dic[player].tokens[token]["position"] = move[token]


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
