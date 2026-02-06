from flask import Flask, request, jsonify
import requests
import json
import argparse
import time
import re

app = Flask(__name__)

SCHEMA_SERVICE_URL = 'http://schema-service:5001'
VALUES_SERVICE_URL = 'http://values-service:5002'
OLLAMA_URL = 'http://ollama:11434'

def wait_for_ollama(max_retries=30, delay=2):
    """Wait for Ollama service to be ready"""
    print("Waiting for Ollama service to be ready...")
    for i in range(max_retries):
        try:
            response = requests.get(f'{OLLAMA_URL}/api/tags', timeout=5)
            if response.status_code == 200:
                print("Ollama service is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if i < max_retries - 1:
            print(f"Ollama not ready yet, retrying in {delay} seconds... ({i+1}/{max_retries})")
            time.sleep(delay)
    
    print("WARNING: Ollama service did not become ready in time")
    return False

def ensure_model_pulled(model_name='llama3.2'):
    """Ensure the LLM model is pulled and ready"""
    print(f"Checking if model '{model_name}' is available...")
    
    try:
        response = requests.get(f'{OLLAMA_URL}/api/tags', timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_exists = any(model_name in model.get('name', '') for model in models)
            
            if model_exists:
                print(f"Model '{model_name}' is already available")
                return True
        
        print(f"Pulling model '{model_name}'... This may take a few minutes...")
        pull_response = requests.post(
            f'{OLLAMA_URL}/api/pull',
            json={'name': model_name},
            stream=True,
            timeout=600
        )
        
        for line in pull_response.iter_lines():
            if line:
                data = json.loads(line)
                status = data.get('status', '')
                if 'progress' in data:
                    print(f"  {status}: {data['progress']}")
                elif status:
                    print(f"  {status}")
        
        print(f"Model '{model_name}' is ready!")
        return True
        
    except Exception as e:
        print(f"Error ensuring model is available: {e}")
        return False

def identify_application(user_input):
    """
    Use LLM to identify which application the user wants to modify
    
    Args:
        user_input: Natural language user request
    
    Returns:
        Application name (chat, matchmaking, or tournament) or None
    """
    user_lower = user_input.lower()
    
    if 'tournament' in user_lower:
        print(f"Identified application via keyword: tournament")
        return 'tournament'
    elif 'matchmaking' in user_lower:
        print(f"Identified application via keyword: matchmaking")
        return 'matchmaking'
    elif 'chat' in user_lower:
        print(f"Identified application via keyword: chat")
        return 'chat'
    
    print("No keyword match, using LLM for identification...")
    
    prompt = f"""Identify the application from this request. Only respond with one word: chat, matchmaking, or tournament.

Request: {user_input}

Answer (one word only):"""

    try:
        response = requests.post(
            f'{OLLAMA_URL}/api/generate',
            json={
                'model': 'llama3.2',
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.0,
                    'num_predict': 10
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            app_name = result.get('response', '').strip().lower()
            
            app_name = re.sub(r'[^a-z]', '', app_name)
            
            if 'tournament' in app_name:
                print(f"LLM identified: tournament")
                return 'tournament'
            elif 'matchmaking' in app_name:
                print(f"LLM identified: matchmaking")
                return 'matchmaking'
            elif 'chat' in app_name:
                print(f"LLM identified: chat")
                return 'chat'
            
            print(f"Could not identify application from LLM response: '{app_name}'")
            return None
        else:
            print(f"Error from Ollama: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error identifying application: {e}")
        return None

def apply_configuration_change(user_input, schema, current_values):
    """
    Use LLM to apply configuration changes to the values JSON
    
    Args:
        user_input: Natural language user request
        schema: JSON Schema for the application
        current_values: Current configuration values
    
    Returns:
        Updated values JSON or None
    """
    prompt = f"""You are a configuration management assistant. Your task is to modify a JSON configuration based on a user's natural language request.

User request: "{user_input}"

Current configuration (JSON):
{json.dumps(current_values, indent=2)}

JSON Schema (for validation):
{json.dumps(schema, indent=2)}

Instructions:
1. Understand the user's request and identify what needs to be changed
2. Apply ONLY the requested change to the current configuration
3. Keep ALL other fields unchanged
4. Ensure the modified JSON is valid and follows the schema
5. Respond with ONLY the complete modified JSON, no explanations or markdown

Common patterns:
- "set X memory to Y" → modify resources.memory.limitMiB or requestMiB
- "set X cpu to Y" → modify resources.cpu.limitMilliCPU or requestMilliCPU  
- "set X env to Y" → modify envs object
- "lower/increase X by Y%" → calculate new value based on percentage

Modified JSON:"""

    try:
        response = requests.post(
            f'{OLLAMA_URL}/api/generate',
            json={
                'model': 'llama3.2',
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.1,
                    'num_predict': 4096
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            json_response = result.get('response', '').strip()
            
            start_idx = json_response.find('{')
            end_idx = json_response.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = json_response[start_idx:end_idx+1]
                
                updated_values = json.loads(json_str)
                print("Successfully parsed updated configuration")
                return updated_values
            else:
                print("Could not find valid JSON in LLM response")
                return None
                
        else:
            print(f"Error from Ollama: {response.status_code}")
            return None
            
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from LLM response: {e}")
        print(f"Response was: {json_response[:500]}")
        return None
    except Exception as e:
        print(f"Error applying configuration change: {e}")
        return None

@app.route('/message', methods=['POST'])
def handle_message():
    """
    Handle user message and return updated configuration
    
    Request body:
        {"input": "natural language request"}
    
    Returns:
        200: Updated configuration JSON
        400: Bad request
        404: Application not found
        500: Internal server error
    """
    try:
        data = request.get_json()
        if not data or 'input' not in data:
            return jsonify({'error': 'Missing "input" field in request'}), 400
        
        user_input = data['input']
        print(f"\n=== Processing request: {user_input} ===")
        
        app_name = identify_application(user_input)
        if not app_name:
            return jsonify({
                'error': 'Could not identify application from request',
                'hint': 'Please mention one of: chat, matchmaking, or tournament'
            }), 400
        
        print(f"Fetching schema for {app_name}...")
        schema_response = requests.get(f'{SCHEMA_SERVICE_URL}/{app_name}', timeout=10)
        if schema_response.status_code != 200:
            return jsonify({
                'error': f'Could not fetch schema for {app_name}',
                'details': schema_response.json()
            }), 404
        
        schema = schema_response.json()
        
        print(f"Fetching current values for {app_name}...")
        values_response = requests.get(f'{VALUES_SERVICE_URL}/{app_name}', timeout=10)
        if values_response.status_code != 200:
            return jsonify({
                'error': f'Could not fetch values for {app_name}',
                'details': values_response.json()
            }), 404
        
        current_values = values_response.json()
    
        print("Applying configuration change...")
        updated_values = apply_configuration_change(user_input, schema, current_values)
        
        if not updated_values:
            return jsonify({
                'error': 'Failed to apply configuration change',
                'hint': 'The LLM could not parse or apply your request'
            }), 500
        
        print("Configuration updated successfully!")
        return jsonify(updated_values), 200
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Service communication error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'bot-service'}), 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bot Service')
    parser.add_argument('--listen', default='0.0.0.0:5003', help='Host:Port to listen on')
    
    args = parser.parse_args()
    
    host, port = args.listen.split(':')
    port = int(port)
    
    print(f"Starting Bot Service on {host}:{port}")

    if wait_for_ollama():
        ensure_model_pulled('llama3.2')
    
    app.run(host=host, port=port, debug=False)