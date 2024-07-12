"""
Contains custom scoring logic for the game 'Ludo'.
"""

import sys
from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent.parent))

from minimax import GameSim, minimax
from clemgame.clemgame import GameScorer
from clemgame.metrics import *
from instancegenerator import find_multitoken_minimum

GAME_NAME: str = "ludo"
ATTEMPT_LIMIT: int = 3


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
        self.min_moves = experiment['min_moves']

    def compute_scores(self, episode_interactions: dict) -> None:
        # first add the speed metric

        final_turn = episode_interactions['Turns played']
        max_retries = (final_turn+1)*ATTEMPT_LIMIT
        retries = episode_interactions['Reprompt attempts']
        status = episode_interactions["Final status"]
        is_multiplayer = episode_interactions["Multiplayer"]

        error_episode_sum = 0
        move_accuracy_sum = 0
        episode_parsing_errors = 0
        accepted_move_sum = 0

        for idx, turn in enumerate(episode_interactions['turns']):
            turn_reprompts = 0
            turn_parsing_errors = 0
            error_turn_sum = 0
            for event in turn:
                action = event['action']
                if action['type'] == "current state": # current state
                    current_state = action["content"]
                if action['type'] == "accepted move": # made move
                    updated_state = action["content"]
                    accepted_move_sum += 1
                if action['type'] == 'reprompt':
                    turn_reprompts += 1
                if action['type'] == 'parsing failed':
                    turn_parsing_errors += 1
                    episode_parsing_errors += 1
                if action['type'] == 'error':
                    error_turn_sum += 1
                    error_episode_sum += 1

            if is_multiplayer == 1:
                score = self._mp_move_score(episode_interactions, current_state, idx, updated_state)
            else:
                score = self._sp_move_score(episode_interactions, current_state, idx, updated_state)

            move_accuracy_sum += score
            # log move accuracy
            self.log_turn_score(idx, 'Turn Accuracy', score)
            self.log_turn_score('Turn Efficiency', 1-(turn_reprompts/ATTEMPT_LIMIT)) # efficiency in terms of reprompting attempts.

            turn_parsing_err_rate = (turn_parsing_errors/error_turn_sum)*100 if error_turn_sum > 0 else 0
            self.log_turn_score('Parsing Error Share', turn_parsing_err_rate)


        # log speed
        if episode_interactions['Aborted']:
            self.log_episode_score('Speed', 0)
        else:
            self.log_episode_score('Speed', (self.min_moves*1.0/(final_turn+1)) * 100)

        # log game status
        self.log_episode_score(METRIC_ABORTED, 1 if status == "ABORTED" else 0)
        self.log_episode_score(METRIC_SUCCESS, 1 if status == "WIN" else 0)
        self.log_episode_score(METRIC_LOSE, 1 if status == "LOSE" else 0)
        self.log_episode_score("Turn limit reached", 1 if status == "DRAW" else 0)

        # percentage of maximum possible reprompting attempts - we can use that score in the final calculation.
        self.log_episode_score("Episode Efficiency", 1-(retries/max_retries))

        # calculate the accuracy on episode level.
        self.log_episode_score("Move Accuracy", (move_accuracy_sum / (final_turn + 1)) * 100)

        # parsing error share on episode level
        episode_parsing_err_share = (episode_parsing_errors / error_episode_sum) * 100 if error_episode_sum > 0 else 0
        self.log_episode_score('Episode Parsing Error Share', episode_parsing_err_share)

        # error to accepted move ratio
        err_per_acc_move = (accepted_move_sum / error_episode_sum) * 100 if error_episode_sum > 0 else 0
        self.log_episode_score('Errors Per Accepted Move', err_per_acc_move)

    # single player and multi player move scoring functions. SP calls the DP Script from instance gen
    # MP uses AlphaBeta prunning
    def _sp_move_score(self, episode_interactions, current_state: dict, idx: int, updated_state: dict):
        memorized_moves = {}
        tokens = current_state.keys()
        _, moves = find_multitoken_minimum(
            rolls=episode_interactions["Rolls"],
            n_fields=episode_interactions["Board size"],
            memorized_moves=memorized_moves,
            X=current_state[tokens[0]],
            Y=current_state[tokens[1]],
            index=idx
        )

        simulated_move = moves[0]
        selected_move = current_state.copy()
        selected_move[simulated_move[0]] = simulated_move[1]
        return self._check_equivalence(updated_state, selected_move)

    def _mp_move_score(self, episode_interactions, current_state, idx, updated_state):

        game: GameSim = GameSim(
            episode_interactions['Board size'],
            current_state,
            episode_interactions["Rolls"],
            idx)
        _, simulated_move = minimax(game, False)  # simulate the game on each turn to get best move

        # simulate the move
        selected_move = current_state.copy()
        selected_move[simulated_move[0]] = simulated_move[1]
        print(simulated_move)
        return self._check_equivalence(updated_state, selected_move)


    def _check_equivalence(self, updated_state, selected_move):
        # check for equivalence
        matches = []
        for token in updated_state.keys():
            if updated_state[token] == selected_move[token]:
                matches.append(True)
            else:
                matches.append(False)

        score = 1.00 if all(matches) else 0
        return score

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
        pass

if __name__ == '__main__':

    pass