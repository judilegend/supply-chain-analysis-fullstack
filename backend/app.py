from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from data_processor import process_supply_chain_data
import os

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')
CORS(app)

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'supply_chain_data.csv')

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    data = process_supply_chain_data(DATA_PATH)
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": "Data file not found"}), 404

# Serve Frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
