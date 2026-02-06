# Internship Project Report: Design & Implementation

## Design Decisions
- **Microservices Isolation**: I separated the system into independent services (Bot, Schema, Values) to ensure high modularity and follow the "Separation of Concerns" principle.
- **Hybrid Identification**: To prevent LLM hallucinations (e.g., identifying "tournament" as "League of Legends"), I implemented a keyword-based identification logic as the primary layer, using the LLM only as a fallback.
- **Defensive Parsing**: I used regex patterns to extract JSON from LLM responses, ensuring the system remains robust even if the model adds conversational text.

## Challenges & Solutions
### 1. Hardware Constraints & Performance
- **Issue**: During the processing of large JSON files (like `tournament.value.json`), the local LLM (Llama 3.2) experienced timeouts and parsing errors ("Failed to apply configuration change").
- **Analysis**: This was identified as a hardware limitation where the system's RAM/CPU struggled to maintain the large context window required for deep nested JSON structures.
- **Solution**: I implemented a **"Targeted Patching"** strategy. Instead of asking the LLM to rewrite the entire file, the system asks for the specific JSON path and value, which significantly reduces the compute load and improves reliability.

### 2. Port Conflicts
- **Issue**: Docker failed to start Ollama due to port 11434 being bound by a local instance.
- **Solution**: Implemented troubleshooting steps to identify and stop background processes, ensuring a clean container environment.

## Trade-offs
- **Local vs. Cloud**: I chose a local LLM via Ollama to prioritize data privacy and zero cost, accepting the trade-off of slower response times compared to cloud-based APIs like GPT-4.