<<<<<<< Updated upstream
=======
"""
Module description
"""

from backends import Model


class Game:
    """
    Class description
    """
    def __init__(self, llm: Model, system_prompt: str, task_description: str) -> None:
        """
        Method description
        """
        self.llm: Model = llm
        self.system_prompt: str = system_prompt
        self.task_description: str = task_description
        self.context: list = []
        self._initialize_context()

    def make_move(self, turn: int, roll: int, current_state: str) -> None:
        """
        Method description

        Args:
            turn (int):
            roll (int):
            current_state (str):
        """
        # Creates turn-dependent prompt
        message: str = (
            f"Beginning state: {current_state}\n" if turn == 0
            else f"Current state: {current_state}\n"
        )
        message += (
            f"Turn: {turn}, Roll: {roll}\n" +
            "Where will you move your token? Let's think step by step."
        )
        self._add_message(message)

    def _add_message(self, message: str, role: str = "user") -> None:
        """
        Adds a message to the conversation context. If it is the first message
        being added, the system prompt is added to the beginning.

        Args:
            message (str): to be added to the conversation context
            role (str): either 'system', 'assistant', or 'user'
        """
        if not self.context:
            self.context = [{"role": "system", "content": self.system_prompt}]

        self.context.append({"role": role, "content": message})

    def _initialize_context(self) -> None:
        """
        Method description
        """
        self._add_message(self.system_prompt, "system")
        self._add_message(self.task_description, "user")


def main() -> None:
    pass


if __name__ == "__main__":
    main()
>>>>>>> Stashed changes
