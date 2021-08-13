import os
from datetime import datetime
import boto3
from authlib.integrations.flask_client import OAuth
from bson import ObjectId
from flask import redirect, send_file, url_for
from flask import session
from pymongo import MongoClient
import numpy as np
from flask import Flask, request, render_template
import pickle
import math
from s3_demo import download_file, upload_file
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import GOOGLE_MAIL_PASSWORD as x

app = Flask(__name__)
app.secret_key = '!secret'
app.config.from_object('config')
title = "TODO"
heading = "TODO"
BUCKET = "youngly"
s3 = boto3.client('s3')

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth = OAuth(app)
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)

client = MongoClient("mongodb://127.0.0.1:27017")  # host uri
db = client.mymongodb  # Select the database
todos = db.todo  # Select the collection name
notes = db.note
voice = db.voice
image = db.image


def redirect_url():
    return request.args.get('next') or \
           request.referrer or \
           url_for('index')


@app.route("/list")
def lists():
    # Display the all Tasks
    useri = session.get('user')
    if useri:
        todos_l = todos.find({"user.email": useri['email']})
        notes_l = notes.find({"user.email": useri['email']})
    else:
        todos_l = todos.find()
        notes_l = notes.find()
    a1 = "active"
    return render_template('index.html', a1=a1, todos=todos_l, t=title, h=heading, user=useri, notes=notes_l)


@app.route("/diabetes")
def diabetes():
    useri = session.get('user')
    if useri:
        return render_template('diabetes.html')
    else:
        return render_template('need.html')


@app.route("/recipe")
def recipe():
    useri = session.get('user')
    if useri:
        return render_template('recipe.html')
    else:
        return render_template('need.html')


@app.route("/bmi")
def bmi():
    useri = session.get('user')
    if useri:
        return render_template('bmi.html')
    else:
        return render_template('need.html')


@app.route("/listn")
def listsn():
    # Display the all notes
    useri = session.get('user')
    if useri:
        todos_l = todos.find({"user.email": useri['email']})
        notes_l = notes.find({"user.email": useri['email']})
    else:
        todos_l = todos.find()
        notes_l = notes.find()
    a1 = "active"
    return render_template('index.html', a1=a1, t=title, todos=todos_l, h=heading, user=useri, notes=notes_l)


@app.route("/completed")
def completed():
    # Display the Completed Tasks
    useri = session.get('user')
    todos_l = todos.find({"done": "yes"})
    a3 = "active"
    return render_template('index.html', a3=a3, todos=todos_l, t=title, h=heading, user=useri)


@app.route("/done")
def done():
    # Done-or-not ICON
    id = request.values.get("_id")
    task = todos.find({"_id": ObjectId(id)})
    if task[0]["done"] == "yes":
        todos.update({"_id": ObjectId(id)}, {"$set": {"done": "no"}})
    else:
        todos.update({"_id": ObjectId(id)}, {"$set": {"done": "yes"}})
    redir = redirect_url()

    return redirect(redir)


@app.route("/action", methods=['POST'])
def action():
    # Adding a Task
    name = request.values.get("name")
    desc = request.values.get("desc")
    date = request.values.get("date")
    pr = request.values.get("pr")
    user = session.get('user')
    todos.insert({"name": name, "desc": desc, "date": date, "pr": pr, "done": "no", "user": user})
    return redirect("/list")


@app.route("/notestore", methods=['POST'])
def note():
    # Adding a Notes
    note = request.values.get("note")
    user = session.get('user')
    notes.insert({"note": note, "user": user})
    return redirect("/listn")


@app.route("/remove")
def remove():
    # Deleting a Task with various references
    key = request.values.get("_id")
    todos.remove({"_id": ObjectId(key)})
    return redirect("/")


@app.route("/remind")
def remind():
    # Deleting a Task with various references
    key = request.values.get("_id")
    x = todos.find({"_id": ObjectId(key)})
    s = "Hi "
    for doc in x:
        s = s + doc['user']['given_name'] + " task " + doc['name'] + " is added on " + doc['date']
        sender(s, doc['user']['email'])
    return redirect("/")


@app.route("/remindnote")
def remindn():
    # Deleting a Note with various references
    key = request.values.get("_id")
    x = notes.find({"_id": ObjectId(key)})
    s = "Hi "
    for doc in x:
        s = s + doc['user']['given_name'] + " note " + doc['note'] + " is added"
        sender(s, doc['user']['email'])
    return redirect("/")


def sender(mail_content, email):
    # The mail addresses and password
    mail_content = mail_content
    sender_address = 'satpathy.amrit@gmail.com'  # your mail id like abc@gmail.com
    sender_pass = x  # 16 digit 2 factor gmail password
    receiver_address = email  # mail id to send the mail
    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = 'task added'  # The subject line
    # The body and the attachments for the mail
    message.attach(MIMEText(mail_content, 'plain'))
    # Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
    session.starttls()  # enable security
    session.login(sender_address, sender_pass)  # login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()


@app.route("/removen")
def removen():
    # Deleting a note with various references
    key = request.values.get("_id")
    notes.remove({"_id": ObjectId(key)})
    return redirect("/")


@app.route("/update")
def update():
    # update task
    id = request.values.get("_id")
    useri = session.get('user')
    task = todos.find({"_id": ObjectId(id)})
    return render_template('update.html', tasks=task, h=heading, t=title, user=useri)


@app.route("/action3", methods=['POST'])
def action3():
    # Updating a Task with various references
    name = request.values.get("name")
    desc = request.values.get("desc")
    date = request.values.get("date")
    pr = request.values.get("pr")
    id = request.values.get("_id")
    todos.update({"_id": ObjectId(id)}, {'$set': {"name": name, "desc": desc, "date": date, "pr": pr}})
    return redirect("/")


@app.route("/search", methods=['GET'])
def search():
    # Searching a Task with various references
    useri = session.get('user')
    key = request.values.get("key")
    refer = request.values.get("refer")
    if key == "_id":
        todos_l = todos.find({refer: ObjectId(key)})
    else:
        todos_l = todos.find({refer: key})
    return render_template('searchlist.html', todos=todos_l, t=title, h=heading, user=useri)


@app.route('/', methods=['POST', 'GET'])
def homepage():
    useri = session.get('user')
    if request.method == "POST":
        f = request.files['audio_data']
        x = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        x = str(x)
        with open(x + ".wav", 'wb') as audio:
            f.save(audio)
        upload_file(f"{x + '.wav'}", BUCKET)
        voice.insert({"voicename": x + '.wav', "user": useri})
        os.remove(x + '.wav')
        print('file uploaded successfully')

        return render_template('storage.html', request="POST")
    else:
        if useri:
            todos_l = todos.find({"user.email": useri['email']})
            notes_l = notes.find({"user.email": useri['email']})
        else:
            todos_l = todos.find()
            notes_l = notes.find()
        a2 = "active"
        return render_template('index.html', a2=a2, todos=todos_l, t=title, h=heading, user=useri, notes=notes_l)


@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route('/auth')
def auth():
    token = oauth.google.authorize_access_token()
    user = oauth.google.parse_id_token(token)
    session['user'] = user
    return redirect('/')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return render_template('bye.html')


@app.route("/storage")
def storage():
    contents = []
    v = []
    useri = session.get('user')
    voice_l = voice.find({"user.email": useri['email']})
    for i in voice_l:
        v.append(i['voicename'])
    for key in s3.list_objects(Bucket='youngly')['Contents']:
        if key['Key'] in v:
            contents.append(key['Key'])
    return render_template('storage.html', user=useri, contents=contents)


@app.route("/upload", methods=['POST'])
def upload():
    useri = session.get('user')
    if request.method == "POST":
        f = request.files['file']
        f.save(f.filename)
        upload_file(f"{f.filename}", BUCKET)
        voice.insert({"voicename": f.filename, "user": useri})
        return redirect("/storage")


@app.route("/download/<filename>", methods=['GET'])
def download(filename):
    if request.method == 'GET':
        output = download_file(filename, BUCKET)

        return send_file(output, as_attachment=True)


@app.route("/storageimage")
def storagei():
    contents = []
    v = []
    useri = session.get('user')
    voice_l = voice.find({"user.email": useri['email']})
    for i in voice_l:
        v.append(i['imangeename'])
    for key in s3.list_objects(Bucket='youngly')['Contents']:
        if key['Key'] in v:
            contents.append(key['Key'])
    return render_template('storage.html', user=useri, contents=contents)


@app.route("/uploadi", methods=['POST'])
def uploadi():
    relationname = request.values.get("relationname")
    useri = session.get('user')
    if request.method == "POST":
        f = request.files['file']
        f.save(f.filename)
        upload_file(f"{f.filename}", BUCKET)
        image.insert({"voicename": f.filename, "user": useri, "relationname": relationname})
        return redirect("/storage")


@app.route('/p')
def home():
    return render_template('prediction.html')

@app.route('/pi')
def homed():
    return render_template('predictiond.html')


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


# Load the scaler
fp = open(r"static/models/scaler.bin", "rb")
scaler = pickle.load(fp)
fp.close()

# Load LinearSVM
fp = open(r"static/models/LinearSVM.bin", "rb")
model1 = pickle.load(fp)
fp.close()

# Load LogisticRegression
fp = open(r"static/models/LogisticRegression.bin", "rb")
model2 = pickle.load(fp)
fp.close()

model = pickle.load(open('static/models/model.pkl', 'rb'))


@app.route('/predict', methods=['POST'])
def predict():
    """
    For rendering results on HTML GUI
    """
    int_features = [[float(x) for x in request.form.values()]]
    final_features = scaler.transform(int_features)
    # output = model.predict(final_features)
    # Now convert linear svm's prediction to probability
    out1 = sigmoid(model1.decision_function(final_features))
    # Get prediction probability from logistic regression
    out2 = model2.predict_proba(final_features)[:, 1]

    # Their average is the final output probability
    final_output = np.mean((out1, out2), axis=0)
    # output = prediction.reshape(-1, 1)
    output = (str(round(final_output[0] * 100, 2)))
    return render_template('prediction.html', prediction_text='Chance of alzheimer disease {}%'.format(output))


@app.route('/predictd', methods=['POST'])
def predictd():
    int_features = [[float(x) for x in request.form.values()]]
    out1 = model.predict(int_features)
    if out1:
        return render_template('predictiond.html', prediction_text='You might have Diabetes')
    else:
        return render_template('predictiond.html', prediction_text='You might not have Diabetes')

if __name__ == '__main__':
    app.run(debug=True)
