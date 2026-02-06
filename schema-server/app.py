from flask import Flask, jsonify
import json
import os
import argparse

app = Flask(__name__)

SCHEMA_DIR = '/data/schemas'

@app.route('/<app_name>', methods=['GET'])
def get_schema(app_name):
    """
    Get JSON Schema for a given application
    
    Args:
        app_name: Name of the application (e.g., 'chat', 'matchmaking', 'tournament')
    
    Returns:
        200: JSON Schema
        404: Schema not found
        500: Internal server error
    """
    try:
        filepath = os.path.join(SCHEMA_DIR, f'{app_name}.schema.json')

        if not os.path.exists(filepath):
            return jsonify({'error': f'Schema not found for application: {app_name}'}), 404
        
        with open(filepath, 'r') as f:
            schema = json.load(f)
        
        return jsonify(schema), 200
        
    except json.JSONDecodeError as e:
        return jsonify({'error': f'Invalid JSON in schema file: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'schema-service'}), 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Schema Service')
    parser.add_argument('--schema-dir', default='/data/schemas', help='Directory containing schema files')
    parser.add_argument('--listen', default='0.0.0.0:5001', help='Host:Port to listen on')
    
    args = parser.parse_args()
    
    SCHEMA_DIR = args.schema_dir
    
    host, port = args.listen.split(':')
    port = int(port)
    
    print(f"Starting Schema Service on {host}:{port}")
    print(f"Schema directory: {SCHEMA_DIR}")
    
    app.run(host=host, port=port, debug=False)