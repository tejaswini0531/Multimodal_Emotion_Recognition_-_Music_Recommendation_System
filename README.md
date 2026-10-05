# Multimodal_Emotion_Recognition_&_Music_Recommendation_System

## 📌 Project Overview

Multimodal Emotion Recognition for Personalized Music Recommendation is an AI-based web application that detects a user's emotional state from text and speech input and recommends music according to the detected mood.

The system combines Natural Language Processing (NLP), Deep Learning, Speech-to-Text processing, and a web-based interface to provide personalized and mood-aware music recommendations.

## 🎯 Objectives

- Detect the emotional state of the user from text and speech.
- Convert speech input into text for emotion analysis.
- Classify the detected emotion into predefined emotion categories.
- Recommend music based on the detected mood.
- Provide a simple and interactive web interface.
- Maintain users' mood history for later reference.

## 😊 Supported Emotions

The system works with the following emotion categories:

- Happy
- Sad
- Angry
- Calm
- Neutral
- Anxious
- Motivated

## ✨ Key Features

### 1. User Registration and Login
Users can create an account and log in to access the application.

### 2. Text-Based Emotion Detection
Users can enter text describing their feelings. The system processes the text and predicts the corresponding emotion.

### 3. Speech Input
Users can provide their mood through voice input. The speech is converted into text before emotion analysis.

### 4. Emotion Recognition
The system processes the input using NLP and a deep learning-based emotion recognition approach.

### 5. Personalized Music Recommendation
After detecting the user's emotion, the system recommends songs that match the detected mood.

### 6. Mood History
The application maintains the user's previous mood detection records along with relevant information such as input and time.

### 7. Web Interface
The complete system is provided through a web-based interface for easy interaction.

## 🧠 System Workflow

```text
User
  |
  v
Text / Voice Input
  |
  v
Speech-to-Text
  |
  v
Text Preprocessing
  |
  v
NLP / Feature Representation
  |
  v
Deep Learning Emotion Classification
  |
  v
Detected Emotion
  |
  v
Mood-Based Music Recommendation
  |
  v
Recommended Songs


🔄 How the System Works
1. The user registers or logs into the application.
2. The user provides input through text or voice.
3. Voice input is converted into text.
4. The input is processed using NLP techniques.
5. The deep learning model analyzes the processed input.
6. The system predicts the user's emotional state.
7. The detected emotion is mapped to a suitable music category.
8. Songs related to the detected mood are recommended.
9. The user's mood information can be maintained in the history.

Project Structure
Multimodal_Emotion_Recognition_-_Music_Recommendation_System/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── render.yaml
├── .gitignore
├── README.md
│
├── static/
│
└── templates/
    ├── history.html
    ├── index.html
    ├── login.html
    └── signup.html

⚙️ Installation & Setup
1. Clone the Repository
git clone https://github.com/tejaswini0531/Multimodal_Emotion_Recognition_-_Music_Recommendation_System.git

2. Open the Project Folder
cd Multimodal_Emotion_Recognition_-_Music_Recommendation_System

3. Create a Virtual Environment
python -m venv .venv

4. Activate the Virtual Environment
For Windows:
.venv\Scripts\activate

5. Install Dependencies
pip install -r requirements.txt

6. Run the Application
python app.py

Then open the local URL displayed by Flask in your browser.

🔮 Future Enhancements
- Facial emotion recognition
- Support for more languages
- Improved speech recognition
- More emotion categories
- Larger music library
- Advanced personalized recommendation algorithms
- Cloud deployment
- Mobile application support
