#!/bin/bash

export PYTHONPATH=$(dirname $(pwd))

echo "Starting 3 replicas of user_routing_service..."

uvicorn services.user_routing_service.src.main:app --host 0.0.0.0 --port 8080 --reload &
uvicorn services.user_routing_service.src.main:app --host 0.0.0.0 --port 8081 --reload &
uvicorn services.user_routing_service.src.main:app --host 0.0.0.0 --port 8082 --reload &

echo "Starting API Gateway on port 8000..."
uvicorn services.api_gateway_service.src.main:app --host 0.0.0.0 --port 8000 --reload