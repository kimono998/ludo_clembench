"""
Module description
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backends import CustomResponseModel, HumanModel, Model, get_model_for, \
    load_model_registry
from clemgame.clemgame import Player

class LudoPlayer(Player):
    """
    Class description
    """
    def __init__(self, model: Model) -> None:
        """
        Method description

        Args:
            model (Model): the configured model, being either a Model object
                           for the LLM Player or either a CustomResponseModel
                           for a programmatic Player or a HumanModel for the
                           game variations which allow for a human Player
        """
        super().__init__(model)

    # TODO Determine programmatic player behavior
    def _custom_response(self) -> None:
        """
        Method description
        """
        if isinstance(self.model, CustomResponseModel):
            pass

    # TODO Determine human player behavior
    def _terminal_response(self) -> None:
        """
        Method description
        """
        pass


def main() -> None:
    # LLM setup
    THIS_MODEL: dict = {
        "model_id": "gpt-3.5-turbo-1106",
        "backend": "openai",
        "model_name": "gpt-3.5-turbo-1106"
    }
    load_model_registry()
    
    # Model instantiation
    llm: Model = get_model_for(THIS_MODEL)
    programmatic_player: CustomResponseModel = CustomResponseModel()
    human_player: HumanModel = HumanModel() # Can be used in place of programmatic_player in game variation

    # Player instantiation
    player_1: LudoPlayer = LudoPlayer(llm)
    player_2: LudoPlayer = LudoPlayer(programmatic_player)


if __name__ == '__main__':
    main()
