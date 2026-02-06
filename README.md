# AI-Assisted Configuration Management System

This project is a microservices-based system designed to manage application configurations using natural language through a local LLM (Llama 3.2).

## Architecture
The system consists of four main components:
- **Bot Service**: The brain of the system. It interprets user input, coordinates data from other services, and applies changes via LLM.
- **Schema Service**: Serves the JSON schemas that define the structure and constraints of configurations.
- **Values Service**: Serves the current configuration values for different services.
- **Ollama**: Runs the local Llama 3.2 model for natural language processing.

## Getting Started
1. Ensure you have Docker and Docker Compose installed.
2. Close any local Ollama instances (check system tray) to avoid port conflicts.
3. Run the system:
   ```bash
   docker compose up --build