"""
Contains custom scoring logic for the game 'Ludo'.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from minimax import GameSim, minimax
from clemgame.clemgame import GameScorer
from clemgame.metrics import METRIC_ABORTED, METRIC_SUCCESS, METRIC_LOSE


GAME_NAME: str = "ludo"
ATTEMPT_LIMIT: int = 3
METRIC_DRAW: str = "Draw"
METRIC_EPISODE_ACCURACY: str = "Episode Accuracy"
METRIC_EPISODE_EFFICIENCY: str = "Episode Efficiency"
METRIC_SPEED: str = "Speed"
METRIC_TURN_ACCURACY: str = "Turn Accuracy"
METRIC_TURN_EFFICIENCY: str = "Turn Efficiency"


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
        self.min_moves: int = experiment['min_moves']

    # TODO Adapt per turn move accuracy to single player
    def score_turns(self, episodic_interactions: dict) -> None:
        """
        TODO Method description

        Args:
            TODO episodic_interactions (dict):
        """
        for idx, turn in enumerate(episodic_interactions['turns']):
            score, turn_reprompts = LudoGameScorer._score_turn(
                turn_number=idx,
                interaction=turn,
                n_fields=episodic_interactions["Board size"], # TODO Correct
                rolls=episodic_interactions["Rolls"] # TODO Correct
            )

            # Logs the move accuracy
            self.log_turn_score(
                turn_idx=idx, 
                score_name=METRIC_TURN_ACCURACY,
                score_value=score
            )

            # Logs the turn efficiency in turns of reprompt attempts made
            self.log_turn_score(
                turn_idx=idx,
                score_name=METRIC_TURN_EFFICIENCY,
                score_value=1 - (turn_reprompts / ATTEMPT_LIMIT)
            )

    def log_main_score(self, episodic_interactions: dict) -> None:
        """
        Calculates and logs the final game status, the speed at which the
        episode was completed, the percentage of reprompts taken during the
        episode, and the average accuracy of the moves made during an episode.

        Args:
            episodic_interactions (dict): contains the information and
                                          interactions which pertain to a
                                          given episode
        """
        scores: tuple = self._calculate_episodic_scores(episodic_interactions)
        status, speed, efficiency, accuracy = scores
        self._log_episodic_scores(
            status=status,
            speed=speed,
            efficiency=efficiency,
            accuracy=accuracy
        )
        main_score: float = self._calculate_main_score(
            status=status,
            speed=speed,
            efficiency=efficiency,
            accuracy=accuracy
        )

        # # Logic from log_episode_score
        # if score_name in self.scores["episode scores"]:
        #     self.logger.warning(f"{self.name}: Episode score {score_name} overwritten!")
        # self.scores["episode scores"][score_name] = score_value
        # self.logger.info(f"{self.name}: Logged episode score {score_name}={score_value}.")

    def _calculate_episodic_scores(
            self,
            episodic_interactions: dict
    ) -> tuple[float, float, float]:
        """
        Given the episodic interactions, calculates the speed, efficiency, and
        accuracy metrics for the entire episode.

        Args:
            episodic_interactions (dict): contains the information and
                                          interactions which pertain to a
                                          given episode
        
        Returns:
            tuple[float, float, float]: contains the episodic speed,
                                        efficiency, and accuracy metrics
        """
        status: str | bool = episodic_interactions["Final status"]
        
        # Calculates the speed at which the game was completed
        final_turn: int = episodic_interactions['Turns played'] + 1
        speed: float = (self.min_moves / final_turn) * 100
        
        # Calculates the percentage of reprompt attempts necessary
        efficiency: float = (
            1 - episodic_interactions['Reprompt attempts'] /
            (final_turn * ATTEMPT_LIMIT)
        )
        
        # Sums the accuracy scores for each turn, then calculates the average
        move_accuracy_sum: float = sum(
            LudoGameScorer._score_turn(
                turn_number=idx,
                interaction=turn,
                n_fields=episodic_interactions["Board size"], # TODO Correct
                rolls=episodic_interactions["Rolls"] # TODO Correct
            )[0] for idx, turn in enumerate(episodic_interactions["turns"])
        )
        accuracy: float = (move_accuracy_sum / final_turn) * 100

        return status, speed, efficiency, accuracy
    
    # TODO Determine how to calculate the main score
    def _calculate_main_score(
            self,
            status: str,
            speed: float,
            efficiency: float,
            accuracy: float
    ) -> float:
        """
        Given the episodic scores, calculates the main score for the episode.

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

        Returns:
            TODO float:
        """
        pass

    def _log_episodic_scores(
            self,
            status: str,
            speed: float,
            efficiency: float,
            accuracy: float
    ) -> None:
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
        self.log_episode_score(METRIC_ABORTED, 1 if status == "ABORTED" else 0)
        self.log_episode_score(METRIC_SUCCESS, 1 if status == "WIN" else 0)
        self.log_episode_score(METRIC_LOSE, 1 if status == "LOSE" else 0)
        self.log_episode_score(METRIC_DRAW, 1 if status == "DRAW" else 0)
        self.log_episode_score(
            score_name=METRIC_SPEED,
            score_value=speed
        )
        self.log_episode_score(
            score_name=METRIC_EPISODE_EFFICIENCY,
            score_value=efficiency
        )
        self.log_episode_score(
            score_name=METRIC_EPISODE_ACCURACY,
            score_value=accuracy
        )

    @staticmethod
    def _score_turn(
            turn_number: int,
            interaction: list[dict[str: str]],
            n_fields: int,
            rolls: list[tuple]) -> tuple[float, int]:
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
        turn_reprompts: int = 0
        for event in interaction:
            match event["action"]["type"]:
                case "current_state": # TODO Rename to something and leave 'current_state' to the board image?
                    current_state: dict = {
                            token: value['position']
                            for token, value
                            in event["action"]["content"].items()
                    }
                case "accepted move":
                    updated_state: str = event["action"]["content"]
                case "reprompt":
                    turn_reprompts += 1

        game: GameSim = GameSim(
            n_fields=n_fields,
            token_positions=current_state,
            rolls=rolls,
            turn=turn_number
        )
        
        # Simulates the game at the current turn to get the best move
        _, simulated_move = minimax(game, False) 

        # Simulates the move
        selected_move: dict = current_state.copy()
        selected_move[simulated_move[0]]["position"] = simulated_move[1]
        print(simulated_move)

        # Checks for equivalence between the optimal and chosen moves
        matches: list[bool] = [
            updated_state[token] == selected_move[token]
            for token in updated_state.keys()
        ]

        return 1.0 if all(matches) else 0.0, turn_reprompts


if __name__ == '__main__':
    pass
    