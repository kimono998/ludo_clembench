import sys
import os
import re
from pathlib import Path

#Adjust the path to include the directory containing the 'backends' module
script_directory = Path(__file__).parent
project_root = script_directory.parent.parent  
sys.path.append(str(project_root))

from backends import ModelSpec, Model, get_model_for, load_model_registry
from instancegenerator import GenerateSequences

class Game:
    def __init__(self, llm: Model, system_prompt: str, instructions: str, game_instance):
        self.llm = llm
        self.system_prompt = system_prompt
        self.instructions = instructions
        self.last_response = []
        self.context = []
        self.reprompt = False
        self.n_fields = 23
        self.board = " ".join(["□"] * self.n_fields)
        self.current_state = self.board
        self.rolls = game_instance['sequence']
        self.turn = 0
        self.tokens_inplay = {"X": False, "Y": False}
        self.current_position = {"X": 0, "Y": 0}
        self.six_count = 0

    def _parse_reply(self, reply):
        match = re.search(r"MY MOVE: X -> (\d+) ; Y -> (\d+)", reply)
        if not match:
            raise ValueError("Invalid response format")
        return {"X": int(match.group(1)), "Y": int(match.group(2))}

    def _check_move(self, move, roll):
        # Detailed validation logic here
        # This should return True if the move is valid, False otherwise
        return True  # Placeholder, implement specific rules

    def make_move(self):
        message = f"{self.instructions}\nCurrent state: {self.current_state}\nTurn number: {self.turn}, Roll: {self.rolls[self.turn]}. Where will you move your token?"
        self.context.append({"role": "user", "content": message})
        _, _, response_text = self.llm.generate_response(self.context)
        try:
            move = self._parse_reply(response_text)
            if self._check_move(move, self.rolls[self.turn]):
                # Update the board and other state
                print("Valid move processed")
            else:
                print("Invalid move detected")
                return False  # Optionally end the game or handle differently
        except ValueError as e:
            print(f"Error parsing response: {e}")
            return False
        self.last_response.append(response_text)
        self.turn += 1
        return True

    def run_game(self):
        while self.turn < len(self.rolls) and self.turn < 20:
            if not self.make_move():
                print("Stopping the game due to an invalid move.")
                break

def main():
    load_model_registry()
    THIS_MODEL = {"model_id": "gpt-3.5-turbo-1106", "backend": "openai", "model_name": "gpt-3.5-turbo-1106"}
    llm = get_model_for(THIS_MODEL)
    llm.set_gen_args(temperature=0.0, max_tokens=400)

    prompts_path = Path(__file__).parent / "resources" / "initial_prompts"
    system_prompt_path = prompts_path / "simple_prompt_v1.txt"
    instructions_path = prompts_path / "multitoken_v1_pace.txt"

    with open(system_prompt_path, 'r') as f:
        system_prompt = f.read()
    with open(instructions_path, 'r') as f:
        instructions = f.read()

    generator = GenerateSequences()
    game_instances = generator.generate_instance(23, 1, 50)

    for index, instance in game_instances.items():
        game = Game(llm, system_prompt, instructions, instance)
        game.run_game()
        print(f"Game {index} Responses:")
        for response in game.last_response:
            print(response)

if __name__ == "__main__":
    main()
