from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import openai
import textract
import os
from werkzeug.utils import secure_filename
from textblob import TextBlob
from nltk.corpus import stopwords

app = Flask(__name__)
messages = []
openai.api_key = "YOUR_API_KEY"
app.config["UPLOAD_FOLDER"] = "AIConverse"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if "message" in request.form:
            # Handle text message
            message = request.form["message"]
            handle_text_message(message)
        elif "file" in request.files:
            # Handle file upload
            file = request.files["file"]
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            handle_file_upload(file_path)
    return render_template("chat.html", messages=messages)

def handle_text_message(message):
    messages.append({"sender": "User", "text": message})
    intent = understand_intent(message)
    prompt = f"I want to {intent}. {message}"
    response = generate_response(prompt)
    messages.append({"sender": "Bot", "text": response})

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
    generated_text += "\n\nThe AIConverse team\n(Powered by OpenAI)"
    return generated_text

def handle_file_upload(file_path):
    file_extension = os.path.splitext(file_path)[1]

    if file_extension == ".pdf":
        # Extract text from PDF
        text = extract_text_from_pdf(file_path)
    elif file_extension in [".jpg", ".jpeg", ".png"]:
        # Perform image processing and extract text from the image
        text = extract_text_from_image(file_path)
    else:
        # Handle other file types
        text = extract_text_from_file(file_path)

    messages.append({"sender": "User", "text": f"Uploaded file: {file_path}"})
    messages.append({"sender": "User", "text": text})

    intent = understand_intent(text)
    prompt = f"I want to {intent}. {text}"
    response = generate_response(prompt)
    messages.append({"sender": "Bot", "text": response})

def extract_text_from_pdf(file_path):
    text = textract.process(file_path)
    return text.decode("utf-8")

def extract_text_from_image(file_path):
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image)
    return text

def extract_text_from_file(file_path):
    file_extension = file_path.split(".")[-1]
    if file_extension == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_extension in ["jpg", "jpeg", "png"]:
        return extract_text_from_image(file_path)
    else:
        # Implement your own logic to extract text from other file types (e.g., docx, txt, etc.)
        return "Text extraction not supported for this file type."

# Example usage:
pdf_text = extract_text_from_file("example.pdf")
image_text = extract_text_from_file("example.jpg")
other_file_text = extract_text_from_file("example.docx")

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        input_text = request.form['input_text']
        conversation = request.form['conversation']

        messages.append({"sender": "User", "text": input_text})
        messages.append({"sender": "Bot", "text": conversation})

    return render_template('chat.html', messages=messages)

if __name__ == "__main__":
    app.run()

