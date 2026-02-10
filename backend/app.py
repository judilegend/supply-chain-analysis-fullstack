from flask import Flask, jsonify
from flask_cors import CORS
from data_processor import process_supply_chain_data
import os

app = Flask(__name__)
CORS(app)

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'supply_chain_data.csv')

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    data = process_supply_chain_data(DATA_PATH)
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": "Data file not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
