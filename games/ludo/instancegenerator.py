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
                experiment["experiment_name"],
                experiment["n_tokens"],
                experiment["n_fields"],
                experiment["n_rolls"]
            )
    
    def _check_sequence(
            self,
            n_fields: int,
            rolls: list[int]
    ) -> tuple[bool, int] | bool:
        """
        Given the size of the board and a sequence of rolls, checks that the
        sequence of rolls will result in a game instance that is solvable.
        
        Args:
            n_fields (int): the size of the board
            rolls (list[int]): contains a sequence of die rolls
        
        Returns:
            tuple[bool, int] | bool: either a tuple containing a bool (True if
                                     the sequence is solveable and False
                                     otherwise) and an integer (the minimum
                                     number of moves required to solve the
                                     sequence) or a bool (False, indicating
                                     that the sequence is not solveable)
        """
        memorized_moves: dict = {}

        def find_minimum(
                X: int,
                Y: int,
                roll_index: int
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
                    next_moves, sequence = find_minimum(new_X, Y, next_roll_index)
                    
                    # Seeks minimum required moves to solve the sequence
                    if next_moves + 1 < min_move_count:
                        min_move_count = next_moves + 1
                        best_sequence = [f"Move X from {X} to {new_X}"] + sequence

            # If Y is in play, calculates its next position
            if Y != 0:
                new_Y: int = Y + roll if Y + roll <= n_fields else Y
                
                # Analyzes next position if it is valid and not final
                if new_Y != X or new_Y == n_fields:
                    next_moves, sequence = find_minimum(X, new_Y, next_roll_index)
                    
                    # Seeks minimum required moves to solve the sequence
                    if next_moves + 1 < min_move_count:
                        min_move_count = next_moves + 1
                        best_sequence = [f"Move Y from {Y} to {new_Y}"] + sequence

            # If a 6 is rolled and either token can be moved to the board
            if roll == 6:
                if X == 0 and Y != 1:
                    next_moves, sequence = find_minimum(1, Y, next_roll_index)
                    if next_moves + 1 < min_move_count:
                        min_move_count = next_moves + 1
                        best_sequence = ["Place X on 1"] + sequence

                if Y == 0 and 1 != X:
                    next_moves, sequence = find_minimum(X, 1, next_roll_index)
                    if next_moves + 1 < min_move_count:
                        min_move_count = next_moves + 1
                        best_sequence = ["Place Y on 1"] + sequence

            memorized_moves[(X, Y, roll_index)] = (min_move_count, best_sequence)

            return min_move_count, best_sequence

        # Initiates the search for the minimum move count
        initial_X, initial_Y = 0, 0
        min_move_count, _ = find_minimum(initial_X, initial_Y, 0)

        if min_move_count == float("inf"):
            return False
        
        return min_move_count != -1, min_move_count

    def _check_monotoken_sequence(self, n_fields: int, rolls: list[int]) -> tuple:
        """
        TODO Method description
        
        Args:
            TODO n_fields (int):
            TODO rolls (list[int]):
        
        Returns:
            TODO tuple:
        """
        memorized_moves: dict = {}

        def find_minimum(position: int, idx: int) -> tuple:
            """
            TODO Method description
            
            Args:
                TODO position (int):
                TODO idx (int):
            
            Returns:
                TODO tuple:
            """
            if position == n_fields:
                return 0, []
            
            if idx >= len(rolls):
                return float("inf"), []
            
            if (position, idx) in memorized_moves:
                return memorized_moves[(position, idx)]
            
            roll: int = rolls[idx]
            next_idx: int = idx + 1
            min_move_count: float = float("inf")
            best_sequence: list = []

            if position != 0:
                if position + roll <= n_fields:
                    next_position: int = position + roll
                else:
                    next_position: int = position

                if next_position == n_fields:
                    next_moves, sequence = find_minimum(next_position, next_idx)
                    if next_moves + 1 < min_move_count:
                        min_move_count = next_moves + 1
                        best_sequence = [f"Move X from {position } to {next_position}"] + sequence

            if roll == 6:
                if position == 0:
                    next_moves, sequence = find_minimum(1, next_idx)
                    if next_moves + 1 < min_move_count:
                        min_move_count = next_moves + 1
                        best_sequence = ["Place X on 1"] + sequence

            memorized_moves[(position, idx)] = (min_move_count, best_sequence)

            return min_move_count, best_sequence
        
        initial_position: int = 0
        min_move_count, _ = find_minimum(initial_position, 0)

        if min_move_count == float("inf"):
            return False
        
        return min_move_count != -1, min_move_count
    
    def _generate_experiment(
            self,
            experiment_name: str,
            n_instances: int,
            dialogue_partners: list[tuple[str, str]],
            prompt_name: str,
            n_tokens: int,
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
            n_tokens (int): the number of tokens to be given to each player
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
                n_tokens,
                n_fields,
                n_rolls
            )

    def _generate_instance(
            self,
            experiment: dict,
            game_id: int,
            dialogue_partners: dict[str: str],
            prompt_name: str,
            n_tokens: int,
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
            n_tokens (int): the number of tokens to be given to each player
            n_fields (int): the size of the board
            n_rolls (int): the number of rolls; also the maximum number of
                           turns
        """
        rolls, min_moves = self._generate_rolls(
            dialogue_partners=dialogue_partners,
            n_tokens=n_tokens,
            n_fields=n_fields,
            n_rolls=n_rolls
        )
        
        game_instance: dict = self.add_game_instance(experiment, game_id)
        game_instance["dialogue_partners"] = dialogue_partners
        game_instance["prompt_name"] = prompt_name
        game_instance["n_tokens"] = n_tokens
        game_instance["n_fields"] = n_fields
        game_instance["rolls"] = rolls
        game_instance["min_moves"] = min_moves

    # TODO Incorporate n_tokens
    def _generate_rolls(
            self,
            dialogue_partners: dict[str: str],
            n_tokens: int,
            n_fields: int,
            n_rolls: int
    ) -> tuple[list[int | tuple[int, int]], int]:
        """
        TODO

        Args:
            dialogue_partners (dict[str: str]): the players in the game
                                                       variant
            n_tokens (int): the number of tokens to be given to each player
            n_fields (int): the size of the board
            n_rolls (int): the number of rolls; also the maximum number of
                           turns
        
        Returns:
            TODO tuple[list[int | tuple[int, int]], int]: 
        """
        p1_rolls, min_moves = self._generate_valid_sequence(n_tokens, n_fields, n_rolls)
        
        match len(dialogue_partners):
            case 1:
                rolls: list[int] = p1_rolls

            case 2:
                p2_rolls, _ = self._generate_valid_sequence(n_tokens, n_fields, n_rolls)
                rolls: list[int] = [
                    (p1_roll, p2_roll)
                    for p1_roll, p2_roll
                    in zip(p1_rolls, p2_rolls)
                ]

        return rolls, min_moves

    def _generate_valid_sequence(
            self,
            n_tokens: int,
            n_fields: int,
            n_rolls: int
    ) -> tuple[list[int], int]:
        """
        TODO Method description
        
        Args:
            n_tokens (int): the number of tokens to be given to each player
            n_fields (int): the size of the board
            n_rolls (int): the number of rolls; also the maximum number of
                           turns
        
        Returns:
            TODO tuple[list[int], int]:
        """
        while True:
            rolls: list[int] = [np.random.randint(1, 7) for _ in range(n_rolls)]
            match n_tokens:
                case 1:
                    min_moves: tuple | bool = self._check_monotoken_sequence(n_fields, rolls)
                case 2:
                    min_moves: tuple | bool = self._check_sequence(n_fields, rolls)
            if min_moves:
                return rolls, min_moves


if __name__ == '__main__':
    # Example experiment
    experiments: list[dict] = [
        {
            "experiment_name": "single_player",
            "n_instances": 1,
            "dialogue_partners": {
                "player 1": "llm"
            },
            "n_tokens": 2,
            "n_fields": 23,
            "n_rolls": 20
        },
        {
            "experiment_name": "multiplayer",
            "n_instances": 1,
            "dialogue_partners": {
                "player 1": "llm",
                "player 2": "programmatic"
            },
            "n_tokens": 1,
            "n_fields": 23,
            "n_rolls": 20
        }
    ]

    # Generates game instances
    instance_generator: LudoInstanceGenerator = LudoInstanceGenerator()
    instance_generator.generate(experiments=experiments)
