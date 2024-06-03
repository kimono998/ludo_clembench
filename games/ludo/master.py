import sys
sys.path.append('../../clemgame')  # Path to clemgame module
sys.path.append('../../')  # Path to the parent directory which contains backends
# in master.py

from clemgame import file_utils, transcript_utils
from game import Game  

class LudoGameMaster(GameMaster):
    def __init__(self, player_model):
        super().__init__("ludo")  # Ensure game name is passed here
        self.game = Game(player_model, "<system_prompt>", "<instructions>")

    def setup(self, **kwargs):
        # Implement setup logic if necessary
        pass

    def run(self):
        # Main loop to run the game
        try:
            while not self.game.is_game_over() and self.game.turn < 20:
                self.game.make_move()
        except Exception as e:
            print(f"Error during game execution: {e}")

    def teardown(self):
        # Clean up after game is over
        print("Game over after", self.game.turn, "turns.")

class LudoGameBenchmark(GameBenchmark):
    def __init__(self, game_instance, player_models):
        super().__init__("ludo")  # Correct initialization of superclass
        self.game_master = LudoGameMaster(player_models[0])

    def get_description(self):
        return "Benchmark for the Ludo game designed to challenge and evaluate strategic model behavior."

# Register the game benchmark
def register_benchmark():
    return {
        'ludo': LudoGameBenchmark
    }

# Here for clarity
if __name__ == "__main__":
    # Simulate a command line call
    # The real command line tool would handle setting up models and calling the right game master
    model = None  
    game_instance = {}  
    ludo_benchmark = LudoGameBenchmark(game_instance, [model])
    ludo_benchmark.game_master.run()
