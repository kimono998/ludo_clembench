"""
Contains custom scoring logic for the game 'Ludo'.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from minimax import GameSim, minimax
from clemgame.clemgame import GameScorer
from clemgame.metrics import METRIC_ABORTED, METRIC_LOSE, METRIC_SUCCESS
from instancegenerator import find_multitoken_minimum


GAME_NAME: str = "ludo"
ATTEMPT_LIMIT: int = 3

# TODO Adapt rest of the metrics
METRIC_DRAW: str = "Draw"
METRIC_EPISODE_ACCURACY: str = "Episode Accuracy"
METRIC_EPISODE_EFFICIENCY: str = "Episode Efficiency"
METRIC_EPISODE_SPEED: str = "Episode Speed"
METRIC_TURN_ACCURACY: str = "Turn Accuracy"
METRIC_TURN_EFFICIENCY: str = "Turn Efficiency"
METRIC_TURN_SPEED: str = "Turn Speed"


class LudoGameScorer(GameScorer):
    """
    Handles the scoring of the game 'Ludo' on a per-turn, episodic, and
    overall basis.
    """
    def __init__(self, experiment: dict, game_instance: dict):
        """
        Passes on arguments to the parent class for use in pre-built methods.

        Args:
            experiment (dict[str: list[dict]]): contains relevant information
                                                concerning a collection of
                                                related game instances
            game_instance (dict): contains relevant information about an
                                  individual game instance
        """
        super().__init__(GAME_NAME, experiment, game_instance)
        self.min_moves = game_instance['min_moves']

    def compute_scores(self, episode_interactions: dict) -> None:
        """
        Computes turn and episodic scores, then logs them.

        Args:
            episodic_interactions (dict): contains relevant information about
                                          played episode, including the per
                                          turn interactions
        """
        # first add the speed metric
        final_turn: int = episode_interactions['Turns played']
        max_retries: int = (final_turn + 1) * ATTEMPT_LIMIT
        retries: int = episode_interactions['Reprompt attempts']
        status: str = episode_interactions["Final status"]
        is_multiplayer: int = episode_interactions["Multiplayer"]

        error_episode_sum: int = 0
        move_accuracy_sum: int = 0
        episode_parsing_errors: int = 0
        accepted_move_sum: int = 0
        total_request_count: int = 0
        total_accepted_move_count: int = 0

        for idx, turn in enumerate(episode_interactions['turns']):
            turn_reprompts: int = 0
            turn_parsing_errors: int = 0
            error_turn_sum: int = 0
            turn_request_count: int = 0
            turn_accepted_move_count: int = 0
            
            for event in turn:
                action: dict = event['action']
                if action['type'] == "current state":
                    current_state: dict[str: int] = action["content"]
                if action['type'] == "accepted move":
                    updated_state: dict[str: int] = action["content"]
                    accepted_move_sum += 1
                if action['type'] == 'reprompt':
                    turn_reprompts += 1
                if action['type'] == 'parsing failed':
                    turn_parsing_errors += 1
                    episode_parsing_errors += 1
                if action['type'] == 'error':
                    error_turn_sum += 1
                    error_episode_sum += 1
                if action['type'] == 'get message':
                    turn_request_count += 1
                if action['type'] == 'accepted move':
                    turn_accepted_move_count += 1

            total_request_count += turn_request_count
            total_accepted_move_count += turn_accepted_move_count

            if is_multiplayer:
                score: float = self._score_multiplayer_move(episode_interactions, idx, current_state, updated_state)
            else:
                score: float = self._score_single_player_move(episode_interactions, current_state, idx, updated_state)

            move_accuracy_sum += score
            
            # Logs move accuracy
            self.log_turn_score(idx, 'Turn Accuracy', score)
            self.log_turn_score(idx, 'Turn Efficiency', (turn_accepted_move_count/turn_request_count))
            self.log_turn_score(idx, 'Reprompt Efficiency', 1 - (turn_reprompts / ATTEMPT_LIMIT))
            self.log_turn_score(idx, 'Violated Request Count', turn_request_count-turn_accepted_move_count)
            turn_parsing_err_rate = (turn_parsing_errors/error_turn_sum) if error_turn_sum > 0 else 0
            self.log_turn_score(idx, 'Parsing Error Share', turn_parsing_err_rate)
            self.log_turn_score(idx, 'Successful Request Count', turn_accepted_move_count)
            self.log_turn_score(idx, 'Total Request Count', turn_request_count)
            self.log_turn_score(idx, 'Error Count', error_turn_sum)
            self.log_turn_score(idx, 'Parsing Error Count', turn_parsing_errors)
            self.log_turn_score(idx, 'Reprompt Attempts Made', turn_reprompts)

        # Logs speed
        if episode_interactions['Aborted']:
            self.log_episode_score('Speed', 0)
        else:
            self.log_episode_score('Speed', (self.min_moves*1.0/(final_turn+1)))

        # Logs game status
        self.log_episode_score(METRIC_ABORTED, 1 if status == "ABORTED" else 0)
        self.log_episode_score(METRIC_SUCCESS, 1 if status == "WIN" else 0)
        self.log_episode_score(METRIC_LOSE, 1 if status == "LOSE" else 0)
        self.log_episode_score("Turn limit reached", 1 if status == "DRAW" else 0)

        # Percentage of maximum possible reprompting attempts - we can use that score in the final calculation.
        self.log_episode_score(METRIC_EPISODE_EFFICIENCY, total_accepted_move_count / total_request_count)
        self.log_episode_score("Episode Reprompt Efficiency", 1 - retries / max_retries)

        # Calculate the accuracy on episode level.
        self.log_episode_score("Move Accuracy", move_accuracy_sum / (final_turn + 1))

        # Parsing error share on episode level
        episode_parsing_err_share = episode_parsing_errors / error_episode_sum if error_episode_sum > 0 else 0
        self.log_episode_score('Episode Parsing Error Share', episode_parsing_err_share)

        # Error to accepted move ratio
        err_per_acc_move = (accepted_move_sum / error_episode_sum) if error_episode_sum > 0 else 0
        self.log_episode_score('Errors Per Accepted Move', err_per_acc_move)

    # TODO Adapt to single token using n_tokens
    def _score_single_player_move(
            self,
            episode_interactions: dict,
            turn: int,
            current_state: dict[str: int],
            updated_state: dict[str: int]
    ) -> None:
        """
        Scores the move made during a turn in a single player game by first
        calculating the best move in the given game state, then comparing the
        player's move against it and scoring accordingly.

        Args:
            episodic_interactions (dict): contains relevant information about
                                          played episode, including the per
                                          turn interactions
            turn (int): the turn number
            current_state (dict[str: int]): for the board at the beginning of
                                            the turn, contains the position of
                                            each token
            updated_state (dict[str: int]): for the board at the end of the
                                            turn, contains the position of
                                            each token

        Returns:
            float: the score of the move, '1.0' if it matches the best move or
                   '0.0' if not
        """
        memorized_moves: dict = {}
        tokens: set[str] = current_state.keys()
        _, moves = find_multitoken_minimum(
            rolls=episode_interactions["Rolls"],
            n_fields=episode_interactions["Board size"],
            memorized_moves=memorized_moves,
            X=current_state[tokens[0]],
            Y=current_state[tokens[1]],
            index=turn
        )

        simulated_move: tuple[str, int] = moves[0]
        selected_move: dict[str: int] = current_state.copy()
        selected_move[simulated_move[0]] = simulated_move[1]

        return self._check_equivalence(updated_state, selected_move)

    # TODO Adapt to single token using n_tokens
    def _score_multiplayer_move(
            self,
            episode_interactions: dict,
            turn: int,
            current_state: dict[str: int],
            updated_state: dict[str: int]
    ) -> float:
        """
        Scores the move made during a turn in a multiplayer game by first
        calculating the best move in the given game state, then comparing the
        player's move against it and scoring accordingly.

        Args:
            episodic_interactions (dict): contains relevant information about
                                          played episode, including the per
                                          turn interactions
            turn (int): the turn number
            current_state (dict[str: int]): for the board at the beginning of
                                            the turn, contains the position of
                                            each token
            updated_state (dict[str: int]): for the board at the end of the
                                            turn, contains the position of
                                            each token

        Returns:
            float: the score of the move, '1.0' if it matches the best move or
                   '0.0' if not
        """
        # Simulates the game each turn to get the best move
        game: GameSim = GameSim(
            n_fields=episode_interactions['Board size'],
            n_tokens=episode_interactions["n_tokens"], # TODO incorporate into logging
            token_positions=current_state,
            rolls=episode_interactions["Rolls"],
            turn=turn
        )
        _, simulated_move = minimax(game, False)  

        # Simulates the move
        selected_move = current_state.copy()
        selected_move[simulated_move[0]] = simulated_move[1]
        print(simulated_move)

        return self._check_equivalence(updated_state, selected_move)

    def _check_equivalence(
            self,
            updated_state: dict[str: int],
            selected_move: dict[str: int]
    ) -> float:
        """
        Checks for equivalence between the updated state and selected move.

        Args:
            updated_state (dict[str: int]): contains the positions of the
                                            player's token(s), representing
                                            the state of the board at the end
                                            of the turn
            selected_move (dict[str: int]): contains the positions of the
                                            player's token(s), representing
                                            the state of the board had the
                                            optimal move been made

        Returns:
            float: a float version of the boolean representation of
                   equivalence, that is '1.0' for True and '0.0' for False
        """
        matches: list[bool] = [
            value == selected_move[token]
            for token, value in updated_state.items()
        ]

        return float(all(matches))

    def score_turns(self, episodic_interactions: dict) -> None:
        """
        Given the the episodic scores, logs the final game status, speed,
        efficiency, and accuracy metrics.

        Args:
            status (str): the final status of the game
            speed (float): the speed at which the game was completed,
                           calculated by dividing the minimum number of moves
                           required by the number of moves made
            efficiency (float): the efficiency with which the game was played,
                                calculated by dividing the number of reprompt
                                attempts needed by the total possible number
            accuracy (float): the accuracy with which the game was played,
                              calculated by taking the average of the turn
                              scores
        """
        # E.g., score LLM performance against optimal decision at each turn,
        # given the information available at that turn. Then, add this
        # information to self.scores in the form of turn_number: turn_score
        for turn in episodic_interactions.values():
            pass

    # TODO Determine final bench score calculation and logging destination
    def log_main_score(self, episodic_interactions: dict) -> None:
        """
        Categorizes the events which took place in a turn, ultimately
        calculating the turn score and the number of reprompts which took
        place during the turn.

        Args:
            turn_number (int): the current turn number
            interaction (list[dict[str: str]]): contains dictionaries, which
                                                each represent an event which
                                                took place during the turn
            n_fields (int): the size of the board in terms of fields
            rolls (list[tuple]): contains the die rolls for the game

        Returns:
            tuple[float, int]: contains the turn score, calculated by
                               comparing the move made to the optimal move,
                               and the number or reprompt attempts made during
                               the turn
        """
        # Replace this function call with a function that logs your main score
        # aka BENCH_SCORE
        pass

if __name__ == '__main__':
    pass
