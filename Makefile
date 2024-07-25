.PHONY:
	pre-commit
	check-connector-plugins
	get-active-connectors
	get-connector-status
	get-connector-configuration
	remove-connector

.EXPORT_ALL_VARIABLES:
COMPOSE_FILE ?= ./docker-compose-kraft.yaml

# Docker commands
docker-build:
	docker-compose -f $(COMPOSE_FILE) up --build

docker-up:
	docker-compose -f $(COMPOSE_FILE) up --remove-orphans --force-recreate

docker-down:
	docker-compose -f $(COMPOSE_FILE) down

# Kafka Connect commands
check-connector-plugins:
	curl -s http://localhost:8083/connector-plugins | jq '.[].class'

get-active-connectors:
	curl -s http://localhost:8083/connectors | jq

get-connector-status:
	curl localhost:8083/connectors/$(CONNECTOR)/status | jq

get-connector-configuration:
	curl http://localhost:8083/connectors/$(CONNECTOR)/config | jq

delete-connector:
	curl -X DELETE http://localhost:8083/connectors/$(CONNECTOR)

# Run pre-commit
pre-commit:
	pre-commit run --all-files

# Run main.py file
pull-reports:
	python3 src/main.py
