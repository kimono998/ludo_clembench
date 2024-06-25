"""
Module focused on generating game instances for the game 'Ludo'.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.append(str(Path(__file__).parent.parent.parent))

from clemgame.clemgame import GameInstanceGenerator, GameResourceLocator


GAME_NAME: str = "ludo"
DIRECTORY_PATH: Path = Path(__file__).parent
RESOURCE_PATH: Path = DIRECTORY_PATH / "resources"
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
                self.load_template(str(RESOURCE_PATH / experiment["prompt_filename"])),
                experiment["n_fields"],
                experiment["n_rolls"]
            )

    def _check_sequence(
        self,
        n_fields: int,
        rolls: list[int]
    ) -> tuple[int, list[str]]:
        """
        Given the size of the board and a sequence of rolls, checks that the
        sequence of rolls will result in a game instance that is solvable.
        
        Args:
            n_fields (int): the size of the board
            rolls (list[int]): contains a sequence of die rolls
        
        Returns:
            tuple[int, list[str]]: contains the minimum number of moves
                                    required to solve the sequence, as well as
                                    the optimal moves it takes to do so
        """
        memorized_moves: dict = {}

        def datapace(X: int, Y: int, roll_index: int) -> tuple[int, list[str]]:
            """
            TODO Description
            
            Args:
                X (int): position of the token 'X' in terms of the field
                         number it is currently occupying
                Y (int): position of the token 'Y' in terms of the field
                         number it is currently occupying
                roll_index (int): the index of the current roll being
                                considered
            
            Returns:
                tuple[int, list[str]]: contains the minimum number of moves
                                    required to solve the sequence, as well as
                                    the optimal moves it takes to do so
            """
            if X == n_fields and Y == n_fields:
                return 0, []
            if roll_index >= len(rolls):
                return float('inf'), []
            if (X, Y, roll_index) in memorized_moves:
                return memorized_moves[(X, Y, roll_index)]

            roll: int = rolls[roll_index]
            next_roll_index: int = roll_index + 1
            moves = float('inf')
            best_move_seq: list[str] = []

            if X != 0:
                new_X: int = X + roll if X + roll <= n_fields else X
                if new_X != Y or new_X == n_fields:
                    next_moves, move_seq = datapace(new_X, Y, next_roll_index)
                    if 1 + next_moves < moves:
                        moves = 1 + next_moves
                        best_move_seq: list[str] = [f"Move X from {X} to {new_X}"] + move_seq

            if Y != 0:
                new_Y: int = Y + roll if Y + roll <= n_fields else Y
                if new_Y != X or new_Y == n_fields:
                    next_moves, move_seq = datapace(X, new_Y, next_roll_index)
                    if 1 + next_moves < moves:
                        moves = 1 + next_moves
                        best_move_seq = [f"Move Y from {Y} to {new_Y}"] + move_seq

            if roll == 6:
                if X == 0 and 1 != Y:
                    next_moves, move_seq = datapace(1, Y, next_roll_index)
                    if 1 + next_moves < moves:
                        moves = 1 + next_moves
                        best_move_seq: list[str] = ["Place X on 1"] + move_seq
                if Y == 0 and 1 != X:
                    next_moves, move_seq = datapace(X, 1, next_roll_index)
                    if 1 + next_moves < moves:
                        moves = 1 + next_moves
                        best_move_seq: list[str] = ["Place Y on 1"] + move_seq

            memorized_moves[(X, Y, roll_index)] = (moves, best_move_seq)

            return moves, best_move_seq

        initial_X, initial_Y = 0, 0
        result, move_sequence = datapace(initial_X, initial_Y, 0)

        if result == float('inf'):
            return -1, []

        return result, move_sequence

    def _generate_experiment(
        self,
        experiment_name: str,
        n_instances: int,
        dialogue_partners: list[tuple[str, str]],
        initial_prompt: str,
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
            initial_prompt (str): the prompt associated with the desired game
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
                initial_prompt,
                n_fields,
                n_rolls
            )

    def _generate_instance(
        self,
        experiment: dict,
        game_id: int,
        dialogue_partners: list[tuple[str, str]],
        initial_prompt: str,
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
            dialogue_partners (list[tuple[str, str]]): the players in the game
                                                       variant
            initial_prompt (str): the initial prompt passed to the LLM
            n_fields (int): the size of the board
            n_rolls (int): the number of rolls; also the maximum number of
                           turns
        """
        # Generates new rolls until finding a viable sequence
        while True:
            # Generates and validates rolls for each player
            min_moves_p1, _ = self._check_sequence(
                n_fields,
                p1_rolls := [np.random.randint(1, 7) for _ in range(n_rolls)]
            )
            min_moves_p2, _ = self._check_sequence(
                n_fields,
                p2_rolls := [np.random.randint(1, 7) for _ in range(n_rolls)]
            )
            
            # Attaches game instance to the experiment
            if min_moves_p1 != -1 and min_moves_p2:
                game_instance: dict = self.add_game_instance(experiment, game_id)
                game_instance["dialogue_partners"] = dialogue_partners
                game_instance["initial_prompt"] = initial_prompt
                game_instance["n_fields"] = n_fields
                game_instance["rolls"] = [
                    (p1_roll, p2_roll)
                    for p1_roll, p2_roll
                    in zip(p1_rolls, p2_rolls)
                ]
                break


if __name__ == '__main__':
    # Example experiment
    experiments: list[dict] = [
        {
            "experiment_name": "basic",
            "n_instances": 5,
            "dialogue_partners": {
                "player_1": "llm",
                "player_2": "programmatic"
            },
            "prompt_filename": "initial_prompt.template",
            "n_fields": 23,
            "n_rolls": 20
        }
    ]

    # Generates game instances
    instance_generator: LudoInstanceGenerator = LudoInstanceGenerator()
    instance_generator.generate(experiments=experiments)
