from ultralytics import YOLO
from deep_translator import GoogleTranslator
import cv2
import subprocess
import time
from groq import Groq
import easyocr
import threading
import socket
import os
import speech_recognition as sr

last_ai_call = 0
last_ai_call2 = 0
last_int_check = 0
last_spoken = {}
cache = {}
previous_boxes = {}
frame = None
detect_enabled = True
internet = False
frame_lock = threading.Lock()

model = YOLO("yolo11x.pt")
model2 = YOLO("best.pt")

print("YOLO11 loaded successfully!")

cap = cv2.VideoCapture(0)
reader = easyocr.Reader(["en", "ru"])
translator = GoogleTranslator(source="en", target="kk")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
recognizer = sr.Recognizer()


def listen_loop():
    global detect_enabled
    global frame

    while True:
        value = listen()
        print(value)

        if value is None:
            continue

        value = value.lower().strip()

        if value == "read":
            with frame_lock:
                current_frame = frame.copy() if frame is not None else None

            if current_frame is not None:
                texts = reader.readtext(current_frame)

                for text in texts:
                    readtext = text[1]

                    subprocess.Popen([
                        "powershell",
                        "-Command",
                        "Add-Type -AssemblyName System.Speech; "
                        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                        f'$s.Speak("{readtext}")'
                    ])

        elif value == "turn on":
            detect_enabled = True
            print("Detection ON")

        elif value == "turn off":
            detect_enabled = False
            print("Detection OFF")


def listen():
    try:
        with sr.Microphone() as source:
            audio_data = recognizer.listen(source)

        text = recognizer.recognize_whisper(
            audio_data,
            language="en"
        )

        return text

    except Exception as e:
        print(e)
        return None


def ask_ai(objects):
    prompt = f"""
You are a navigation assistant for a visually impaired person in Kazakhstan.
You receive a list of objects detected around them by a camera.
Your job is to return exactly ONE short sentence in Kazakh.

objects detected: {objects}

Rules:
- If there are dangerous objects (car, truck, bus, motorcycle, bicycle, person walking toward user) → warn about them first
- If there are navigation objects (chair, table, door, stairs) → mention them as obstacles
- If only basic objects (phone, bottle, plant) → briefly describe the surroundings: mostly there is an object, or there are object1, object2. Keep it in the same format
- Never mention: books, remote controls, potted plants, decorations
- Always respond in Kazakh
- Maximum 20 words
- Never return empty string
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Groq error:", e)
        return None


def check_int():
    try:
        socket.setdefaulttimeout(1)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("8.8.8.8", 53))

        return True

    except Exception:
        return False


def speak(item):
    if item not in cache:
        trans_item = translator.translate(item)
        cache[item] = trans_item
    else:
        trans_item = cache[item]

    try:
        subprocess.Popen([
            "powershell",
            "-Command",
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f'$s.Speak("{trans_item}")'
        ])

        last_spoken[item] = time.time()

    except Exception as e:
        print("Speech error:", e)


def speak_ai(response):
    if response is None:
        return

    response = response.strip()

    if not response:
        return

    try:
        response = response.replace('"', '`"')

        subprocess.Popen([
            "powershell",
            "-Command",
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f'$s.Speak("{response}")'
        ])

    except Exception as e:
        print("AI speech error:", e)


def moving(item):
    if item in last_spoken:
        if time.time() - last_spoken[item] >= 5:
            speak(item)
    else:
        speak(item)


threading.Thread(
    target=listen_loop,
    daemon=True
).start()

while True:
    ret, new_frame = cap.read()

    if not ret:
        print("Failed to read camera frame")
        continue

    with frame_lock:
        frame = new_frame.copy()

    if time.time() - last_int_check >= 1:
        internet = check_int()
        last_int_check = time.time()

    if detect_enabled:
        results = model.track(
            new_frame,
            persist=True,
            conf=0.5
        )

        results2 = model2.track(
            new_frame,
            persist=True,
            conf=0.5
        )

        for result2 in results2:
            objects2 = []

            for box2 in result2.boxes:
                if box2.id is None:
                    continue

                item2 = result2.names[int(box2.cls)]
                objects2.append(item2)

            if not objects2:
                continue

            if internet:
                if time.time() - last_ai_call2 >= 6:
                    response2 = ask_ai(objects2)

                    if response2:
                        speak_ai(response2)

                    last_ai_call2 = time.time()

            else:
                for item2 in objects2:
                    moving(item2)

        for result in results:
            objects = []

            for box in result.boxes:
                if box.id is None:
                    continue

                object_id = box.id.int().item()
                current_width = box.xywh[0][2].item()
                item = result.names[int(box.cls)]

                if object_id in previous_boxes:
                    if current_width >= previous_boxes[object_id] + 20:
                        item = f"approaching {item}"

                    previous_boxes[object_id] = current_width

                else:
                    previous_boxes[object_id] = current_width

                objects.append(item)

            if not objects:
                continue

            if internet:
                if time.time() - last_ai_call >= 8:
                    response = ask_ai(objects)

                    if response:
                        speak_ai(response)

                    last_ai_call = time.time()

            else:
                for item in objects:
                    moving(item)
