#!/bin/sh

# List of message lengths to test
MESSAGE_LENGTHS=(8 16 32 64 128 256 512 1024)

# Default number of trials
TRIALS=5

if [ "$#" -ge 1 ]; then
    TRIALS=$1
fi

echo "Running benchmark with:"
echo "  Message lengths: ${MESSAGE_LENGTHS[@]}"
echo "  Trials per test: $TRIALS"
echo

echo "msg_len,trials,avg_time,ci_95,capacity_bps" > phase-2-report/results.csv

# Run benchmarks for each message length
for MSG_LEN in "${MESSAGE_LENGTHS[@]}"; do
    echo "Running for message length: $MSG_LEN"

    docker compose exec -T python-processor sh -c "python3 /code/python-processor/main.py &"
    sleep 1
    echo "Processor Activated"

    docker compose exec insec sh -c "python3 receiver.py &" > /dev/null 2>&1
    sleep 1
    echo "Receiver Activated"

    # Extract benchmark results in the csv format and write it inside the results file
    docker compose exec sec sh -c "python3 sender.py $MSG_LEN $TRIALS" \
    | grep '^\[CSV\]' | sed 's/^\[CSV\] //g' >> phase-2-report/results.csv

    echo "-----------------------------------------------------"
done