from flask import *
from flask_socketio import SocketIO, join_room, leave_room, emit, send
import random
from string import ascii_uppercase
from deep_translator import *
from faster_whisper import WhisperModel
import base64
import io
import av
import numpy as np
import soundfile as sf
import speech_recognition as sr
import requests
from langdetect import detect
import langid

LANG_CODES = {"af":"Afrikaans","ar":"Arabic","az":"Azerbaijani","be":"Belarusian","bg":"Bulgarian","bn":"Bengali","bs":"Bosnian","ca":"Catalan","cs":"Czech","cy":"Welsh","da":"Danish","de":"German","el":"Greek","en":"English","eo":"Esperanto","es":"Spanish","et":"Estonian","fa":"Persian","fi":"Finnish","fr":"French","ga":"Irish","gl":"Galician","gu":"Gujarati","he":"Hebrew","hi":"Hindi","hr":"Croatian","ht":"Haitian Creole","hu":"Hungarian","hy":"Armenian","id":"Indonesian","is":"Icelandic","it":"Italian","ja":"Japanese","ka":"Georgian","kk":"Kazakh","km":"Khmer","kn":"Kannada","ko":"Korean","ku":"Kurdish","ky":"Kyrgyz","la":"Latin","lb":"Luxembourgish","lo":"Lao","lt":"Lithuanian","lv":"Latvian","mk":"Macedonian","ml":"Malayalam","mn":"Mongolian","mr":"Marathi","ms":"Malay","mt":"Maltese","ne":"Nepali","nl":"Dutch","no":"Norwegian","pa":"Punjabi","pl":"Polish","ps":"Pashto","pt":"Portuguese","ro":"Romanian","ru":"Russian","sd":"Sindhi","si":"Sinhala","sk":"Slovak","sl":"Slovenian","sq":"Albanian","sr":"Serbian","sv":"Swedish","sw":"Swahili","ta":"Tamil","te":"Telugu","th":"Thai","tl":"Tagalog","tr":"Turkish","uk":"Ukrainian","ur":"Urdu","uz":"Uzbek","vi":"Vietnamese","zh":"Chinese","zh-CN":"Chinese (Simplified)","zh-TW":"Chinese (Traditional)"}


app = Flask(__name__)
app.config['SECRET_KEY'] = 'bskajdbsujfhdkjshafjknskdjfn'
socketio = SocketIO(app, cors_allowed_origins="*")
model = WhisperModel("base", device="cpu")
r = sr.Recognizer

rooms = {}
user_sessions = {}

def generateRoomCode(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code

@app.route("/", methods=["GET", "POST"])
def home():
    session.clear()
    if request.method == "POST":
        user = request.form.get("user")
        room = request.form.get("room")
        lang = request.form.get("lang")
        join = request.form.get("join", False)
        create = request.form.get("create", False) 

        if not user:
            flash("Please enter a username.", "error")
            return render_template("home.html", room=room, user=user, lang=lang)
        
        if join != False and not room:
            flash("Please enter a room code to join.", "error")
            return render_template("home.html", room=room, user=user, lang=lang)
        
        if create != False:
            room = generateRoomCode(4)
            rooms[room] = {"members" : 0, "messages" : []}
        elif room not in rooms:
            flash("Room does not exist.", "error")
            return render_template("home.html", room=room, user=user, lang=lang)
        
        session["room"] = room
        session["user"] = user
        session["lang"] = lang
        print(f"language of session at index: {lang}")
        print(f"language recorded by session at index: {session.get('lang')}")

        flash(f"Welcome {user}! You have joined room {room}.", "success")
        return redirect(url_for("room"))
        
    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    user = session.get("user")
    lang = session.get("lang")
    print(f"language of session at room: lang")

    if not room or not user or room not in rooms:
        flash("Please join a room first.", "error")
        return redirect(url_for("home"))
    return render_template("room.html", lang=lang, room=room, messages=rooms[room]["messages"])

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    user = session.get("user")
    lang = session.get("lang")
    user_sessions[request.sid] = lang

    if not room or not user:
        return
    
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"user": user, "message": "has joined the room."}, to=room)
    rooms[room]["members"] += 1

    print(f"{user} connected to room {room}. Total members: {rooms[room]['members']}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    user = session.get("user")
    user_sessions.pop(request.sid, None)
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1

        if rooms[room]["members"] <= 0:
            del rooms[room]
            print(f"Room {room} deleted due to no members.")

    send({"user": user, "message": "has left the room."}, to=room)

@socketio.on("message")
def handle_message(data):
    room = session.get("room")
    user = session.get("user")
    lang = session.get("lang")
    print(data)
    print(data["data"])
   
    if not room or not user:
        return
    text = data["data"]
    lang = session.get("lang")
    source_lang = detect(text)
    sourceLang = langid.classify(text)
    
    sourceLangName = LANG_CODES[source_lang]
    langName = LANG_CODES[lang]

    for sid, lang in user_sessions.items():
        print(f"for user: {sid}, session language is: {lang}")
        try:
            translated = GoogleTranslator(source=source_lang, target=lang).translate(text)
            print(f"{sid} google translated text: {translated}")
        except:
            translated = MyMemoryTranslator(source=source_lang, target=lang).translate(text)
            print(f"{sid} memory translated text: {translated}")
        content = {"user": user, "message": translated}
        emit("messageSent", content, to=sid)
        rooms[room]["messages"].append(content)

    # print(text)
    # content = {"user": user, "message": text}
    # socketio.emit("messageSent", content, to=sid)
    # rooms[room]["messages"].append(content)
    # print(f"Message from {user} in room {room}: {data["data"]}")

# def translator(text):
#     lang = session.get("lang")
#     source_lang = detect(text)
#     sourceLang = langid.classify(text)
    
#     sourceLangName = LANG_CODES[source_lang]
#     langName = LANG_CODES[lang]

#     for sid, lang in user_sessions.items():
#         print(f"for user: {sid}, session language is: {lang}")
#         try:
#             translated = GoogleTranslator(source=source_lang, target=lang).translate(text)
#             print(f"{sid} google translated text: {translated}")
#         except:
#             translated = MyMemoryTranslator(source=source_lang, target=lang).translate(text)
#             print(f"{sid} memory translated text: {translated}")
#         emit("translated_message", {"translated": translated}, to=sid)
    # try:
    #     translated = GoogleTranslator(source=source_lang, target=lang).translate(text)
    # except:
    #     translated = MyMemoryTranslator(source=sourceLangName, target=langName).translate(text)
    # return translated

# def translate_libre(text, lang, source_lang):
#     url = "https://translate.argosopentech.com/translate"
#     payload = {
#         "q": text,
#         "source": source_lang,
#         "target": lang,
#         "format": "text"
#     }
#     try:
#         res = requests.post(url, json=payload, timeout=10)
#         res.raise_for_status()
#         return res.json().get("translatedText", "")
#     except Exception as e:
#         print("LibreTranslate error:", e)
#         return text
    
@socketio.on("recorded")
def hearMessage():
    with sr.Microphone as source:
        audio = r.listen(source)
    try:
        words = r.recognize_bing(audio)
        socketio.emit("recorded", words)
    except:
        print("nah twin")


if __name__ == "__main__":
    socketio.run(app, debug=True)