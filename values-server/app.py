from flask import Flask, jsonify
import json
import os
import argparse

app = Flask(__name__)

VALUES_DIR = '/data/values'

@app.route('/<app_name>', methods=['GET'])
def get_values(app_name):
    """
    Get current configuration values for a given application
    
    Args:
        app_name: Name of the application (e.g., 'chat', 'matchmaking', 'tournament')
    
    Returns:
        200: JSON values
        404: Values not found
        500: Internal server error
    """
    try:

        filepath = os.path.join(VALUES_DIR, f'{app_name}.value.json')
        
        if not os.path.exists(filepath):
            return jsonify({'error': f'Values not found for application: {app_name}'}), 404
        
        with open(filepath, 'r') as f:
            values = json.load(f)
        
        return jsonify(values), 200
        
    except json.JSONDecodeError as e:
        return jsonify({'error': f'Invalid JSON in values file: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'values-service'}), 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Values Service')
    parser.add_argument('--values-dir', default='/data/values', help='Directory containing values files')
    parser.add_argument('--listen', default='0.0.0.0:5002', help='Host:Port to listen on')
    
    args = parser.parse_args()
    
    VALUES_DIR = args.values_dir

    host, port = args.listen.split(':')
    port = int(port)
    
    print(f"Starting Values Service on {host}:{port}")
    print(f"Values directory: {VALUES_DIR}")
    
    app.run(host=host, port=port, debug=False)