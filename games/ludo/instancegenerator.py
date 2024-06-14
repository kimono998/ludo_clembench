"""
TODO Module description
"""

import sys
import numpy as np
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from clemgame.clemgame import GameInstanceGenerator


GAME_NAME: str = "ludo"
RANDOM_SEED: int = 42


# TODO Determine how GameInstanceGenerator is used -- not instantiated or called anywhere
class LudoInstanceGenerator(GameInstanceGenerator):
    """
    TODO Class description
    """
    def __init__(self):
        """
        TODO Method description
        """
        super().__init__(GAME_NAME)

    # TODO Implement main logic of LudoInstanceGenerator here
    def on_generate(self, **kwargs) -> None:
        """
        TODO Method description

        Args:
            TODO

        Returns:
            TODO
        """
        pass

    @staticmethod
    def _check_sequence(
        n_fields: int,
        rolls: list[int]
    ) -> tuple[int, list[str]]:
        """
        TODO Description
        
        Args:
            TODO n_fields (int):
            TODO rolls (list[int]):
        
        Returns:
            TODO tuple[int, list[str]]:
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
                                       required to solve the sequence, as well
                                       as the optimal moves it takes to do so
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
        initial_prompt: str,
        n_fields: int,
        dialogue_partners: list[tuple[str, str]]
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
            initial_prompt (str): the prompt associated with the desired game
                                  variant
            n_fields (int): the size of the board in the game
            dialogue_partners (list[tuple[str, str]]): the players in the game
                                                       variant
        """
        # Creates an experiment
        experiment: dict = self.add_experiment(experiment_name, dialogue_partners)
        
        # Generates and attaches game instances to the experiment
        for index in range(n_instances):
            game_id: str = f"in{index + 1:03}"
            self._generate_instance(
                experiment,
                game_id,
                initial_prompt,
                n_fields
            )
    
    def _generate_instance(
        self,
        experiment: dict,
        game_id: int,
        initial_prompt: str,
        n_fields: int
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
            initial_prompt (str): the initial prompt passed to the LLM
            n_fields (int): the size of the board
        """
        # Generates rolls and checks their viability
        np.random.seed(RANDOM_SEED)
        rolls: list[int] = [np.random.randint(1, 7) for _ in range(turn_limit)]
        min_moves, _ = self._check_sequence(n_fields, rolls)
        
        # Attaches game instance to the experiment
        if min_moves != -1:
            game_instance: dict = self.add_game_instance(experiment, game_id)
            game_instance["initial_prompt"] = initial_prompt
            game_instance["n_fields"] = n_fields
            game_instance["rolls"] = rolls


def main() -> None:
    pass


if __name__ == '__main__':
    main()
