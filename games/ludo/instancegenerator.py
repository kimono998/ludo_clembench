"""
Module focused on generating game instances for the game 'Ludo'.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.append(str(Path(__file__).parent.parent.parent))

from clemgame.clemgame import GameInstanceGenerator

N_FIELDS = 23
N_INSTANCES = 5
N_ROLLS = 30
EXP_VARIANTS = ["single_player", "multiplayer"]
COT = [True, False]
REPROMPT = [True, False]
SINGLE_TOKEN = [True, False]
NO_BOARD = [True, False]

GAME_NAME: str = "ludo"
RANDOM_SEED: int = 23

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



    def on_generate(self):
        for item in EXP_VARIANTS:
            for c in COT:
                for r in REPROMPT:
                    for b in NO_BOARD:
                        if item == 'multiplayer':
                            for s in SINGLE_TOKEN:
                                self._generate_experiment(item, c, r, b, s)
                        else:
                            self._generate_experiment(item, c, r, b)

    def _generate_experiment(
            self,
            experiment_name: str,
            chain_of_thought,
            reprompt,
            no_board,
            n_tokens=False
    ) -> None:
        """
        Given experiment specifications, generates an experiment as well as a
        number of game instances, then attaches the game instances to the
        experiment.

        Args:
            experiment_name (str): name of the experiment, which matches the game variant.
            chain_of_thought (bool): is CoT enabled.
            reprompt (bool): is reprompting enabled.

            n_tokens (bool): is it single or multiplayer.
        """
        # Creates an experiment
        num_players = 1 if experiment_name == 'single_player' else 2
        num_tokens = 1 if n_tokens == True else 2
        experiment: dict = self.add_experiment(f'{experiment_name}_{chain_of_thought}_{reprompt}_{no_board}_{num_tokens}')
        experiment['chain_of_thought'] = chain_of_thought
        experiment['reprompting'] = reprompt
        experiment['n_tokens'] = num_tokens
        experiment['no_board'] = no_board

        # Generates and attaches game instances to the experiment
        for index in range(N_INSTANCES):
            self._generate_instance(
                experiment,
                f"in{index + 1:03}",
                experiment_name,
                num_tokens,
                N_FIELDS,
                N_ROLLS,
                num_players
            )

    def _check_sequence(
            self,
            n_fields: int,
            n_tokens: int,
            rolls: list[int]
    ) -> int:
        """
        Given the size of the board and a sequence of rolls, checks that the
        sequence of rolls will result in a game instance that is solvable.

        Args:
            n_fields (int): the size of the board
            n_tokens (int): the number of tokens to be given to each player
            rolls (list[int]): contains a sequence of die rolls

        Returns:
            int: minimum number of moves required to solve the die sequence
        """
        match n_tokens:
            case 1:
                min_moves, _ = find_monotoken_minimum(
                    rolls=rolls,
                    n_fields=n_fields,
                    memorized_moves=dict()
                )
            case 2:
                min_moves, _ = find_multitoken_minimum(
                    rolls=rolls,
                    n_fields=n_fields,
                    memorized_moves=dict()
                )

        if min_moves == float('inf'):
            return -1

        return min_moves

    def _generate_instance(
            self,
            experiment: dict,
            game_id: int,
            prompt_name: str,
            n_tokens: int,
            n_fields: int,
            n_rolls: int,
            num_players: int
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
        rolls, min_moves = self._get_rolls(
            n_tokens=n_tokens,
            n_fields=n_fields,
            n_rolls=n_rolls,
            num_players=num_players
        )

        game_instance: dict = self.add_game_instance(experiment, game_id)
        game_instance["num_players"] = num_players
        game_instance["prompt_name"] = prompt_name
        game_instance["n_tokens"] = n_tokens
        game_instance["n_fields"] = n_fields
        game_instance["rolls"] = rolls
        game_instance["min_moves"] = min_moves

    def _get_rolls(
            self,
            n_tokens: int,
            n_fields: int,
            n_rolls: int,
            num_players: int,
    ) -> tuple[list[int | tuple[int, int]], int]:
        """
        Generates valid die rolls resulting in a solvable sequence, depending
        on the number of dialogue partners and the number of tokens in the
        game variant.

        Args:
            dialogue_partners (dict[str: str]): the players in the game
                                                       variant
            n_tokens (int): the number of tokens to be given to each player
            n_fields (int): the size of the board
            n_rolls (int): the number of rolls; also the maximum number of
                           turns

        Returns:
            tuple[list[int | tuple[int, int]], int]: contains a list of either
                                                     single or pairs of die
                                                     rolls, as well as the
                                                     minimum number of moves
                                                     required to solve the
                                                     sequence
        """
        p1_rolls, min_moves = self._generate_valid_rolls(
            n_tokens=n_tokens,
            n_fields=n_fields,
            n_rolls=n_rolls
        )

        match num_players:
            case 1:
                rolls: list[int] = p1_rolls

            case 2:
                p2_rolls, _ = self._generate_valid_rolls(
                    n_tokens=n_tokens,
                    n_fields=n_fields,
                    n_rolls=n_rolls
                )
                rolls: list[int] = [
                    (p1_roll, p2_roll)
                    for p1_roll, p2_roll
                    in zip(p1_rolls, p2_rolls)
                ]

        return rolls, min_moves

    def _generate_valid_rolls(
            self,
            n_tokens: int,
            n_fields: int,
            n_rolls: int
    ) -> tuple[list[int], int]:
        """
        Generates a sequence of die rolls which result in a solvable game,
        then returns the die rolls and the minimum number of moves required to
        solve the sequence.

        Args:
            n_tokens (int): the number of tokens to be given to each player
            n_fields (int): the size of the board
            n_rolls (int): the number of rolls; also the maximum number of
                           turns

        Returns:
            tuple[list[int], int]: contains a list of die rolls and the
                                   minimum number of moves required to solve
                                   the sequence
        """
        while True:
            rolls: list[int] = [np.random.randint(1, 7) for _ in range(n_rolls)]
            min_moves: int = self._check_sequence(
                n_fields=n_fields,
                n_tokens=n_tokens,
                rolls=rolls
            )
            if min_moves != -1:
                return rolls, min_moves


def find_monotoken_minimum(
            rolls: list[int],
            n_fields: int,
            memorized_moves: dict,
            X: int = 0,
            index: int = 0,
    ) -> tuple[int, list[tuple[str, int]]]:
        """
        Finds the minimum number of moves required to solve a sequence of
        die rolls, as well as the moves associated with that minimum.

        Args:
            rolls (list[int]): contains die rolls
            n_fields (int): the size of the board
            memorized_moves (dict[tuple: tuple]): used to contain the moves as
                                                  they are evaluated
            X (int): position of the token 'X' in terms of the field
                     number it is currently occupying
            index (int): the index of the current roll being considered

        Returns:
            tuple[int, list[tuple[str, int]]]: contains the minimum number of
                                               moves required to solve the
                                               sequence and the associated
                                               move sequence
        """
        # For completed sequences
        if X == n_fields:
            return 0, []

        # For sequences that have surpassed the turn limit
        if index >= len(rolls):
            return float('inf'), []

        # If the move has already been analyzed
        if (X, index) in memorized_moves:
            return memorized_moves[(X, index)]

        roll: int = rolls[index]
        next_index: int = index + 1
        min_move_count: float | int = float('inf')
        best_sequence: list[str] = []

        # If X is in play, calculates its next position
        if X != 0:
            new_X: int = X + roll if X + roll <= n_fields else X

            # Analyzes next position if it is valid and not final
            if new_X == n_fields:
                next_moves, sequence = find_multitoken_minimum(
                    rolls=rolls,
                    n_fields=n_fields,
                    memorized_moves=memorized_moves,
                    X=new_X,
                    index=next_index
                )

                # Seeks minimum required moves to solve the sequence
                if next_moves + 1 < min_move_count:
                    min_move_count = next_moves + 1
                    best_sequence = [('X', new_X)] + sequence

        # If a 6 is rolled and either token can be moved to the board
        if roll == 6:
            if X == 0:
                next_moves, sequence = find_multitoken_minimum(
                    rolls=rolls,
                    n_fields=n_fields,
                    memorized_moves=memorized_moves,
                    X=1,
                    index=next_index
                )
                if next_moves + 1 < min_move_count:
                    min_move_count = next_moves + 1
                    best_sequence = [('X', 1)] + sequence

        memorized_moves[(X, index)] = (min_move_count, best_sequence)

        if roll != 6:
            if X == 0:
                next_moves, sequence = find_multitoken_minimum(
                    rolls=rolls,
                    n_fields=n_fields,
                    memorized_moves=memorized_moves,
                    X=X,
                    index=next_index
                )
                if next_moves + 1 < min_move_count:
                    min_move_count = next_moves + 1
                    best_sequence = [('X', 0)] + sequence

        return min_move_count, best_sequence


def find_multitoken_minimum(
            rolls: list[int],
            n_fields: int,
            memorized_moves: dict,
            X: int = 0,
            Y: int = 0,
            index: int = 0,
    ) -> tuple[int, list[tuple[str, int]]]:
        """
        Finds the minimum number of moves required to solve a sequence of
        die rolls, as well as the moves associated with that minimum.

        Args:
            rolls (list[int]): contains die rolls
            n_fields (int): the size of the board
            memorized_moves (dict[tuple: tuple]): used to contain the moves as
                                                  they are evaluated
            X (int): position of the token 'X' in terms of the field
                     number it is currently occupying
            Y (int): position of the token 'Y' in terms of the field
                     number it is currently occupying
            index (int): the index of the current roll being considered

        Returns:
            tuple[int, list[tuple[str, int]]]: contains the minimum number of
                                               moves required to solve the
                                               sequence and the associated
                                               move sequence
        """
        # For completed sequences
        if X == n_fields and Y == n_fields:
            return 0, []

        # For sequences that have surpassed the turn limit
        if index >= len(rolls):
            return float('inf'), []

        # If the move has already been analyzed
        if (X, Y, index) in memorized_moves:
            return memorized_moves[(X, Y, index)]

        roll: int = rolls[index]
        next_index: int = index + 1
        min_move_count = float('inf')
        best_sequence: list[str] = []

        # If X is in play, calculates its next position
        if X != 0:
            new_X: int = X + roll if X + roll <= n_fields else X

            # Analyzes next position if it is valid and not final
            if new_X != Y or new_X == n_fields:
                next_moves, sequence = find_multitoken_minimum(
                    rolls=rolls,
                    n_fields=n_fields,
                    memorized_moves=memorized_moves,
                    X=new_X,
                    Y=Y,
                    index=next_index
                )

                # Seeks minimum required moves to solve the sequence
                if next_moves + 1 < min_move_count:
                    min_move_count = next_moves + 1
                    best_sequence = [('X', new_X)] + sequence

        # If Y is in play, calculates its next position
        if Y != 0:
            new_Y: int = Y + roll if Y + roll <= n_fields else Y

            # Analyzes next position if it is valid and not final
            if new_Y != X or new_Y == n_fields:
                next_moves, sequence = find_multitoken_minimum(
                    rolls=rolls,
                    n_fields=n_fields,
                    memorized_moves=memorized_moves,
                    X=X,
                    Y=new_Y,
                    index=next_index
                )

                # Seeks minimum required moves to solve the sequence
                if next_moves + 1 < min_move_count:
                    min_move_count = next_moves + 1
                    best_sequence = [('Y', new_Y)] + sequence

        # If a 6 is rolled and either token can be moved to the board
        if roll == 6:
            if X == 0 and Y != 1:
                next_moves, sequence = find_multitoken_minimum(
                    rolls=rolls,
                    n_fields=n_fields,
                    memorized_moves=memorized_moves,
                    X=1,
                    Y=Y,
                    index=next_index
                )
                if next_moves + 1 < min_move_count:
                    min_move_count = next_moves + 1
                    best_sequence = [('X', 1)] + sequence

            if Y == 0 and 1 != X:
                next_moves, sequence = find_multitoken_minimum(
                    rolls=rolls,
                    n_fields=n_fields,
                    memorized_moves=memorized_moves,
                    X=X,
                    Y=1,
                    index=next_index
                )
                if next_moves + 1 < min_move_count:
                    min_move_count = next_moves + 1
                    best_sequence = [('Y', 1)] + sequence

        if roll != 6:
            if X == 0 and Y == 0:
                next_moves, sequence = find_multitoken_minimum(
                    rolls=rolls,
                    n_fields=n_fields,
                    memorized_moves=memorized_moves,
                    X=X,
                    Y=Y,
                    index=next_index
                )
                if next_moves + 1 < min_move_count:
                    min_move_count = next_moves + 1
                    best_sequence = [('X', 0)] + sequence


        memorized_moves[(X, Y, index)] = (min_move_count, best_sequence)

        return min_move_count, best_sequence


if __name__ == '__main__':


    LudoInstanceGenerator().generate()