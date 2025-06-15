#!/bin/sh

docker compose up -d --build

# Wait for the services to start
sleep 5

# Check if the services are running
if ! docker compose ps | grep -q "Up"; then
    echo "Error: One or more services failed to start."
    exit 1
fi

# List of message lengths to test
MESSAGE_LENGTHS=(50 100 250 500)
COVERT_OR_VISIBLE=("covert" "visible")
MAX_TOTAL_CHARS=1000

echo "Running benchmark with:"
echo "  Message lengths: ${MESSAGE_LENGTHS[@]}"
echo

docker compose exec -T python-processor sh -c "echo "msg_id,msg_len,is_covert,is_detected" > results.csv"
docker compose exec -T python-processor sh -c "echo "msg_id,is_covert" > mitigation_results.csv"

docker compose exec insec sh -c "python3 receiver.py &" > /dev/null 2>&1
sleep 1
echo "Receiver Activated"

docker compose exec -T python-processor sh -c "python3 /code/python-processor/main.py mitigation &"
sleep 1
echo "Processor Activated"

# Run benchmarks for each message length

# Global message ID
MSG_ID=1

for MSG_LEN in "${MESSAGE_LENGTHS[@]}"; do
    NUM_ITERATIONS=20
    echo "Running for message length: $MSG_LEN ($NUM_ITERATIONS iterations)"

    for CV in "${COVERT_OR_VISIBLE[@]}"; do
        echo "Running for message type: $CV"

        for ((i = 1; i <= NUM_ITERATIONS; i++)); do
            echo "  Sending message ID $MSG_ID (len=$MSG_LEN, type=$CV)"
            docker compose exec sec sh -c "python3 sender.py $MSG_LEN $CV $MSG_ID"
            MSG_ID=$((MSG_ID + 1))
            sleep 1
        done

        echo "-----------------------------------------------------"
    done
done

docker compose down --remove-orphans