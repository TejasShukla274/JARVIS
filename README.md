# 🤖 JARVIS AI Assistant

An advanced AI-powered desktop assistant inspired by Iron Man's JARVIS.
Built using Python, AI modules, computer vision, voice recognition, automation, and a futuristic GUI.

---

# ✨ Features

## 🎤 Voice Interaction

* Wake word detection
* Speech recognition
* Natural AI conversations
* Text-to-speech responses

## 🧠 AI Brain

* AI-powered command processing
* Memory system
* Context understanding
* Smart responses

## 👁️ Computer Vision

* Real-time camera vision
* Object detection using YOLOv8
* Vision memory system
* AI surveillance capabilities

## 🖥️ Futuristic GUI

* Reactive orb animation
* Audio visualizer
* Modern PyQt5 interface
* Dynamic GUI states

## 🌦️ Smart Services

* Weather updates
* News updates
* React Leaflet maps with cached place search
* Spotify integration
* App launching & automation

---

# 🛠️ Tech Stack

| Technology        | Purpose           |
| ----------------- | ----------------- |
| Python            | Core Backend      |
| PyQt5             | GUI               |
| YOLOv8            | Computer Vision   |
| OpenCV            | Camera Processing |
| SpeechRecognition | Voice Input       |
| pyttsx3           | Voice Output      |
| Torch             | AI Models         |
| Spotify API       | Music Control     |

---

# 📂 Project Structure

```bash
JARVIS/
│
├── brain/                 # AI logic & memory
├── commands/              # System commands
├── core/                  # Command handling
├── gui/                   # Futuristic GUI
├── memory/                # Persistent memory
├── music/                 # Spotify controller
├── services/              # Weather & news
├── vision/                # AI vision system
├── voice/                 # Voice input/output
│
├── main.py                # Main entry point
├── listener.py            # Wake listener
├── requirements.txt
└── README.md
```

---

# 🚀 Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/TejasShukla274/JARVIS.git
cd JARVIS
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

Activate environment:

### Windows

```bash
venv\Scripts\activate
```

---

## 3️⃣ Install Requirements

```bash
pip install -r requirements.txt
```

---

# ▶️ Run JARVIS

```bash
python main.py
```

---

# 🧩 Current Capabilities

✅ Voice assistant
✅ GUI assistant
✅ AI conversations
✅ Object detection
✅ Smart memory
✅ Cached maps for places
✅ App automation
✅ Music integration
✅ Weather services

---

# Maps

Ask JARVIS for a map with commands like:

```bash
jarvis show map of Delhi
jarvis where is Japan
jarvis locate Ayodhya
jarvis route from Greater Noida to Mumbai
jarvis smartest route from Ayodhya to Lucknow
jarvis show 3d map of Statue of Liberty
jarvis 4d route from Greater Noida to Mumbai
jarvis zoom in
jarvis zoom out
```

JARVIS opens a local React Leaflet map at `http://127.0.0.1:8765`.
Place searches are cached in `memory/map_cache.json`, and repeat searches are loaded from cache instead of calling the geocoding service again.
Routes are cached in `memory/route_cache.json`, and the map shows distance, estimated travel time, and an animated route line.
The default 2D map uses a dark futuristic basemap with city, country, and street label overlays. The 3D/4D modes use MapLibre with OpenFreeMap/OpenStreetMap vector building geometry where that locality has building data.

---

# 🔥 Future Plans

* Face recognition
* Home automation
* GPT memory upgrades
* Mobile integration
* Multi-agent AI system
* Emotion detection
* Full AI surveillance dashboard

---

# 📸 Screenshots

> Add screenshots of your GUI here

---

# ⚠️ Important Notes

* Do NOT upload `venv/`
* Keep AI model files outside GitHub if very large
* Python 3.11 recommended
* GPU recommended for YOLO

---

# 👨‍💻 Developer

### Tejas Shukla

🚀 B.Tech CSE Student
🤖 AI & Automation Enthusiast
🧠 Building real-world futuristic AI systems

GitHub:
https://github.com/TejasShukla274

---

# ⭐ Support

If you like this project:

⭐ Star the repository
🍴 Fork the repository
🛠️ Contribute improvements

---

# 📜 License

This project is for educational and personal development purposes.
