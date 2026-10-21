
# AI Vision Assistant

An experimental computer vision project exploring how AI can help visually impaired people understand their surroundings through audio feedback.

The program uses a camera to detect and track objects, read text, and respond to voice commands. It uses AI to generate short descriptions in Kazakh when an internet connection is available and switches to basic object announcements when offline.

## Features

- Object detection using two YOLO models (`yolo11x.pt` and `best.pt`)
- Object tracking across video frames
- Basic detection of approaching objects
- AI-generated descriptions in Kazakh using Groq
- Text recognition using EasyOCR
- Voice commands for controlling object detection and reading text
- Offline object announcements using translation and text-to-speech

## Technologies

- Python
- YOLO11
- OpenCV
- EasyOCR
- Groq API (Llama 3.3 70B)
- SpeechRecognition and Whisper
- Google Translator
- Windows Speech Synthesis
- best.pt

## Setup

Install the required libraries:

```bash
pip install ultralytics opencv-python deep-translator groq easyocr SpeechRecognition openai-whisper
```

Download the YOLO model weights and place them in the project directory alongside main.py:

yolo11x.pt - Download the pretrained model from the official Ultralytics YOLO11 documentation. You can also let Ultralytics download it automatically when the program first runs, provided you have an internet connection.

best.pt - An additional YOLO model that I used for detecting traffic-related objects, potentially including cars and traffic lights. This file is not included in the repository, and its original source and exact classes need to be verified.

Set your Groq API key in PowerShell:

```powershell
$env:GROQ_API_KEY="your_api_key_here"
```

Run the program:

```bash
python main.py
```

A working camera and microphone are required. The current speech output uses Windows PowerShell.

## Voice Commands

- `read` - reads text detected by the camera
- `turn on` = enables object detection
- `turn off` - disables object detection

## How It Works

The camera captures frames that are processed by two YOLO models. Detected objects are sent to Groq to generate short Kazakh descriptions when the internet is available. Without internet, the program translates object names and reads them aloud.

The program also compares bounding-box widths across frames to estimate whether an object is getting closer. This is only an approximation and does not provide accurate distance measurements.

The `read` command uses EasyOCR to recognize English and Russian text in the current camera frame.

## Limitations

This project is still a work in progress. Detection accuracy depends on the models and camera conditions. AI descriptions require an internet connection, and the offline mode provides simpler announcements. The system has not been validated as a reliable mobility aid.

## Future Improvements

- Improve obstacle detection and distance estimation, mainly by using better modules
- Make approaching-object warnings more reliable
- Explore integration with smart glasses and application
