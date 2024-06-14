"""
TODO Module description
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from clemgame.clemgame import GameScorer


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

    # TODO Determine turn scoring procedure
    def score_turns(self, episodic_interactions: dict) -> None:
        """
        TODO Method description

        Args:
            TODO episodic_interactions (dict):
        """
        # E.g., score LLM performance against optimal decision at each turn,
        # given the information available at that turn. Then, add this
        # information to self.scores in the form of turn_number: turn_score
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


def main() -> None:
    pass


if __name__ == '__main__':
    main()
    