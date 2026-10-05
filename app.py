from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import speech_recognition as sr
import random
import string
import os
import google.generativeai as genai

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mood_music.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ---------- Database Models ----------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    mood_histories = db.relationship('MoodHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MoodHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood = db.Column(db.String(50), nullable=False)
    user_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- Mood Keywords ----------
mood_keywords = {
    "Happy": [
        "happy","joy","joyful","excited","fun","smile","great","awesome","amazing","love","cheerful","fantastic",
        "glad","delighted","thrilled","ecstatic","euphoric","elated","jubilant","merry","gleeful","content",
        "pleased","satisfied","optimistic","hopeful","enthusiastic","vibrant","lively","upbeat","bright","sunny",
        "celebration","party","dancing","laugh","laughter","wonderful","excellent","brilliant","spectacular","fabulous",
        "terrific","superb","magnificent","outstanding","remarkable","incredible","blessed","fortunate","lucky",
        "cheer","rejoice","glee","delight","bliss","happiness","elation","euphoria","jubilation","exhilaration",
        "radiant","shining","sparkling","colorful","rainbow","sunshine","summer","vacation","holiday","festive",
        "playful","joking","humorous","witty","charming","sweet","cute","adorable","beautiful","gorgeous",
        "wins","victory","triumph","achievement","success","accomplishment","praise","compliment","reward","prize"
    ],
    "Sad": [
        "sad","lonely","depressed","cry","broken","pain","miss","lost","hopeless","low",
        "melancholy","sorrowful","grief","heartbroken","devastated","miserable","gloomy","blue","downcast",
        "somber","tearful","wistful","pensive","forlorn","despondent","dejected","crushed","empty","numb",
        "tragedy","suffering","agony","misery","despair","anguish","torment","torture","burden","heavy",
        "darkness","night","winter","cold","storm","rain","tears","weeping","sobbing","crying",
        "goodbye","farewell","separation","divorce","breakup","loss","death","dying","gone","disappeared",
        "failure","defeat","rejection","abandonment","betrayal","disappointment","regret","guilt","shame","embarrassment",
        "isolated","alone","solitary","abandoned","neglected","forgotten","ignored","unwanted","unloved","hated",
        "sick","ill","injured","hurt","wounded","damaged","ruined","destroyed","broken","shattered"
    ],
    "Angry": [
        "angry","mad","furious","rage","annoyed","frustrated","hate","irritated",
        "outraged","enraged","infuriated","resentful","bitter","hostile","aggressive","violent","temper",
        "wrath","disgusted","livid","irate","incensed","provoked","antagonized","exasperated","indignant",
        "furious","outraged","enraged","infuriated","resentful","bitter","hostile","aggressive","violent","temper",
        "wrath","disgusted","livid","irate","incensed","provoked","antagonized","exasperated","indignant",
        "mad","insane","crazy","wild","berserk","uncontrollable","explosive","volatile","dangerous","threatening",
        "revenge","vengeance","justice","punishment","payback","retaliation","fight","battle","war","conflict",
        "argument","dispute","quarrel","fight","clash","confrontation","opposition","resistance","defiance","rebellion",
        "destroy","damage","break","smash","crush","kill","harm","hurt","injure","attack",
        "stupid","idiot","fool","dumb","ridiculous","absurd","nonsense","garbage","trash","disgusting"
    ],
    "Calm": [
        "calm","relaxed","relax","peaceful","peace","quiet","meditation","breathe","soothing",
        "serene","tranquil","composed","collected","centered","balanced","grounded","still","restful",
        "gentle","mellow","placid","harmonious","zen","repose","comfortable","at ease","untroubled",
        "meditation","mindfulness","contemplation","reflection","introspection","silence","stillness","serenity","tranquility","peacefulness",
        "nature","forest","ocean","beach","mountain","river","lake","sky","clouds","stars",
        "soft","smooth","warm","cozy","comfortable","safe","secure","protected","sheltered","hidden",
        "slow","steady","rhythmic","flowing","drifting","floating","gliding","sailing","wandering","roaming",
        "healing","recovery","restoration","renewal","rejuvenation","refreshment","revitalization","restoration","comfort","solace"
    ],
    "Neutral": [
        "neutral","okay","fine","normal","average","regular","standard","typical","ordinary",
        "balanced","stable","steady","consistent","moderate","middle","medium","fair","acceptable",
        "satisfactory","adequate","reasonable","calm","composed","unaffected","indifferent","impartial",
        "normal","usual","common","typical","standard","regular","average","ordinary","mediocre","so-so",
        "nothing","none","neither","nor","either","maybe","perhaps","possibly","probably","sometimes",
        "routine","daily","everyday","usual","habitual","customary","traditional","conventional","standard","normal",
        "boring","dull","uninteresting","plain","simple","basic","unremarkable","average","ordinary","commonplace",
        "waiting","watching","observing","seeing","looking","noticing","aware","conscious","alert","awake",
        "working","studying","reading","writing","learning","thinking","considering","pondering","reflecting","contemplating"
    ],
    "Anxious": [
        "anxious","worried","nervous","scared","fear","panic","stressed","overthinking",
        "tense","uneasy","apprehensive","restless","agitated","troubled","disturbed","concerned","afraid",
        "frightened","intimidated","overwhelmed","vulnerable","insecure","uncertain","doubtful","hesitant",
        "panic","terror","horror","nightmare","phobia","dread","apprehension","foreboding","premonition","anxiety",
        "sweating","shaking","trembling","tremor","palpitations","heartbeat","racing","pounding","throbbing","pulsing",
        "breathing","hyperventilating","choking","suffocating","drowning","trapped","stuck","cornered","helpless","powerless",
        "danger","threat","risk","peril","hazard","menace","warning","alarm","emergency","crisis",
        "failure","mistake","error","fault","blame","responsibility","pressure","expectation","deadline","exam",
        "crowd","people","social","public","speaking","presentation","performance","evaluation","judgment","criticism"
    ],
    "Motivated": [
        "motivated","inspired","confident","focus","goal","success","determined","energetic",
        "driven","ambitious","passionate","dedicated","committed","enthusiastic","empowered","strong",
        "powerful","ready","prepared","focused","disciplined","resilient","persistent","hardworking","productive",
        "champion","winner","victor","leader","pioneer","innovator","creator","builder","achiever","accomplisher",
        "power","strength","force","energy","vitality","stamina","endurance","courage","bravery","valor",
        "action","movement","progress","advancement","improvement","growth","development","evolution","transformation","change",
        "dream","vision","ambition","aspiration","purpose","mission","calling","destiny","fate","future",
        "exercise","training","practice","preparation","planning","strategy","tactics","method","approach","technique",
        "work","business","career","profession","job","task","project","assignment","duty","responsibility"
    ]
}

# ---------- Songs and Genres ----------
music_recommendations = {
    "Happy": {
        "genres": ["Pop", "Dance", "EDM"],
        "songs": [
            "Happy - Pharrell Williams",
            "Can't Stop the Feeling - Justin Timberlake", 
            "Uptown Funk - Mark Ronson ft. Bruno Mars",
            "Shake It Off - Taylor Swift",
            "Good as Hell - Lizzo"
        ]
    },
    "Sad": {
        "genres": ["Acoustic", "Piano", "Indie"],
        "songs": [
            "Someone Like You - Adele",
            "Mad World - Gary Jules",
            "Hurt - Johnny Cash",
            "Blackbird - The Beatles",
            "The Night We Met - Lord Huron"
        ]
    },
    "Angry": {
        "genres": ["Rock", "Rap", "Metal"],
        "songs": [
            "Killing in the Name - Rage Against the Machine",
            "Lose Yourself - Eminem",
            "Break Stuff - Limp Bizkit",
            "Stronger - Kanye West",
            "Bodies - Drowning Pool"
        ]
    },
    "Calm": {
        "genres": ["Classical", "Lo-fi", "Ambient"],
        "songs": [
            "Clair de Lune - Claude Debussy",
            "Weightless - Marconi Union",
            "River Flows in You - Yiruma",
            "Study Lo-fi Hip Hop Mix",
            "Spiegel im Spiegel - Arvo Pärt"
        ]
    },
    "Neutral": {
        "genres": ["Indie", "Soft Pop", "Alternative"],
        "songs": [
            "Ho Hey - The Lumineers",
            "Banana Pancakes - Jack Johnson",
            "Better Together - Jack Johnson",
            "Little Talks - Of Monsters and Men",
            "Home - Edward Sharpe & The Magnetic Zeros"
        ]
    },
    "Anxious": {
        "genres": ["Ambient", "Instrumental", "Meditation"],
        "songs": [
            "Ambient 1 - Brian Eno",
            "Weightless - Marconi Union",
            "Om Namo Bhagavate - Krishna Das",
            "Breathing Meditation - Calm",
            "Deep Focus - Spotify Playlist"
        ]
    },
    "Motivated": {
        "genres": ["Workout", "Hip-Hop", "EDM"],
        "songs": [
            "Eye of the Tiger - Survivor",
            "Lose Yourself - Eminem",
            "Till I Collapse - Eminem",
            "Thunder - Imagine Dragons",
            "Can't Hold Us - Macklemore & Ryan Lewis"
        ]
    }
}

# ---------- Functions ----------
def preprocess(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text

def get_music_files(mood):
    music_dir = os.path.join(os.path.dirname(__file__), 'music', mood)
    if os.path.exists(music_dir):
        music_files = [f for f in os.listdir(music_dir) if f.endswith(('.mp3', '.wav', '.ogg', '.m4a'))]
        return music_files
    return []

def detect_mood(text):
    text = preprocess(text)
    words = text.split()
    scores = {}
    
    # Calculate scores for each mood
    for mood, keywords in mood_keywords.items():
        score = 0
        keyword_matches = 0
        
        for keyword in keywords:
            # Check for exact word matches
            keyword_count = words.count(keyword)
            if keyword_count > 0:
                # Weight by keyword importance
                weight = 1 + (len(keyword) - 3) * 0.1 if len(keyword) > 3 else 1
                # Stronger weight for more specific emotions
                if mood in ["Happy", "Sad", "Angry"]:
                    weight *= 1.2
                elif mood in ["Anxious", "Motivated"]:
                    weight *= 1.1
                
                score += keyword_count * weight
                keyword_matches += keyword_count
                
            # Check for partial matches (for compound words)
            for word in words:
                if keyword in word and word != keyword:
                    partial_weight = 0.5
                    score += partial_weight
        
        # Bonus for multiple different keywords from same mood
        if keyword_matches >= 2:
            score *= 1.3
        elif keyword_matches >= 3:
            score *= 1.5
            
        scores[mood] = score
    
    # Find the best mood
    best_mood = max(scores, key=scores.get)
    best_score = scores[best_mood]
    
    # If no keywords found, return Neutral
    if best_score == 0:
        return "Neutral"
    
    # Calculate confidence metrics
    total_score = sum(scores.values())
    confidence_ratio = best_score / total_score if total_score > 0 else 0
    second_best = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
    
    # Strong confidence conditions
    if best_score >= 3:  # Strong evidence
        return best_mood
    elif confidence_ratio >= 0.4:  # Clear majority
        return best_mood
    elif best_score - second_best >= 1.5:  # Clear winner
        return best_mood
    
    # Moderate confidence - check for mood-specific patterns
    if best_score >= 1.5:
        # Prefer more specific moods over neutral when there's some evidence
        if best_mood != "Neutral" and scores["Neutral"] < best_score * 0.8:
            return best_mood
    
    # Low confidence - return Neutral
    return "Neutral"

# ---------- Gemini AI Configuration ----------
# Configure Gemini API
GEMINI_API_KEY = "AIzaSyBxC6EJWXv0g2tbfe30cB_YffZduRRalDc"
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")
genai.configure(api_key=GEMINI_API_KEY)

# Function to get a free model that supports generateContent
def get_available_model():
    try:
        models = genai.list_models()
        # Prioritize officially supported models for generateContent
        supported_models = [
            'models/gemini-2.5-flash',
            'models/gemini-2.5-flash-lite',
            'models/gemini-2.5-pro',
            'models/gemini-2.0-flash',
            'models/gemini-2.0-flash-lite'
        ]
        for model in models:
            if model.name in supported_models and 'generateContent' in model.supported_generation_methods:
                return model.name
        # Fallback to any model supporting generateContent
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                return model.name
        raise ValueError("No suitable model found that supports generateContent")
    except Exception as e:
        raise ValueError(f"Error listing models: {str(e)}")

def get_chatbot_response(user_message, user_mood=None):
    """Get response from Gemini AI chatbot"""
    try:
        model_name = get_available_model()
        model = genai.GenerativeModel(model_name)
        
        # Create context-aware prompt
        context_prompt = f"""
You are a helpful and empathetic AI assistant for a mood-based music recommendation app. 
Your role is to:
1. Provide emotional support and understanding
2. Suggest music based on the user's mood
3. Engage in friendly conversation
4. Offer positive encouragement

Current user mood: {user_mood if user_mood else 'Unknown'}
User message: {user_message}

Please provide a caring, supportive response that acknowledges their feelings and suggests appropriate music or activities. Keep your response conversational and warm (under 150 words).
"""
        
        response = model.generate_content(context_prompt)
        return response.text
    except Exception as e:
        return f"I'm having trouble connecting right now. Please try again later. Error: {str(e)}"

# ---------- Voice Recognition ----------
def listen_and_recognize():
    max_attempts = 3
    
    try:
        # Check if PyAudio is available
        try:
            import pyaudio
        except ImportError:
            return {"success": False, "error": "Voice recognition requires PyAudio. Please install it locally or use text input."}
        
        recognizer = sr.Recognizer()
        
        # Check for available microphones
        try:
            mics = sr.Microphone.list_microphone_names()
            if not mics:
                return {"success": False, "error": "No microphones found. Please check your microphone settings or use text input."}
        except:
            return {"success": False, "error": "Microphone access not available on this server. Please use text input."}
        
        print(f"Available microphones: {mics}")
        
        # Try multiple times for better recognition
        for attempt in range(max_attempts):
            try:
                # Use default microphone with optimized settings
                with sr.Microphone() as source:
                    print(f"Attempt {attempt + 1}/{max_attempts}: Listening... Please speak clearly.")
                    
                    # Better noise adjustment and sensitivity
                    recognizer.adjust_for_ambient_noise(source, duration=3)
                    recognizer.pause_threshold = 0.6  # Lower threshold for better sensitivity
                    recognizer.dynamic_energy_threshold = True
                    recognizer.operation_timeout = 0.5
                    
                    try:
                        print("Recording... Speak clearly into your microphone.")
                        audio = recognizer.listen(
                            source, 
                            timeout=8, 
                            phrase_time_limit=10,
                            snowboy_configuration=None
                        )
                        print("Audio captured successfully")
                        
                        # Try to recognize using Google's API with multiple attempts
                        try:
                            text = recognizer.recognize_google(audio)
                            print(f"Recognized text: '{text}'")
                            print(f"Text length: {len(text)} characters")
                            
                            # Validate recognized text
                            if text and len(text.strip()) > 0:
                                print(f" Valid text detected, returning success")
                                return {"success": True, "text": text}
                            else:
                                print(" Empty text detected, trying again...")
                                if attempt < max_attempts - 1:
                                    continue
                                else:
                                    return {"success": False, "error": "Speech not clear after multiple attempts. Please:\n1. Speak louder and clearer\n2. Reduce background noise\n3. Try typing instead"}
                                
                        except sr.RequestError as e:
                            print(f"Google API error: {str(e)}")
                            # Try alternative recognition method if Google fails
                            try:
                                text = recognizer.recognize_sphinx(audio)
                                print(f"Sphinx recognized text: '{text}'")
                                if text and len(text.strip()) > 0:
                                    return {"success": True, "text": text}
                                else:
                                    return {"success": False, "error": "Sphinx recognition failed. Please try again."}
                            except:
                                # If both methods fail, provide helpful error
                                return {"success": False, "error": "Speech recognition service unavailable. Please try again."}
                            
                    except sr.WaitTimeoutError:
                        print(f"Attempt {attempt + 1} timeout")
                        if attempt < max_attempts - 1:
                            print("Trying again...")
                            continue
                        else:
                            return {"success": False, "error": "Recording timeout. Please ensure you're speaking clearly and have microphone access."}
                            
            except sr.RequestError as e:
                return {"success": False, "error": f"Microphone access error: {str(e)}. Please check microphone permissions and restart app."}
                
    except ImportError as e:
        return {"success": False, "error": f"Missing dependencies: {str(e)}. Please install PyAudio: pip install PyAudio"}
    except OSError as e:
        return {"success": False, "error": f"Microphone hardware error: {str(e)}. Please check your microphone connection."}
    except Exception as e:
        return {"success": False, "error": f"Voice recognition error: {str(e)}"}

@app.route("/stop-recording", methods=["POST"])
@login_required
def stop_voice_recording():
    global stop_recording
    stop_recording = True
    return jsonify({"success": True, "message": "Recording stopped"})

# ---------- Routes ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "error")
    
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("signup.html")
        
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "error")
            return render_template("signup.html")
        
        if User.query.filter_by(email=email).first():
            flash("Email already exists", "error")
            return render_template("signup.html")
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for("login"))
        except:
            db.session.rollback()
            flash("Error creating account", "error")
    
    return render_template("signup.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("index"))

@app.route("/voice-input", methods=["POST"])
@login_required
def voice_input():
    try:
        print("🎤 Voice input request received")
        result = listen_and_recognize()
        print(f"Voice recognition result: {result}")
        
        if result["success"]:
            print(f"✅ Voice recognition successful: {result['text']}")
            # Analyze recognized text for mood
            mood = detect_mood(result["text"])
            print(f"🎭 Detected mood: {mood}")
            
            # Save mood history
            mood_history = MoodHistory(
                user_id=current_user.id,
                mood=mood,
                user_text=result["text"]
            )
            db.session.add(mood_history)
            try:
                db.session.commit()
                print("💾 Mood history saved successfully")
            except Exception as e:
                print(f"❌ Error saving mood history: {e}")
                db.session.rollback()
            
            # Get music recommendations
            songs = []
            music_files = []
            music_file_list = get_music_files(mood)
            if music_file_list:
                for file in music_file_list:
                    music_files.append(f"/music/{mood}/{file}")
                    songs.append(file)
            else:
                songs = music_recommendations[mood]["songs"]
                music_files = []
            
            genres = ", ".join(music_recommendations[mood]["genres"])
            print(f"🎵 Music recommendations prepared: {len(songs)} songs")
            
            response_data = {
                "success": True,
                "text": result["text"],
                "mood": mood,
                "songs": songs,
                "music_files": music_files,
                "genres": genres
            }
            print(f"📤 Sending response: {response_data}")
            return jsonify(response_data)
        else:
            print(f"❌ Voice recognition failed: {result['error']}")
            return jsonify(result)
    except Exception as e:
        print(f"💥 Voice input endpoint error: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/test-voice", methods=["GET"])
@login_required
def test_voice():
    """Test endpoint to check voice recognition setup"""
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        mics = sr.Microphone.list_microphone_names()
        
        return jsonify({
            "success": True,
            "microphones": mics,
            "speech_recognition_version": sr.__version__ if hasattr(sr, '__version__') else "Unknown"
        })
    except ImportError as e:
        return jsonify({
            "success": False,
            "error": f"SpeechRecognition not installed: {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Voice recognition test failed: {str(e)}"
        })

@app.route("/history")
@login_required
def history():
    mood_histories = MoodHistory.query.filter_by(user_id=current_user.id).order_by(MoodHistory.timestamp.desc()).all()
    return render_template("history.html", mood_histories=mood_histories)

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    mood = None
    songs = []
    music_files = []
    genres = None
    user_text = ""

    if request.method == "POST":
        user_text = request.form["text"]
        mood = detect_mood(user_text)
        
        # Save mood history for logged in user
        mood_history = MoodHistory(
            user_id=current_user.id,
            mood=mood,
            user_text=user_text
        )
        db.session.add(mood_history)
        try:
            db.session.commit()
        except:
            db.session.rollback()
        
        # Get actual music files from mood folder
        music_file_list = get_music_files(mood)
        if music_file_list:
            for file in music_file_list:
                music_files.append(f"/music/{mood}/{file}")
                songs.append(file)
        else:
            # Fallback to placeholder if no music files found
            songs = music_recommendations[mood]["songs"]
            music_files = []
        
        genres = ", ".join(music_recommendations[mood]["genres"])

    return render_template(
        "index.html",
        mood=mood,
        songs=songs,
        music_files=music_files,
        genres=genres,
        user_text=user_text
    )

@app.route("/chatbot", methods=["POST"])
@login_required
def chatbot():
    try:
        user_message = request.json.get("message", "").strip()
        
        if not user_message:
            return jsonify({
                "success": False,
                "error": "Message cannot be empty"
            })
        
        # Detect mood from user message for context
        user_mood = detect_mood(user_message)
        
        # Get chatbot response
        bot_response = get_chatbot_response(user_message, user_mood)
        
        return jsonify({
            "success": True,
            "response": bot_response,
            "detected_mood": user_mood
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Chatbot error: {str(e)}"
        })

@app.route("/music/<mood>/<filename>")
def serve_music(mood, filename):
    music_dir = os.path.join(os.path.dirname(__file__), 'music', mood)
    return send_from_directory(music_dir, filename)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
