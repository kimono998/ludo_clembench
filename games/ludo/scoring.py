"""
Contains custom scoring logic for the game 'Ludo'.
"""

import sys
import numpy as np
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from games.ludo.minimax import GameSim, minimax
from clemgame.clemgame import GameScorer
from clemgame.metrics import METRIC_REQUEST_COUNT, \
    METRIC_REQUEST_COUNT_PARSED, METRIC_REQUEST_COUNT_VIOLATED, \
        METRIC_REQUEST_SUCCESS, BENCH_SCORE, METRIC_PLAYED
from games.ludo.instancegenerator import find_monotoken_minimum, find_multitoken_minimum


GAME_NAME: str = "ludo"
ATTEMPT_LIMIT: int = 3
BOARD_SIZE = 23
EPISODE_SCORE_NAMES: dict[str: str] = {
    "speed": "Episode Speed",
    "draw": "Draw",
    "efficiency": "Episode Efficiency",
    "reprompt_efficiency": "Episode Reprompt Efficiency",
    "accuracy": "Episode Accuracy",
    "parsing_error_share": "Episode Parsing Error Share",
    "accepted_per_error": "Episode Accepted Moves per Error",
    "completion_score": "Percentage Completed"
}
TURN_SCORE_NAMES: dict[str: str] = {
    "accuracy": "Accuracy",
    "efficiency": "Efficiency",
    "reprompt_efficiency": "Reprompt Efficiency",
    "violated_requests": METRIC_REQUEST_COUNT_VIOLATED,
    "parsing_error_share": "Parsing Error Share",
    "accepted": "Accepted Moves",
    "requests": METRIC_REQUEST_COUNT,
    "errors": "Errors",
    "parsing_errors": "Parsing Errors",
    "reprompts": "Remprompts"
}


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
        self.turn_scores = {}
    def log_main_score(self, episode_interactions: dict) -> None:
        """
        TODO

        Args:
            episodic_interactions (dict): contains relevant information about
                                          played episode, including the per
                                          turn interactions
        """



        speed, accuracy, efficiency, completion_score = self._score_episode(episode_interactions)

        main_score: float = self._calculate_main_score(speed, accuracy, efficiency)

        # we want to give a better score to models that are closer to completion.
        if episode_interactions["Final status"] == "ABORTED":
            main_score = main_score*completion_score

        if BENCH_SCORE in self.scores["episode scores"]:
            self.logger.warning(f"{self.name}: Main score overwritten!")

        self.scores["episode scores"][BENCH_SCORE] = main_score*100
        self.logger.info(f"{self.name}: Logged episode score {BENCH_SCORE}={main_score}.")
    
    def score_turns(self, episode_interactions: dict) -> None:
        """
        For each turn in the episode, gleans from the events beginning and end
        board state information, as well as relevant metric counts. This
        information is then used to calculate a number of turn metrics,which
        are then logged.

        Args:
            episodic_interactions (dict): contains relevant information about
                                          played episode, including the per
                                          turn interactions
        """
        tokens: dict = {item: True for item in episode_interactions["LLM Tokens"]}

        for idx, turn in enumerate(episode_interactions["turns"]):
            # Classifies events in the turn, gets moves and metric counts
            current_state, updated_state, counts = self._classify_events(turn, tokens)

            # Scores moves and counts
            scores: dict[str: int] = self._calculate_turn_scores(
                turn=idx,
                current_state=current_state,
                updated_state=updated_state,
                counts=counts,
                multiplayer=bool(episode_interactions["Multiplayer"])
            )
            self.turn_scores[idx] = scores
            # Logs and stores scores
            self._log_turn_scores(idx, scores)
    
    def _calculate_episode_scores(self, counts: dict) -> dict[str: int]:
        """
        Given relevant episode-level metric counts, calculates numerous
        episode-level scores.

        Args:
            counts (dict): contains various episode-level metric counts used
                           in the calculation of episode scores

        Returns:
            dict[str: int]: contains numerous episode-level scores
        """
        counter = 0
        reprompt_sum = 0
        for idx, turn in self.turn_scores.items():
            counter += 1 if turn['reprompt_efficiency'] != None else 0
            reprompt_sum += turn['reprompt_efficiency'] if turn['reprompt_efficiency'] != None else 0

        reprompt_efficiency = reprompt_sum/counter if counter > 0 else None

        # Speed needs to be capped at 1.
        # if not Aborted, we have to consider how much of the game was completed
        # so speed = speed * completion score

        speed = (((self.game_instance["min_moves"]*1.0) / (counts["final_turn"] + 1))*counts['completion_score'])\
            if counts["status"] != "ABORTED" else 0

        return {
            "speed": 1 if speed > 1 else speed,
            "draw": 1 if counts["status"] == "DRAW" else 0,
            "efficiency": counts["total_accepted_moves"] / counts["total_requests"],
            "reprompt_efficiency": reprompt_efficiency,
            "accuracy": counts["total_accuracy"] / (counts["final_turn"] + 1),
            "parsing_error_share": (
                counts["total_parsing_errors"] / counts["total_errors"]
                if counts["total_errors"] > 0 else 0
            ),
            "accepted_per_error": (
                counts["total_accepted_moves"] / counts["total_errors"]
                if counts["total_errors"] > 0 else 0
            ),
            "completion_score": counts['completion_score']
        }

    def _calculate_main_score(
            self,
            speed: float,
            accuracy: float,
            efficiency: float
    ) -> float:
        """
        TODO

        Args:
            TODO speed (float):
            TODO accuracy (float):
            TODO efficiency (float):

        Returns:
            TODO float:
        """
        main_score = ((speed + accuracy) / 2) * efficiency

        return 1 if main_score > 1 else main_score
    
    def _calculate_turn_scores(
            self,
            turn: int,
            current_state: dict[str: int],
            updated_state: dict[str: int],
            counts: dict[str: int],
            multiplayer: bool
    ) -> dict[str: int]:
        """
        Given turn-level metrics, calculates numerous turn-level scores.

        Args:
            turn (int): the turn number
            current_state (dict[str: int]): for the board at the beginning of
                                            the turn, contains the position of
                                            each token
            updated_state (dict[str: int]): for the board at the end of the
                                            turn, contains the position of
                                            each token
            counts (dict[str: int]): various turn-level metric counts
            multiplayer (bool): True if the episode was multiplayer, False
                                otherwise

        Returns:
            dict[str: int]: contains numerous turn-level scores
        """
        if updated_state:
            # Calculates move accuracy
            if multiplayer:
                accuracy: float = self._score_multiplayer_move(
                    turn=turn,
                    current_state=current_state,
                    updated_state=updated_state
                )
            else:
                accuracy: float = self._score_single_player_move(
                    turn=turn,
                    current_state=current_state,
                    updated_state=updated_state
                )
        else:
            accuracy: float = 0
        
        # Calculates count-based metrics
        efficiency: float = counts["accepted_moves"] / counts["requests"]
        reprompt_efficiency: float = counts["accepted_moves"] / counts["reprompts"] if counts['reprompts'] > 0 else None
        # violated_requests: int = counts["requests"] - counts["accepted_moves"]
        violated_requests: int = counts["parsing_errors"] # violated requests is the number of requests that could not be parsed
        parsing_error_share: int = (
            counts["parsing_errors"] / counts["errors"]
            if counts["errors"] > 0 else 0
        )

        return {
            "accuracy": accuracy,
            "efficiency": efficiency,
            "reprompt_efficiency": reprompt_efficiency,
            "violated_requests": violated_requests,
            "parsing_error_share": parsing_error_share,
            "accepted_moves": counts["accepted_moves"],
            "requests": counts["requests"],
            "errors": counts["errors"],
            "parsing_errors": counts["parsing_errors"],
            "reprompts": counts["reprompts"]
        }

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
    
    def _classify_events(
            self,
            turn: list[dict],
            tokens: dict
    ) -> tuple[dict, dict, dict]:
        """
        Given a list of the events which took place during a given turn,
        classifies the events, gleaning from them the beginning and end
        positions of the tokens, as well as various turn-level metric counts.

        Args:
            turn (list[dict]): contains one dict per event which took place in
                               the turn
            TODO tokens (dict):

        Returns:
            tuple[dict, dict, dict]: contains three dictionaries, one
                                     representing the token positions at the
                                     beginning of the turn, one representing
                                     the token positions at the end of then
                                     turn, and the third containing various
                                     turn-level metric counts 
        """
        counts: dict[str: int] = {
            "accepted_moves": 0,
            "errors": 0,
            "parsing_errors": 0,
            "reprompts": 0,
            "requests": 0
        }
        current_state: dict[str: int] | None = None
        updated_state: dict[str: int] | None = None

        for event in turn:
            match event["action"]["type"]:
                case "accepted move":
                    keys: list[str] = list(event["action"]["content"].keys())
                    req: list[bool] = [tokens.get(item, False) for item in keys]
                    if np.all(req):
                        updated_state = event["action"]["content"]
                        counts["accepted_moves"] += 1
                case "current state":
                    current_state = event["action"]["content"]
                case 'error':
                    counts["errors"] += 1
                case 'get message':
                    if event['from'] == 'Player 1':
                        counts["requests"] += 1
                case 'parsing failed':
                    counts["parsing_errors"] += 1
                case 'reprompt':
                    counts["reprompts"] += 1


        return current_state, updated_state, counts

    def _log_episode_scores(self, scores: dict[str: int]) -> None:
        """
        Given episode-level scores, logs them and stores them in an instance
        attribute.

        Args:
            scores (dict[str: int]): contains numerous episode-level scores
        """
        for score_name, score_value in zip(EPISODE_SCORE_NAMES.values(), scores.values()):
            print(f"{score_name} : {score_value}")
            self.log_episode_score(score_name, score_value)
    
    def _log_turn_scores(self, turn: int, scores: dict[str: int]) -> None:
        """
        Given the turn number and the calculates scores of the interactions
        during that turn, logs the scores and stores them in an instance
        attribute.

        Args:
            scores (dict[str: int]): contains numerous turn-level scores
        """
        for score_name, score_value in zip(TURN_SCORE_NAMES.values(), scores.values()):
            self.log_turn_score(turn, score_name, score_value)

    def _get_episode_counts(self, episode_interactions: dict) -> dict:
        """
        Given an episode interaction, gets various episode-level metric
        counts, some from the episode interactions and some by summing totals
        across turn scores.

        Args:
            episodic_interactions (dict): contains relevant information about
                                          played episode, including the per
                                          turn interactions
        """
        # Sums counts in all turns
        total_accepted_moves: int = 0
        total_requests: int = 0
        total_accuracy: int = 0
        total_parsing_errors: int = 0
        total_errors: int = 0
        counter = 0
        for turn in self.scores["turn scores"].values():
            counter += 1
            total_accepted_moves += turn["Accepted Moves"]
            total_requests += turn[METRIC_REQUEST_COUNT]
            total_errors += turn["Errors"]
            total_parsing_errors += turn['Parsing Errors']
            total_accuracy += turn['Accuracy']

        # Percentage of the game completed by the LLM
        final_state = episode_interactions['Final State']
        llm_tokens = episode_interactions['LLM Tokens']
        completion_score = 0
        for token in llm_tokens:
            completion_score += final_state[token]/BOARD_SIZE
        completion_score = completion_score/len(llm_tokens)

        return {
            "status": episode_interactions["Final status"],
            "final_turn": episode_interactions['Turns played'],
            "retries": episode_interactions['Reprompt attempts'],
            "total_accepted_moves": total_accepted_moves,
            "total_requests": total_requests,
            "total_accuracy": total_accuracy,
            "total_parsing_errors": total_parsing_errors,
            "total_errors": total_errors,
            "completion_score": completion_score
        }

    def _score_episode(self, episode_interactions: dict) -> tuple[float, float, float]:
        """
        Given episode interactions and previously calculated turn-level
        scores, calculates numerous episode-level scores, then logs the scores
        and stores them in an instance attribute.

        Args:
            episodic_interactions (dict): contains relevant information about
                                          played episode, including the per
                                          turn interactions

        Returns:
            TODO tuple[float, float, float]
        """
        # calculate how much of the board was completed



        counts: dict = self._get_episode_counts(episode_interactions)
        scores: dict = self._calculate_episode_scores(counts)
        self._log_episode_scores(scores)

        return (
            self.scores["episode scores"][EPISODE_SCORE_NAMES["speed"]],
            self.scores["episode scores"][EPISODE_SCORE_NAMES["accuracy"]],
            self.scores["episode scores"][EPISODE_SCORE_NAMES["efficiency"]],
            self.scores["episode scores"][EPISODE_SCORE_NAMES["completion_score"]]
        )

    def _score_multiplayer_move(
            self,
            turn: int,
            current_state: dict[str: int],
            updated_state: dict[str: int]
    ) -> float:
        """
        Scores the move made during a turn in a multiplayer game by first
        calculating the best move in the given game state, then comparing the
        player's move against it and scoring accordingly.

        Args:
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
            n_fields=self.game_instance["n_fields"],
            n_tokens=self.game_instance["n_tokens"],
            token_positions=current_state,
            rolls=self.game_instance["rolls"],
            turn=turn
        )
        _, simulated_move = minimax(game, False)  

        # Simulates the move
        selected_move = current_state.copy()
        selected_move[simulated_move[0]] = simulated_move[1]

        return self._check_equivalence(updated_state, selected_move)
    
    def _score_single_player_move(
            self,
            turn: int,
            current_state: dict[str: int],
            updated_state: dict[str: int]
    ) -> None:
        """
        Scores the move made during a turn in a single player game by first
        calculating the best move in the given game state, then comparing the
        player's move against it and scoring accordingly.

        Args:
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
        tokens: set[str] = list(current_state.keys())

        match self.game_instance["n_tokens"]:
            case 1:
                _, moves = find_monotoken_minimum(
                    rolls=self.game_instance["rolls"],
                    n_fields=self.game_instance["n_fields"],
                    memorized_moves=memorized_moves,
                    X=current_state[tokens[0]],
                    index=turn
                )
            case 2:
                _, moves = find_multitoken_minimum(
                    rolls=self.game_instance["rolls"],
                    n_fields=self.game_instance["n_fields"],
                    memorized_moves=memorized_moves,
                    X=current_state[tokens[0]],
                    Y=current_state[tokens[1]],
                    index=turn
                )

        simulated_move: tuple[str, int] = moves[0]
        selected_move: dict[str: int] = current_state.copy()
        selected_move[simulated_move[0]] = simulated_move[1]

        return self._check_equivalence(updated_state, selected_move)


if __name__ == '__main__':
    from clemgame import benchmark

    game_name: str = "ludo"
    model_specs: list[str] = ["gpt-3.5-turbo-1106", "programmatic"]
    gen_args: dict[str: str] = {"temperature": 0.0, "max_tokens": 400}
    instances_name: str = "instances"
    results_dir: str = "results"

    benchmark.score(game_name=game_name)
