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

    def _check_sequence(self, board_size, rolls):
        N = board_size  # Total number of fields
        memo = {}  # Memorized moves

        def dp(posX, posY, roll_index):
            if posX == N and posY == N:
                return 0, []
            if roll_index >= len(rolls):
                return float('inf'), []
            if (posX, posY, roll_index) in memo:
                return memo[(posX, posY, roll_index)]

            roll = rolls[roll_index]
            next_roll_index = roll_index + 1
            moves = float('inf')
            best_move_seq = []

            if posX != 0:
                new_posX = posX + roll if posX + roll <= N else posX
                if new_posX != posY or new_posX == N:
                    next_moves, move_seq = dp(new_posX, posY, next_roll_index)
                    if 1 + next_moves < moves:
                        moves = 1 + next_moves
                        best_move_seq = [f"Move X from {posX} to {new_posX}"] + move_seq

            if posY != 0:
                new_posY = posY + roll if posY + roll <= N else posY
                if new_posY != posX or new_posY == N:
                    next_moves, move_seq = dp(posX, new_posY, next_roll_index)
                    if 1 + next_moves < moves:
                        moves = 1 + next_moves
                        best_move_seq = [f"Move Y from {posY} to {new_posY}"] + move_seq

            if roll == 6:
                if posX == 0 and 1 != posY:
                    next_moves, move_seq = dp(1, posY, next_roll_index)
                    if 1 + next_moves < moves:
                        moves = 1 + next_moves
                        best_move_seq = ["Place X on 1"] + move_seq
                if posY == 0 and 1 != posX:
                    next_moves, move_seq = dp(posX, 1, next_roll_index)
                    if 1 + next_moves < moves:
                        moves = 1 + next_moves
                        best_move_seq = ["Place Y on 1"] + move_seq

            memo[(posX, posY, roll_index)] = (moves, best_move_seq)
            return moves, best_move_seq

        initial_posX, initial_posY = 0, 0
        result, move_sequence = dp(initial_posX, initial_posY, 0)
        if result == float('inf'):
            return -1, []
        return result, move_sequence

    def _generate_experiment(
        self,
        experiment_name: str,
        n_instances: int,
        initial_prompt: str,
        n_fields: int,
        turn_limit: int,
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
            turn_limit (int): the maximum number of turns allowed
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
                n_fields,
                turn_limit
            )
    
    def _generate_instance(
        self,
        experiment: dict,
        game_id: int,
        initial_prompt: str,
        n_fields: int,
        turn_limit: int
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
            turn_limit (int): the maximum number of turns
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
            game_instance["turn_limit"] = turn_limit


def main() -> None:
    pass


if __name__ == '__main__':
    main()
