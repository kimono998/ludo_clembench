# Ludo Benchmark for Evaluating Chat-Optimized Language Models using clembench Framework.

This document describes a project that evaluates the capabilities of large language models (LLMs) using [clembench](https://clembench.github.io). The chosen game is Ludo, a classic turn-based board game where players strategically move tokens across a board.

## Introduction

Traditional LLM evaluation relies on static datasets and tasks focused on language understanding. However, as LLMs evolve, there's a need to assess them in more dynamic, goal-oriented environments. This work introduces Ludo as a testbed for evaluating LLMs in a situated, strategic setting.

## Ludo Benchmark Design

The Ludo adaptation features both single-player and multiplayer modes, allowing testing with varying numbers of tokens controlled by the model. Here's a breakdown of the key aspects:

- **Board**: A 1x23 ASCII board with movement only allowed from left to right.
- **Tokens**: Each player controls up to 4 tokens.
- **Goal**: Navigate all tokens successfully across the board in the fewest turns possible.
- **Evaluation**: The benchmark assesses decision-making, spatial reasoning, and the ability to follow game rules.

## Evaluation Methodology

The evaluation involved eight LLMs and explored the impact of various factors on their performance:

- **Chain of Thought (CoT) prompting**: Guides the model's thought process by providing a structured approach.
- **Reprompting**: Allows the model to receive additional prompts after making an invalid move.
- **Board representation**: Text-based vs. no board representation.
- **Single vs. multi-token control**: Tests the model's ability to manage multiple tokens.

## Key Findings

- **Overall Performance**: The game proved challenging for LLMs, with an average abortion rate of 83.1%.
- **Single Token vs. Multitoken**: Models performed significantly better when controlling a single token.
- **Chain of Thought**: CoT prompting generally improved performance, especially in multitoken scenarios.
- **Reprompting**: Reprompting showed a slight positive impact but seemed more effective in multitoken games.
- **Parsing Errors**: Most errors were parsing errors, indicating difficulty understanding game instructions.
- **Board Representation**: Providing a board representation might help reduce parsing errors.

These findings highlight the challenges LLMs face in complex, interactive environments and the importance of strategic reasoning, situational understanding, and efficient information processing.

## Future Work

The authors suggest further studies on:

- **Prompt design**: Optimizing prompts to provide clearer instructions and guidance.
- **Action space exploration**: Investigating strategies for LLMs to explore different game actions.
- **Multimodal learning**: Combining textual information with visual representations (e.g., board image) for improved understanding.




### UPDATE (16.02.24): We released v0.3 of the benchmark code. The main branch will continue as v1.0-beta which has changes that effect the game code. Follow [this guide](docs/howto_update_to_v1.md) to update your game.

# clembench: A Framework for the Systematic Evaluation of Chat-Optimized Language Models as Conversational Agents

The cLLM (chat-optimized Large Language Model, "clem") framework tests such models' ability to engage in games – rule-constituted activities played using language.
The framework is a systematic way of probing for the situated language understanding of language using agents.

This repository contains the code for setting up the framework and implements a number of games that are further discussed in 

> Chalamalasetti, K., Götze, J., Hakimov, S., Madureira, B., Sadler, P., & Schlangen, D. (2023). clembench: Using Game Play to Evaluate Chat-Optimized Language Models as Conversational Agents (arXiv:2305.13455). arXiv. https://doi.org/10.48550/arXiv.2305.13455

### Evaluation Results

On the [main project website](https://clembench.github.io) , under [leaderboard](https://clembench.github.io/leaderboard.html).

### Game details

- A Simple Word Game: [taboo](docs/taboo.md)
- A Word-Guessing Game Based on Clues: [wordle](docs/wordle.md)
- Drawing Instruction Giving and Following: [image](docs/image.md)
- An ASCII Picture Reference Game: [reference](docs/reference.md)
- Scorekeeping: [private and shared](docs/privateshared.md)

## Using the benchmark

This repository is tested on `Python 3.8+`

We welcome you to contribute to or extend the benchmark with your own games and models. 
Please simply open a pull request. You can find more information on how to use the benchmark in the links below.

- [How to run the benchmark and evaluation locally](docs/howto_run_benchmark.md)
- [How to run the benchmark, update leaderboard workflow](docs/howto_benchmark_workflow.md)
- [How to add a new model](docs/howto_add_models.md)
- [How to add and run your own game](docs/howto_add_games.md)
- [How to integrate with Slurk](docs/howto_slurk.md)
