"""
Module focused on generating game instances for the game 'Ludo'.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.append(str(Path(__file__).parent.parent.parent))

from clemgame.clemgame import GameInstanceGenerator


GAME_NAME: str = "ludo"
RANDOM_SEED: int = 42

np.random.seed(RANDOM_SEED)


class LudoInstanceGenerator(GameInstanceGenerator):
    """
    A 'Ludo'-specific GameInstanceGenerator, intended to be used to generate
    experiments according to given configurations, then store them in
    instances.json for further use.
    """
    def __init__(self):
        """
        Passes along the game name to the parent class.
        """
        super().__init__(GAME_NAME)

    def on_generate(self, **kwargs) -> None:
        """
        Given a list of experiment configurations, generates the appropriate
        amount of instances for each experiment, attaches them, then creates
        the experiment.

        Args:
            experiments (list[dict]): contains a dictionary for each
                                      experiment, detailing the experiment
                                      name, the number of instances to be
                                      generated, the initial prompt, the size
                                      of the board, the number of rolls to be
                                      generated, and the intended dialogue
                                      partners for the experiment
        """
        experiments: list[dict] = kwargs.get("experiments")
        for experiment in experiments:
            self._generate_experiment(
                experiment["experiment_name"],
                experiment["n_instances"],
                experiment["dialogue_partners"],
                experiment["prompt_name"],
                experiment["n_fields"],
                experiment["n_rolls"],
            )

    def _check_sequence(self, n_fields: int, rolls: list[int]) -> bool:
        """
        Given the size of the board and a sequence of rolls, checks that the
        sequence of rolls will result in a game instance that is solvable.
        
        Args:
            n_fields (int): the size of the board
            rolls (list[int]): contains a sequence of die rolls
        
        Returns:
            bool: True if a move sequence is solvable, False otherwise
        """
        memorized_moves: dict = {}


        # Initiates the search for the minimum move count
        initial_X, initial_Y = 0, 0
        min_move_count, _ = self.find_minimum(initial_X, initial_Y,0, rolls, n_fields, memorized_moves)

        if min_move_count == float('inf'):
            return -1

        return min_move_count

    def find_minimum(self,
                     X: int,
                     Y: int,
                     roll_index: int,
                     rolls: list,
                     n_fields: int,
                     memorized_moves: dict
                     ) -> tuple[int, list[str]]:
        """
        Finds the minimum number of moves required to solve a sequence of
        die rolls, as well as the moves associated with that minimum.

        Args:
            X (int): position of the token 'X' in terms of the field
                     number it is currently occupying
            Y (int): position of the token 'Y' in terms of the field
                     number it is currently occupying
            roll_index (int): the index of the current roll being
                              considered

        Returns:
            tuple[int, list[str]]: contains the minimum number of moves
                                   required to solve the sequence and the
                                   associated move sequence

        """
        # For completed sequences
        if X == n_fields and Y == n_fields:
            return 0, []

        # For sequences that have surpassed the turn limit
        if roll_index >= len(rolls):
            return float('inf'), []

        # If the move has already been analyzed
        if (X, Y, roll_index) in memorized_moves:
            return memorized_moves[(X, Y, roll_index)]

        roll: int = rolls[roll_index]
        next_roll_index: int = roll_index + 1
        min_move_count = float('inf')
        best_sequence: list[str] = []

        # If X is in play, calculates its next position
        if X != 0:
            new_X: int = X + roll if X + roll <= n_fields else X

            # Analyzes next position if it is valid and not final
            if new_X != Y or new_X == n_fields:
                next_moves, sequence = self.find_minimum(new_X, Y, next_roll_index, rolls, n_fields, memorized_moves)

                # Seeks minimum required moves to solve the sequence
                if next_moves + 1 < min_move_count:
                    min_move_count = next_moves + 1
                    best_sequence = [('X', new_X)] + sequence

        # If Y is in play, calculates its next position
        if Y != 0:
            new_Y: int = Y + roll if Y + roll <= n_fields else Y

            # Analyzes next position if it is valid and not final
            if new_Y != X or new_Y == n_fields:
                next_moves, sequence = self.find_minimum(X, new_Y, next_roll_index, rolls, n_fields, memorized_moves)

                # Seeks minimum required moves to solve the sequence
                if next_moves + 1 < min_move_count:
                    min_move_count = next_moves + 1
                    best_sequence = [('Y', new_Y)] + sequence

        # If a 6 is rolled and either token can be moved to the board
        if roll == 6:
            if X == 0 and Y != 1:

                next_moves, sequence = self.find_minimum(1, Y, next_roll_index, rolls, n_fields, memorized_moves)
                if next_moves + 1 < min_move_count:
                    min_move_count = next_moves + 1
                    best_sequence = [('X', 1)] + sequence

            if Y == 0 and 1 != X:

                next_moves, sequence = self.find_minimum(X, 1, next_roll_index, rolls, n_fields, memorized_moves)
                if next_moves + 1 < min_move_count:
                    min_move_count = next_moves + 1
                    best_sequence = [('Y', 1)] + sequence
        memorized_moves[(X, Y, roll_index)] = (min_move_count, best_sequence)

        return min_move_count, best_sequence

    def _generate_experiment(
        self,
        experiment_name: str,
        n_instances: int,
        dialogue_partners: list[tuple[str, str]],
        prompt_name: str,
        n_fields: int,
        n_rolls: int
    ) -> None:
        """
        Given experiment specifications, generates an experiment as well as a
        number of game instances, then attaches the game instances to the
        experiment.
        
        Args:
            experiment_name (str): name of the experiment, which matches the
                                   game variant
            n_instances (int): the number of instances to be generated and
                               attached to the experiment
            dialogue_partners (list[tuple[str, str]]): the players in the game
                                                       variant
            prompt_name (str): the prompt associated with the desired game
                               variant
            n_fields (int): the size of the board in the game
            n_rolls (int): the number of rolls; also the maximum number of
                           turns
        """
        # Creates an experiment
        experiment: dict = self.add_experiment(experiment_name, dialogue_partners)

        # Generates and attaches game instances to the experiment
        for index in range(n_instances):
            self._generate_instance(
                experiment,
                f"in{index + 1:03}",
                dialogue_partners,
                prompt_name,
                n_fields,
                n_rolls
            )

    def _generate_instance(
        self,
        experiment: dict,
        game_id: int,
        dialogue_partners: dict[str: str],
        prompt_name: str,
        n_fields: int,
        n_rolls: int
    ) -> None:
        """
        Given an instantiated experiment dictionary and the various arguments
        that describe the instance configurations, randomly generates die
        rolls, checks to make sure the sequence of die rolls results in a
        solvable game, then attaches the instance to the experiment, and
        configures the instance.
        
        Args:
            experiment (dict): where the instance will be attached
            game_id (dict): the identifying marker for the game instance
            dialogue_partners (dict[str: str]): the players in the game
                                                       variant
            prompt_name (str): the initial prompt passed to the LLM
            n_fields (int): the size of the board
            n_rolls (int): the number of rolls; also the maximum number of
                           turns

        Raises:
            ValueError: raised if either too few or too many dialogue partners
                        are introduced
        """
        while True:
            p1_min_moves = self._check_sequence(
                n_fields,
                p1_rolls := [np.random.randint(1, 7) for _ in range(n_rolls)]
            )
            if p1_min_moves != -1:
                match len(dialogue_partners):
                    case 1:
                        rolls: list[int] = p1_rolls
                    case 2:
                        if self._check_sequence(
                            n_fields,
                            p2_rolls := [np.random.randint(1, 7) for _ in range(n_rolls)]
                        ) != -1:
                            rolls: list[tuple[int, int]] = [
                                (p1_roll, p2_roll)
                                for p1_roll, p2_roll
                                in zip(p1_rolls, p2_rolls)
                            ]
                        else:
                            continue
                    case _:
                        raise ValueError("There should only be two dialogue partners.")

                game_instance: dict = self.add_game_instance(experiment, game_id)
                game_instance["dialogue_partners"] = dialogue_partners
                game_instance["prompt_name"] = prompt_name
                game_instance["n_fields"] = n_fields
                game_instance["rolls"] = rolls
                game_instance["min_moves"] = p1_min_moves
                break


if __name__ == '__main__':
    # Example experiment
    experiments: list[dict] = [
        {
            "experiment_name": "single_player",
            "n_instances": 1,
            "dialogue_partners": {
                "player 1": "llm"
            },
            "prompt_name": "single_player",
            "n_fields": 23,
            "n_rolls": 20
        }
    ]

    # Generates game instances
    instance_generator: LudoInstanceGenerator = LudoInstanceGenerator()
    instance_generator.generate(experiments=experiments)
