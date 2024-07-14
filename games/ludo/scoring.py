"""
Contains custom scoring logic for the game 'Ludo'.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from minimax import GameSim, minimax
from clemgame.clemgame import GameScorer
from clemgame.metrics import METRIC_ABORTED, METRIC_LOSE, METRIC_SUCCESS
from instancegenerator import find_monotoken_minimum, find_multitoken_minimum


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

    # TODO Determine final bench score calculation and logging destination
    def log_main_score(self, episode_interactions: dict) -> None:
        """
        TODO

        Args:
            episodic_interactions (dict): contains relevant information about
                                          played episode, including the per
                                          turn interactions
        """
        self._score_episode(episode_interactions)
        # TODO Calculate main score
        # TODO Log main score
    
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
        for idx, turn in enumerate(episode_interactions["turns"]):
            # Classifies events in the turn, gets moves and metric counts
            current_state, updated_state, counts = self._classify_events(turn)

            # Scores moves and counts
            scores: dict[str: int] = self._calculate_turn_scores(
                turn=idx,
                current_state=current_state,
                updated_state=updated_state,
                counts=counts,
                multiplayer=bool(episode_interactions["Multiplayer"])
            )

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
        max_retries: int = (counts["final_turn"] + 1) * ATTEMPT_LIMIT
        
        return {
            "speed": (
                0 if counts["status"] == "ABORTED"
                else self.game_instance["min_moves"] * 1.0 / (counts["final_turn"] + 1)
            ),
            "aborted": 1 if counts["status"] == "ABORTED" else 0,
            "success": 1 if counts["status"] == "SUCCESS" else 0,
            "lose": 1 if counts["status"] == "LOSE" else 0,
            "draw": 1 if counts["status"] == "DRAW" else 0,
            "efficiency": counts["total_accepted_moves"] / counts["total_requests"],
            "reprompt_efficiency": 1 - counts["retries"] / max_retries,
            "accuracy": counts["total_accuracy"] / (counts["final_turn"] + 1),
            "parsing_error_share": (
                counts["total_parsing_errors"] / counts["total_errors"]
                if counts["total_errors"] > 0 else 0
            ),
            "errors_per_accepted": (
                counts["total_accepted_moves"] / counts["total_errors"]
                if counts["total_errors"] > 0 else 0
            )
        }
    
    # TODO Determine main score calculation
    def _calculate_main_score(self) -> float:
        """
        TODO
        """
        ...
    
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
        
        # Calculates count-based metrics
        efficiency: float = counts["accepted_moves"] / counts["requests"]
        reprompt_efficiency: float = 1 - (counts["reprompts"] / ATTEMPT_LIMIT)
        violated_requests: int = counts["requests"] - counts["accepted_moves"]
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
    
    def _classify_events(self, turn: list[dict]) -> tuple[dict, dict, dict]:
        """
        Given a list of the events which took place during a given turn,
        classifies the events, gleaning from them the beginning and end
        positions of the tokens, as well as various turn-level metric counts.

        Args:
            turn (list[dict]): contains one dict per event which took place in
                               the turn

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
                    updated_state = event["action"]["content"]
                    counts["accepted_moves"] += 1
                case "current state":
                    current_state = event["action"]["content"]
                case 'error':
                    counts["errors"] += 1
                case 'get message':
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
        score_names: list[str] = [
            "Episode Speed",
            METRIC_ABORTED,
            METRIC_SUCCESS,
            METRIC_LOSE,
            "Draw",
            "Episode Efficiency",
            "Episode Reprompt Efficiency",
            "Episode Accuracy",
            "Episode Parsing Error Share",
            "Episode Errors per Accepted Move"
        ]

        for score_name, score_value in zip(score_names, scores.values()):
            self.log_episode_score(score_name, score_value)
    
    def _log_turn_scores(self, turn: int, scores: dict[str: int]) -> None:
        """
        Given the turn number and the calculates scores of the interactions
        during that turn, logs the scores and stores them in an instance
        attribute.

        Args:
            scores (dict[str: int]): contains numerous turn-level scores
        """
        score_names: list[str] = [
            "Turn Accuracy",
            "Turn Efficiency",
            "Turn Reprompt Efficiency",
            "Turn Violated Requests",
            "Turn Parsing Error Share",
            "Turn Accepted Moves",
            "Turn Requests",
            "Turn Errors",
            "Turn Parsing Errors",
            "Turn Reprompts"
        ]

        for score_name, score_value in zip(score_names, scores.values()):
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
        for turn in self.scores["turn scores"].values():
            total_accepted_moves += turn["Turn Accepted Moves"]
            total_requests += turn["Turn Requests"]
            total_accuracy += turn["Turn Accuracy"]
            total_parsing_errors += turn["Turn Parsing Errors"]
            total_errors += turn["Turn Errors"]

        return {
            "status": episode_interactions["Final status"],
            "final_turn": episode_interactions['Turns played'],
            "retries": episode_interactions['Reprompt attempts'],
            "total_accepted_moves": total_accepted_moves,
            "total_requests": total_requests,
            "total_accuracy": total_accuracy,
            "total_parsing_errors": total_parsing_errors,
            "total_errors": total_errors
        }

    def _score_episode(self, episode_interactions: dict) -> None:
        """
        Given episode interactions and previously calculated turn-level
        scores, calculates numerous episode-level scores, then logs the scores
        and stores them in an instance attribute.

        Args:
            episodic_interactions (dict): contains relevant information about
                                          played episode, including the per
                                          turn interactions
        """
        counts: dict = self._get_episode_counts(episode_interactions)
        scores: dict = self._calculate_episode_scores(counts)
        self._log_episode_scores(scores)

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
        tokens: set[str] = current_state.keys()

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
    pass
