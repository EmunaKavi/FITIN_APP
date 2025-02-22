import streamlit as st
import pandas as pd
import numpy as np
import groq
import joblib
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import datetime
import PyPDF2
import pyttsx3
import tempfile
from io import BytesIO
from googleapiclient.discovery import build
import shutil  # for checking if eSpeak exists
from gtts import gTTS  # fallback TTS engine

# Set your Groq API key
api_key = "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"
# Set your YouTube API key here
YOUTUBE_API_KEY = "AIzaSyCg4MsfEezpeMY8QZ78WDDFqaQZv-keNxc"

# Load trained model
model_path = "Model/workout_recommender.pkl"
if os.path.exists(model_path):
    model = joblib.load(model_path)
else:
    st.error("Error: Model file not found!")

def calculate_bmi_bfp_category(weight, height, age, gender):
    bmi = weight / (height ** 2)
    if gender == "Male":
        bfp = (1.20 * bmi) + (0.23 * age) - 16.2
    else:
        bfp = (1.20 * bmi) + (0.23 * age) - 5.4

    if bmi < 16:
        bmi_category = "Severe Thinness"
    elif 16 <= bmi < 17:
        bmi_category = "Moderate Thinness"
    elif 17 <= bmi < 18.5:
        bmi_category = "Mild Thinness"
    elif 18.5 <= bmi < 25:
        bmi_category = "Normal"
    elif 25 <= bmi < 30:
        bmi_category = "Overweight"
    elif 30 <= bmi < 35:
        bmi_category = "Obese"
    else:
        bmi_category = "Severe Obese"
    return round(bmi, 2), round(bfp, 2), bmi_category

def generate_workout(plan_id, fitness_goal, workout_type, intensity, hypertension, disability, diabetes, training_focus):
    client = groq.Client(api_key=api_key)
    if intensity.lower() == "beginner":
        workout_description = (f"a workout plan with one exercise per day, designed for beginners, including at least one rest day per week, "
                               f"with a focus on {training_focus}")
    else:
        workout_description = f"a {intensity} level workout plan with a focus on {training_focus}"
    prompt = f"""Generate a detailed workout plan with {workout_description} for a user assigned to exercise plan {plan_id}. 
The user prefers {workout_type} workouts, has a fitness goal of {fitness_goal}, and has the following considerations: 
Hypertension = {hypertension}, Disability = {disability}, Diabetes = {diabetes}. Ensure exercises are safe and suitable."""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a fitness expert."},
            {"role": "user", "content": prompt},
        ]
    )
    return response.choices[0].message.content

def generate_diet_plan(bmi, bfp, bmi_category, fitness_goal, diabetes):
    client = groq.Client(api_key=api_key)
    prompt = f"""Generate a detailed diet and meal plan for a user with a BMI of {bmi} and a Body Fat Percentage of {bfp} ({bmi_category} category), 
with a fitness goal of {fitness_goal}. The user has diabetes = {diabetes}. Provide balanced meal recommendations, including calorie guidelines and recipes for breakfast, lunch, dinner, and snacks. 
Ensure the diet plan is nutritionally balanced and aligns with the user's fitness goal."""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a nutrition expert."},
            {"role": "user", "content": prompt},
        ]
    )
    return response.choices[0].message.content

def save_pdf(filename, user_data, workout_plan, diet_plan=None, video_url=None):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, "🏋️ AI Personal Workout & Diet Plan")
    c.line(100, 745, 500, 745)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 720, "📌 User Information:")
    c.setFont("Helvetica", 12)
    y = 700
    for key, value in user_data.items():
        c.drawString(100, y, f"• {key}: {value}")
        y -= 20

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "🏋️ Workout Plan:")
    y -= 30
    c.setFont("Helvetica", 12)
    max_width = 400
    for line in workout_plan.split("\n"):
        if "**" in line:
            c.setFont("Helvetica-Bold", 12)
            line = line.replace("**", "")
        elif "*" in line:
            c.setFont("Helvetica", 12)
            line = "• " + line.replace("*", "")
        elif "+" in line:
            c.setFont("Helvetica", 11)
            line = "   ◦ " + line.replace("+", "")
        wrapped_lines = simpleSplit(line, "Helvetica", 12, max_width)
        for wrapped_line in wrapped_lines:
            c.drawString(100, y, wrapped_line)
            y -= 20
            if y < 100:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 750

    if diet_plan:
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, y, "🍏 Diet & Meal Plan:")
        y -= 30
        c.setFont("Helvetica", 12)
        for line in diet_plan.split("\n"):
            if "**" in line:
                c.setFont("Helvetica-Bold", 12)
                line = line.replace("**", "")
            elif "*" in line:
                c.setFont("Helvetica", 12)
                line = "• " + line.replace("*", "")
            elif "+" in line:
                c.setFont("Helvetica", 11)
                line = "   ◦ " + line.replace("+", "")
            wrapped_lines = simpleSplit(line, "Helvetica", 12, max_width)
            for wrapped_line in wrapped_lines:
                c.drawString(100, y, wrapped_line)
                y -= 20
                if y < 100:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = 750

    if video_url:
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, y, "Exercise Video:")
        y -= 20
        link_text = "Click here to watch the exercise video"
        c.setFillColorRGB(0, 0, 1)
        c.drawString(100, y, link_text)
        text_width = c.stringWidth(link_text, "Helvetica", 12)
        c.linkURL(video_url, (100, y, 100 + text_width, y + 12), relative=0)
        c.setFillColorRGB(0, 0, 0)
        y -= 30

    thankyou_img_path = "thankyou.jpg"
    if os.path.exists(thankyou_img_path):
        c.drawImage(thankyou_img_path, 100, y - 150, width=300, height=150, preserveAspectRatio=True, mask="auto")
    
    c.save()

def text_to_speech(text):
    if not text:
        st.error("No text available for conversion.")
        return None, None
    # If eSpeak is available, try pyttsx3 first; otherwise, use gTTS.
    if shutil.which("espeak") is not None:
        try:
            engine = pyttsx3.init()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_filename = temp_file.name
            engine.save_to_file(text, temp_filename)
            engine.runAndWait()
            with open(temp_filename, "rb") as audio_file:
                audio_data = audio_file.read()
            os.remove(temp_filename)
            return audio_data, "audio/wav"
        except Exception as e:
            st.info("pyttsx3 conversion failed. Falling back to gTTS.")
    try:
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_filename = temp_file.name
        tts.save(temp_filename)
        with open(temp_filename, "rb") as audio_file:
            audio_data = audio_file.read()
        os.remove(temp_filename)
        return audio_data, "audio/mp3"
    except Exception as e:
        st.error("Text-to-speech conversion failed using gTTS.")
        st.error(str(e))
        return None, None

def get_youtube_video(query):
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=1
        )
        response = request.execute()
        items = response.get("items")
        if items:
            video_id = items[0]["id"]["videoId"]
            return f"https://www.youtube.com/watch?v={video_id}"
        else:
            return None
    except Exception as e:
        st.error("YouTube search failed.")
        st.error(str(e))
        return None

# Initialize session state for generated texts and audio
if "workout_text" not in st.session_state:
    st.session_state["workout_text"] = ""
if "diet_text" not in st.session_state:
    st.session_state["diet_text"] = ""
if "audio_buffer" not in st.session_state:
    st.session_state["audio_buffer"] = None

st.title("🏆 AI Personal Workout, Diet, Audio & Video Plan Recommender")

# User inputs with added symbols for better visual cues
weight = st.number_input("Enter your weight (kg) ⚖️:", min_value=30.0, max_value=200.0, step=0.1)
height = st.number_input("Enter your height (m) 📏📐:", min_value=1.0, max_value=2.5, step=0.01)
dob = st.date_input("Enter your Date of Birth (YYYY-MM-DD) 📅:", min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today())
today = datetime.date.today()
age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
gender = st.selectbox("Select your gender 👤:", ["Male", "Female"])
fitness_goal = st.text_input("Enter your fitness goal 🎯 (e.g., weight loss, muscle gain):")
workout_type = st.selectbox("Select your preferred workout type 🏋️:", ["Gym", "Home", "Bodyweight"])
intensity = st.selectbox("Select workout intensity 🔥:", ["Beginner", "Intermediate", "Advanced"])
hypertension = st.radio("Do you have hypertension 💓?", ["Yes", "No"])
disability = st.radio("Do you have any disabilities ♿?", ["Yes", "No"])
diabetes = st.radio("Do you have diabetes 🩺?", ["Yes", "No"])
mother_tongue = st.selectbox("Select your mother tongue 🗣️:", ["English", "Spanish", "Hindi", "French", "German", "Other"])
training_focus = st.selectbox("Select your training focus 💪:", ["Strength", "Stamina", "Power", "Flexibility", "Balance", "Endurance"])

if st.button("Get Workout, Diet & Audio Plan"):
    bmi, bfp, bmi_category = calculate_bmi_bfp_category(weight, height, age, gender)
    st.subheader("Your Fitness Analysis:")
    st.write(f"**BMI:** {bmi}")
    st.write(f"**Body Fat Percentage (BFP):** {bfp}")
    st.write(f"**BMI Category:** {bmi_category}")
    
    input_data = np.array([[weight, height, bmi, bfp, 0 if gender == "Male" else 1, age, 4]])
    predicted_plan = model.predict(input_data)[0]
    personalized_workout = generate_workout(predicted_plan, fitness_goal, workout_type, intensity, hypertension, disability, diabetes, training_focus)
    st.subheader("Your Personalized Workout Plan:")
    st.write(personalized_workout)
    
    personalized_diet = generate_diet_plan(bmi, bfp, bmi_category, fitness_goal, diabetes)
    st.subheader("Your Personalized Diet & Meal Plan:")
    st.write(personalized_diet)
    
    st.session_state["workout_text"] = personalized_workout
    st.session_state["diet_text"] = personalized_diet
    
    user_info = {
        "Weight (kg)": weight,
        "Height (m)": height,
        "Age": age,
        "Gender": gender,
        "BMI": bmi,
        "BFP": bfp,
        "BMI Category": bmi_category,
        "Workout Type": workout_type,
        "Intensity Level": intensity,
        "Hypertension": hypertension,
        "Disability": disability,
        "Diabetes": diabetes,
        "Fitness Goal": fitness_goal,
        "Mother Tongue": mother_tongue,
        "Training Focus": training_focus,
    }
    query = f"{fitness_goal} {workout_type} exercise workout in {mother_tongue} with a focus on {training_focus}"
    video_url = get_youtube_video(query)
    
    pdf_filename = "Workout_Diet_Audio_Plan.pdf"
    save_pdf(pdf_filename, user_info, personalized_workout, personalized_diet, video_url)
    
    with open(pdf_filename, "rb") as pdf_file:
        st.download_button(label="Download Your Plan as PDF", data=pdf_file, file_name=pdf_filename, mime="application/pdf")
    
    if video_url:
        st.video(video_url)
    else:
        st.write("No exercise video found.")

if st.button("Read Generated Text Aloud"):
    combined_text = st.session_state["workout_text"] + "\n\n" + st.session_state["diet_text"]
    audio_data, mime_type = text_to_speech(combined_text)
    if audio_data is not None:
        st.session_state["audio_buffer"] = (audio_data, mime_type)

if st.session_state["audio_buffer"] is not None:
    audio_data, mime_type = st.session_state["audio_buffer"]
    st.audio(audio_data, format=mime_type)
