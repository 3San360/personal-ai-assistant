from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:4200"])

@app.route('/api/v1/health/', methods=['GET'])
def health():
    return {"status": "ok", "message": "Personal AI Assistant API is running"}

@app.route('/api/v1/chat/message', methods=['POST'])
def chat():
    return {"message": "Chat endpoint is working", "response": "Hello! This is a test response."}

if __name__ == '__main__':
    print("🚀 Starting Personal AI Assistant API")
    print("🌐 Server: http://localhost:5000")
    print("📋 Available endpoints:")
    print("   • Health: http://localhost:5000/api/v1/health/")
    print("   • Chat: http://localhost:5000/api/v1/chat/message")
    app.run(host='localhost', port=5000, debug=True)
