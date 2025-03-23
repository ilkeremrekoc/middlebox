#!/bin/sh

# List of delay values to test
MS_DELAYS="1 8 16 32 128 256 512"
REPEATS=50

# Loop through each delay value in the list
for MS_DELAY in $MS_DELAYS; do
  echo "Running test with delay: $MS_DELAY"

  # Start the Python processor
  docker compose exec -T python-processor sh -c "python3 /code/python-processor/main.py $MS_DELAY &"
  sleep 2

  # Run the ping test and save results
  docker compose exec sec sh -c "ping -c $REPEATS insec" > "ping-results/ping-result_${MS_DELAY}.txt"

  # Stop the Python processor
  docker compose exec python-processor sh -c "pkill -9 python3"

  echo "Test completed for delay: $MS_DELAY"
done

echo "All tests completed."
