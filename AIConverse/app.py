from flask import login_required, UserManager, UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, Length
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from user import User
from flask import Flask, render_template, request, session, redirect, url_for
from message_listener_layer import MessageListenerLayer
import openai
import magic
import pytesseract
from PIL import Image
import cv2
import random
from yowsup.layers import YowParallelLayer, YowLayerEvent
from yowsup.layers.auth import YowAuthenticationProtocolLayer
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers.protocol_messages import YowMessagesProtocolLayer
from yowsup.layers.protocol_receipts import YowReceiptProtocolLayer
from yowsup.layers.protocol_presence import YowPresenceProtocolLayer
from yowsup.layers.protocol_iq import YowIqProtocolLayer
from yowsup.layers.logger import YowLoggerLayer
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db


app = Flask(__name__)
messages = []
openai.api_key = "YOUR_API_KEY"
app.secret_key = 'your-secret-key'

login_manager = LoginManager(app)
login_manager.login_view = 'login'


app.config['USER_APP_NAME'] = 'File Analyzer'
app.config['USER_ENABLE_EMAIL'] = False
app.config['USER_ENABLE_USERNAME'] = True
app.config['USER_REQUIRE_RETYPE_PASSWORD'] = True
app.config['USER_ENABLE_REGISTRATION'] = True
app.config['USER_ENABLE_CHANGE_USERNAME'] = False
app.config['USER_ENABLE_CHANGE_PASSWORD'] = True
app.config['USER_ENABLE_CONFIRM_EMAIL'] = False
app.config['USER_SEND_PASSWORD_CHANGED_EMAIL'] = False
app.config['USER_SEND_REGISTERED_EMAIL'] = False
app.config['USER_LOGIN_TEMPLATE'] = 'login.html'
app.config['USER_REGISTER_TEMPLATE'] = 'register.html'

# Initialize the Flask-User extension
user_manager = UserManager(app, db, User)


class MessageListenerLayer(YowParallelLayer):
    def __init__(self):
        super(MessageListenerLayer, self).__init__()
        self.ackQueue = []

    def receive(self, event):
        if event.name == "message":
            self.onMessageEvent(event)

    def onMessageEvent(self, event):
        node = event.getFrom(False)
        if event.getType() == "text":
            incoming_message = event.getBody().lower().strip()
            intent = self.understand_intent(incoming_message)
            prompt = f"I want to {intent}. {incoming_message}"
            response = self.generate_response(prompt)
            outgoing_message = response.replace("\n", " ")

            outgoing_event = YowLayerEvent(
                YowMessagesProtocolLayer.EVENT_SEND_MESSAGE,
                (node, outgoing_message),
            )
            self.ackQueue.append(outgoing_event)
            self.broadcastEvent(outgoing_event)

    def generate_response(self, prompt):
        prompt = f"Desire: {prompt}"
        response = openai.Completion.create(
            prompt=prompt,
            temperature=0.7,
            max_tokens=100,
            n=1,
            stop=None,
        )
        generated_text = response.choices[0].text
        generated_text += "\nThe Alien TV team \n(Powered by TEXT GENIUS)"
        return generated_text

    def understand_intent(self, message):
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


message_listener = MessageListenerLayer()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    profile_picture = db.Column(db.String(120))
    social_media_profiles = db.Column(db.String(255))
    website_url = db.Column(db.String(255))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('Email already registered.')

    def validate_phone(self, field):
        user = User.query.filter_by(phone=field.data).first()
        if user:
            raise ValidationError('Phone number already registered.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        message = request.form["message"]
        messages.append({"sender": "User", "text": message})
        intent = understand_intent(message)
        prompt = f"I want to {intent}. {message}"
        response = generate_response(prompt)
        messages.append({"sender": "Bot", "text": response})
    if "file" in request.files:
        file = request.files["file"]
        if file:
            file_type = magic.from_buffer(file.stream.read(), mime=True)
            file.stream.seek(0)

            if file_type.startswith("image"):
                text = process_image(file)
            elif file_type == "application/pdf":
                text = process_pdf(file)
            else:
                return render_template("error.html", error="Unsupported file type.")

            messages.append({"sender": "User", "text": file.filename})
            messages.append({"sender": "Bot", "text": text})
        else:
            message = request.form["message"]
            messages.append({"sender": "User", "text": message})
            intent = understand_intent(message)
            prompt = f"I want to {intent}. {message}"
            response = generate_response(prompt)
            messages.append({"sender": "Bot", "text": response})

    return render_template("index.html", messages=messages)


def process_image(file):
    image = Image.open(file)
    text = pytesseract.image_to_string(image)
    response = {"type": "text", "content": text}
    if random.random() < 0.2:
        response["type"] = "image"
        response["content"] = get_random_image()
    return response


def process_pdf(file):
    text = ""
    pdf = PyPDF2.PdfFileReader(file)
    for page_num in range(pdf.getNumPages()):
        page = pdf.getPage(page_num)
        text += page.extract_text()
    return {"type": "text", "content": text}


def get_random_image():
    width, height = 500, 300
    image = Image.new("RGB", (width, height), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    return image


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
    generated_text += "\nThe Allien TV team \n(Powered by TEXT GENIUS)"
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


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(email=form.email.data, phone=form.phone.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password.')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('profile'))

    return render_template('login.html', form=form)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


if __name__ == "__main__":
    stack = MessageListenerLayer()
    stack.start()
    app.run()
