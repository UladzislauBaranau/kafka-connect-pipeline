#!/bin/bash

# Kafka Connect REST API endpoint
KC_REST_API='http://localhost:8083'

# Function to wait for Kafka Connect to start
wait_for_connect() {
    echo "Waiting for Kafka Connect to start listening on $KC_REST_API"
    while : ; do
        curl -s "$KC_REST_API/connectors" > /dev/null
        if [ $? -eq 0 ]; then
            echo "Kafka Connect is able to accept the requests"
            break
        fi

        echo "Kafka Connect is not yet ready"
        sleep 5
    done
}

# Function to apply connector configurations
apply_connector_config() {
    echo "Applying Kafka Connect config from $CONFIG_FILE"

    curl -X PUT -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        "$KC_REST_API/connectors/$CONNECTOR_NAME/config" \
        -d @"$CONFIG_FILE"

    if [ $? -eq 0 ]; then
        echo "Connector configuration applied successfully"
    else
        echo "Failed to apply connector configuration"
    fi
}

echo "Launching Kafka Connect worker and keep the container running"
/etc/confluent/docker/run &

# Apply first connector configuration
echo "Apply sink connector configuration"
CONNECTOR_NAME="sink-postgres-jdbc-connector"
CONFIG_FILE="/etc/kafka-connect/configs/sink-postgres-jdbc-connector.json"
wait_for_connect
apply_connector_config

# Apply second connector configuration
echo "Apply source connector configuration"
CONNECTOR_NAME="source-spooldir-csv-connector"
CONFIG_FILE="/etc/kafka-connect/configs/source-spooldir-csv-connector.json"
wait_for_connect
apply_connector_config

sleep infinity