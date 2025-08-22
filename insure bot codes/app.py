from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
import pyttsx3
import threading
import speech_recognition as sr
import ollama

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

client = MongoClient("mongodb://localhost:27017/")
db = client["insurebot"]
collection = db["chat_history"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/send_message", methods=["POST"])
def send_message():
    data = request.get_json()
    user_input = data.get("message")

    if not user_input:
        return jsonify({"response": "No message received."}), 400

    try:
        response = ollama.chat(
            model='llama3',
            messages=[{'role': 'user', 'content': user_input}]
        )
        bot_reply = response['message']['content']
    except Exception as e:
        print("🔥 Ollama API error:", e)
        return jsonify({"response": "⚠ AI generation failed."}), 500

    try:
        collection.insert_one({"user": user_input, "bot": bot_reply})
    except Exception as e:
        print("❌ MongoDB error:", e)

    return jsonify({"response": bot_reply})


@app.route("/api/listen_and_reply", methods=["POST"])
def listen_and_reply():
    recognizer = sr.Recognizer()

    # Try to find a working microphone
    mic = None
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        try:
            test_mic = sr.Microphone(device_index=index)
            with test_mic as test_source:
                recognizer.adjust_for_ambient_noise(test_source, duration=0.5)
            mic = sr.Microphone(device_index=index)
            print(f"✅ Using microphone index {index}: {name}")
            break
        except Exception as e:
            print(f"❌ Mic index {index} failed: {e}")

    if mic is None:
        return jsonify({"response": "❌ No working microphone found.", "spoken": ""})

    # Listen from working mic
    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("🎤 Listening...")
            audio = recognizer.listen(source, timeout=6)
            user_input = recognizer.recognize_google(audio)
            print("🗣 You said:", user_input)
    except sr.UnknownValueError:
        return jsonify({"response": "❌ Could not understand your voice.", "spoken": ""})
    except sr.RequestError:
        return jsonify({"response": "⚠ Speech recognition API error.", "spoken": ""})
    except Exception as e:
        print("🎙 Mic error while listening:", e)
        return jsonify({"response": "❌ Failed during microphone input.", "spoken": ""})

    # Get AI response using Ollama API
    try:
        response = ollama.chat(
            model='llama3',
            messages=[{'role': 'user', 'content': user_input}]
        )
        bot_reply = response['message']['content']
    except Exception as e:
        print("🔥 Ollama API error:", e)
        return jsonify({"response": "⚠ AI error occurred.", "spoken": user_input})

    # Save to MongoDB
    try:
        collection.insert_one({"user": user_input, "bot": bot_reply})
    except Exception as e:
        print("💾 DB insert error:", e)

    # Speak the reply
    try:
        def speak():
            engine = pyttsx3.init()
            engine.say(bot_reply)
            engine.runAndWait()
        threading.Thread(target=speak).start()
    except Exception as e:
        print("🔊 TTS error:", e)

    return jsonify({"response": bot_reply, "spoken": user_input})


@app.route("/api/get_history", methods=["GET"])
def get_history():
    messages = collection.find().sort("_id", -1).limit(20)
    return jsonify([{"user": msg.get("user", ""), "bot": msg.get("bot", "")} for msg in messages])

if __name__ == "__main__":
    app.run(debug=True)
