#!/usr/bin/env python3
"""
Minimal Flask app to test if the basic setup works.
"""

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/test')
def test():
    return jsonify({"message": "Backend is working!", "status": "success"})

if __name__ == '__main__':
    print("🚀 Starting minimal test server...")
    print("🌐 Test endpoint: http://localhost:5000/test")
    app.run(host='localhost', port=5000, debug=True)
