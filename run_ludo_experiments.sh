#!/bin/bash

# Define the game and other parameters
game="ludo"
temperature=0
max_tokens=300
instances_name="instances"
results_dir="results"

# Define the experiment lists
single_player_experiments=(
  "single_player_True_True_True_2"
  "single_player_True_True_False_2"
  "single_player_True_False_True_2"
  "single_player_True_False_False_2"
  "single_player_False_True_True_2"
  "single_player_False_True_False_2"
  "single_player_False_False_True_2"
  "single_player_False_False_False_2"




)

multiplayer_experiments=(
  "multiplayer_True_True_True_1"
  "multiplayer_True_True_True_2"
  "multiplayer_True_True_False_1"
  "multiplayer_True_True_False_2"
  "multiplayer_True_False_True_1"
  "multiplayer_True_False_True_2"
  "multiplayer_True_False_False_1"
  "multiplayer_True_False_False_2"
  "multiplayer_False_True_True_1"
  "multiplayer_False_True_True_2"
  "multiplayer_False_True_False_1"
  "multiplayer_False_True_False_2"
  "multiplayer_False_False_True_1"
  "multiplayer_False_False_True_2"
  "multiplayer_False_False_False_1"
  "multiplayer_False_False_False_2"

)

# Define the player lists
single_player_model="gpt-3.5-turbo-1106"
multiplayer_models="gpt-3.5-turbo-1106 programmatic"

# Function to run experiments
run_experiment() {
  local experiment=$1
  local model_args=$2

  echo "Running experiment: $experiment with models: $model_args"
  python3 /Users/dicaristic/PycharmProjects/clembench/scripts/cli.py run \
    -g "$game" \
    -m $model_args \
    -t "$temperature" \
    -l "$max_tokens" \
    -i "$instances_name" \
    -r "$results_dir" \
    -e "$experiment"

  echo "Scoring experiment: $experiment"
  python3 /Users/dicaristic/PycharmProjects/clembench/scripts/cli.py score \
    -g "$game" \
    -r "$results_dir" \
    -e "$experiment"

  echo "Transcribing experiment: $experiment"
  python3 /Users/dicaristic/PycharmProjects/clembench/scripts/cli.py transcribe \
    -g "$game" \
    -r "$results_dir" \
    -e "$experiment"
}

# Run single-player experiments
for experiment in "${single_player_experiments[@]}"; do
  run_experiment "$experiment" "$single_player_model"
done

# Run multiplayer experiments
for experiment in "${multiplayer_experiments[@]}"; do
  run_experiment "$experiment" "$multiplayer_models"
done
