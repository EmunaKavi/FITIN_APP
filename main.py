import streamlit as st
import pandas as pd
import numpy as np
import os
import joblib
import shutil
import time
import tempfile
import datetime
import pyttsx3
from googleapiclient.discovery import build
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from pydub import AudioSegment
from gtts import gTTS, gTTSError  # Fallback TTS engine

# Set API keys
GROQ_API_KEY = "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"
YOUTUBE_API_KEY = "AIzaSyCg4MsfEezpeMY8QZ78WDDFqaQZv-keNxc"

# Load ML model safely
model_path = "Model/workout_recommender.pkl"
model = None
try:
    if os.path.exists(model_path):
        model = joblib.load(model_path)
    else:
        st.error(f"Error: Model file not found at {model_path}")
except Exception as e:
    st.error(f"Error loading the model: {str(e)}")

def calculate_bmi_bfp(weight, height, age, gender):
    bmi = weight / (height ** 2)
    bfp = (1.20 * bmi) + (0.23 * age) - (16.2 if gender == "Male" else 5.4)
    
    categories = {
        "Severe Thinness": bmi < 16,
        "Moderate Thinness": 16 <= bmi < 17,
        "Mild Thinness": 17 <= bmi < 18.5,
        "Normal": 18.5 <= bmi < 25,
        "Overweight": 25 <= bmi < 30,
        "Obese": 30 <= bmi < 35,
        "Severe Obese": bmi >= 35
    }
    
    bmi_category = next(cat for cat, cond in categories.items() if cond)
    return round(bmi, 2), round(bfp, 2), bmi_category

def generate_workout(plan_id, fitness_goal, workout_type, intensity, hypertension, disability, diabetes, training_focus):
    client = groq.Client(api_key=GROQ_API_KEY)
    prompt = f"""Generate a {intensity} level {workout_type} workout plan for a user with fitness goal: {fitness_goal}.
    User has health concerns - Hypertension: {hypertension}, Disability: {disability}, Diabetes: {diabetes}.
    Focus area: {training_focus}. Provide a safe & effective weekly plan."""
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": "You are a fitness expert."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def generate_diet_plan(bmi, bfp, category, goal, diabetes):
    client = groq.Client(api_key=GROQ_API_KEY)
    prompt = f"""Create a diet plan for a person with BMI {bmi}, BFP {bfp}, in {category} category.
    Fitness Goal: {goal}. Diabetes: {diabetes}. Include balanced meals for breakfast, lunch, dinner, and snacks."""
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": "You are a nutritionist."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def search_exercise_video(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    search_response = youtube.search().list(q=query, part="id,snippet", maxResults=1).execute()
    for item in search_response.get("items", []):
        if item["id"]["kind"] == "youtube#video":
            return f"https://www.youtube.com/watch?v={item['id']['videoId']}"
    return None

def save_pdf(filename, user_data, workout, diet, video_url):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, "🏋️ AI Personal Workout & Diet Plan")
    c.line(100, 745, 500, 745)

    y = 720
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "📌 User Information:")
    y -= 20
    c.setFont("Helvetica", 12)
    for key, value in user_data.items():
        c.drawString(100, y, f"• {key}: {value}")
        y -= 20

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "🏋️ Workout Plan:")
    y -= 30
    c.setFont("Helvetica", 12)
    for line in workout.split("\n"):
        c.drawString(100, y, line)
        y -= 20

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "🍏 Diet Plan:")
    y -= 30
    c.setFont("Helvetica", 12)
    for line in diet.split("\n"):
        c.drawString(100, y, line)
        y -= 20

    if video_url:
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, y, "Exercise Video:")
        y -= 20
        link_text = "Click here to watch"
        c.setFillColorRGB(0, 0, 1)
        c.drawString(100, y, link_text)
        text_width = c.stringWidth(link_text, "Helvetica", 12)
        c.linkURL(video_url, (100, y, 100 + text_width, y + 12), relative=0)
        c.setFillColorRGB(0, 0, 0)

    c.save()

def tts_gtts(text):
    try:
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_filename = temp_file.name
        tts.save(temp_filename)
        return temp_filename, "mp3"
    except gTTSError:
        return None, None

# Streamlit UI
st.title("🏋️ AI Workout & Diet Planner")
st.sidebar.header("User Details")

name = st.sidebar.text_input("Name")
weight = st.sidebar.number_input("Weight (kg)", 30, 150)
height = st.sidebar.number_input("Height (m)", 1.0, 2.5)
age = st.sidebar.number_input("Age", 10, 100)
gender = st.sidebar.radio("Gender", ["Male", "Female"])
fitness_goal = st.sidebar.selectbox("Fitness Goal", ["Weight Loss", "Muscle Gain", "General Fitness"])
workout_type = st.sidebar.selectbox("Workout Type", ["Strength", "Cardio", "Mixed"])
intensity = st.sidebar.selectbox("Intensity", ["Beginner", "Intermediate", "Advanced"])
training_focus = st.sidebar.text_input("Focus Area (e.g., Abs, Legs, Arms)")
diabetes = st.sidebar.checkbox("Diabetes?")
hypertension = st.sidebar.checkbox("Hypertension?")
disability = st.sidebar.checkbox("Disability?")

if st.sidebar.button("Generate Plan"):
    bmi, bfp, category = calculate_bmi_bfp(weight, height, age, gender)
    workout = generate_workout(1, fitness_goal, workout_type, intensity, hypertension, disability, diabetes, training_focus)
    diet = generate_diet_plan(bmi, bfp, category, fitness_goal, diabetes)
    video_url = search_exercise_video(workout_type)
    st.write(workout)
    st.write(diet)
    st.video(video_url)
