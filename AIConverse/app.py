from flask import Flask, render_template, request
from message_listener_layer import MessageListenerLayer
import openai
from werkzeug.utils import secure_filename
import textract
from flask import Flask, request, render_template
import os
from file_handler import handle_file_upload


app = Flask(__name__)
messages = []
openai.api_key = "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"

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if "message" in request.form:
            message = request.form["message"]
            messages.append({"sender": "User", "text": message})
            intent = understand_intent(message)
            prompt = f"I want to {intent}. {message}"
            response = generate_response(prompt)
            messages.append({"sender": "Bot", "text": response})
        elif "file" in request.files:
            # Handle file upload
            file = request.files["file"]
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            handle_file_upload(file_path)
    return render_template("chat.html", messages=messages)

def generate_response(prompt):
    prompt = f"Desire: {prompt}"
    response = openai.Completion.create(
        prompt=prompt,
        temperature=0.7,
        max_tokens=100,
        n=1,
        stop=None,
    )
    generated_text = response.choices[0].text
    generated_text += "\n\nThe Alien TV team\n(Powered by TEXT GENIUS)"
    return generated_text

def understand_intent(message):
    stop_words = stopwords.words("english")

    # Preprocessing
    words = message.lower().split()
    words = [word for word in words if word not in stop_words]
    message = " ".join(words)

    # Extract sentiment
    sentiment = TextBlob(message).sentiment.polarity

    # Return intent based on sentiment
    if sentiment > 0:
        return "praise"
    elif sentiment < 0:
        return "complain"
    else:
        return "request"
def create_app():
    app = Flask(__name__)
    
    # Set the upload folder path
    UPLOAD_FOLDER = "uploads"
    
    # Create the upload folder if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Set the upload folder configuration in Flask
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    
    # Routes and other configurations

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]

    if file:
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)

        # Call the handle_file_upload function from file_handler.py
        handle_file_upload(file_path, messages)

        return "File uploaded successfully"
    else:
        return "No file uploaded"

if __name__ == "__main__":
    stack = MessageListenerLayer()
    stack.start()
    app = create_app()
    app.run()

