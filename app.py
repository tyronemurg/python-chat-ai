from flask import Flask, request, jsonify, g
from flask_cors import CORS
import sqlite3
from openai import OpenAI

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# Initialize OpenAI API
client = OpenAI(api_key='Your_key')


# Function to get SQLite database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('chat.db')
    return db

# Create table if not exists
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Function to close SQLite database connection
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, '_database'):
        g._database.close()

# Route to send message to the chatbot
@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    user_message = data['message']

    # Get response from OpenAI
    response = client.chat.completions.create(
        messages=[{"role": "system", "content": user_message}],
        model="gpt-3.5-turbo",
        max_tokens=50
    )

    # Extract chatbot's response content
    chatbot_response_content = response.choices[0].message.content

    # Store user message and chatbot response as a single chat entry
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO chats (message) VALUES (?)", (user_message,))
    cursor.execute("INSERT INTO chats (message) VALUES (?)", (chatbot_response_content,))
    db.commit()

    # Create a JSON-serializable response
    response_data = {"message": chatbot_response_content}

    return jsonify(response_data)




# Route to get all chats from the database
@app.route('/get_chats', methods=['GET'])
def get_chats():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM chats")
    chats = cursor.fetchall()
    return jsonify({"chats": chats})

if __name__ == '__main__':
    app.run(debug=True)
