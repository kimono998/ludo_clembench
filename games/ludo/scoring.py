"""
Contains custom scoring logic for the game 'Ludo'.
"""

import sys
from pathlib import Path
from typing import Dict
from minimax import GameSim, minimax
from clemgame.metrics import *
sys.path.append(str(Path(__file__).parent.parent.parent))

from clemgame.clemgame import GameScorer

ATTEMPT_LIMIT = 3
GAME_NAME: str = "ludo"


class LudoGameScorer(GameScorer):
    """
    Handles the scoring of the game 'Ludo' on a per-turn, episodic, and overall
    basis.
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

    # TODO Determine turn scoring procedure

    def compute_scores(self, episode_interactions: Dict) -> None:
        # first add the speed metric

        final_turn = episode_interactions['Turns played']
        max_retries = (final_turn+1)*ATTEMPT_LIMIT
        retries = episode_interactions['Reprompt attempts']
        status = episode_interactions["Final status"]

        # log game status
        self.log_episode_score(METRIC_ABORTED, 1 if status == "ABORTED" else 0)
        self.log_episode_score(METRIC_SUCCESS, 1 if status == "WIN" else 0)
        self.log_episode_score(METRIC_LOSE, 1 if status == "LOSE" else 0)
        self.log_episode_score("Turn limit reached", 1 if status == "DRAW" else 0)

        # log speed
        if episode_interactions['Aborted']:
            self.log_episode_score('Speed', 0)

        else:
            self.log_episode_score('Speed', (self.min_moves*1.0/(final_turn+1)) * 100)



        # percentage of maximum possible reprompting attempts - we can use that score in the final calculation.
        # maybe we can call it sth like turn and episode efficiency

        self.log_episode_score("Episode Efficiency", 1-(retries/max_retries))


        move_accuracy_sum = 0
        # per turn move accuracy -> currently only will work for Multiplayer games. TODO adapt for singleplayer as well; use DP.
        for idx, turn in enumerate(episode_interactions['turns']):
            turn_reprompts = 0
            for event in turn:
                action = event['action']
                if action['type'] == "current state": # current state
                    # temp = action["content"]
                    current_state = {token: value['position'] for token, value in action["content"].items()}
                if action['type'] == "accepted move": # made move
                    updated_state = action["content"]
                if action['type'] == 'reprompt':
                    turn_reprompts += 1


            game: GameSim = GameSim(
                episode_interactions['Board size'],
                current_state,
                episode_interactions["Rolls"],
                idx)
            _, simulated_move = minimax(game, False) # simulate the game on each turn to get best move

            # simulate the move
            selected_move = current_state.copy()
            selected_move[simulated_move[0]]["position"] = simulated_move[1]
            print(simulated_move)

                # check for equivalence
            matches = []
            for token in updated_state.keys():
                if updated_state[token] == selected_move[token]:
                    matches.append(True)
                else:
                    matches.append(False)

            score = 1.00 if all(matches) else 0
            move_accuracy_sum += score
            # log move accuracy
            self.log_turn_score(idx, 'Turn Accuracy', score)
            self.log_turn_score('Turn Efficiency', 1-(turn_reprompts/ATTEMPT_LIMIT)) # efficiency in terms of reprompting attempts.
        # calculate the accuracy on episode level.
        self.log_episode_score("Move Accuracy", (move_accuracy_sum/(final_turn+1))*100)






        # +1 if match else 0

        # look at accepted move in the interactions json
        # if the accepted move is the same as the best move (based on the current state + roll)
        # flag as 1
        # else, flag as 0
        # score is % achieved out of max
        pass

        # reprompting -> sum max reprompting attempts possible
        #










        pass


    def score_turns(self, episodic_interactions: dict) -> None:
        """
        TODO Method description

        Args:
            TODO episodic_interactions (dict):
        """
        # E.g., score LLM performance against optimal decision at each turn,
        # given the information available at that turn. Then, add this
        # information to self.scores in the form of turn_number: turn_score
        for turn in episodic_interactions.values():
            pass

    # TODO Determine final bench score calculation and logging destination
    def log_main_score(self, episodic_interactions: dict) -> None:
        """
        TODO Method description

        Args:
            TODO episodic_interactions (dict):
        """
        # Replace this function call with a function that logs your main score
        # aka BENCH_SCORE
        pass


if __name__ == '__main__':
    pass
    