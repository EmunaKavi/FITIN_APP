import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

# Load trained model
model_path = "Model/workout_recommender.pkl"

if not os.path.exists(model_path):
    st.error(f"Model file not found at: {model_path}. Please check the path.")
    st.stop()

try:
    model = joblib.load(model_path)
except Exception as e:
    st.error(f"Error loading model: {e}")
    st.stop()

# Custom CSS for better UI
st.markdown(
    """
    <style>
    body {
        background-image: url('https://t4.ftcdn.net/jpg/01/74/21/25/360_F_174212531_cerVf4uP6vinBWieBB46p2P5xVhnsNSK.jpg');
        background-size: cover;
        background-attachment: fixed;
        color: white;
    }
    .stApp {
        background: rgba(20, 20, 20, 0.85);
        width: 60%;
        margin: auto;
        padding: 2rem;
        border-radius: 20px;
        backdrop-filter: blur(8px);
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        font-size: 1rem;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .output-box {
        background-color: black;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1rem;
    }
    .emoji {
        font-size: 2rem;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Function to calculate BMI, BFP, and category
def calculate_bmi_bfp_category(weight, height, age, gender):
    bmi = weight / (height ** 2)
    bfp = (1.20 * bmi) + (0.23 * age) - (16.2 if gender == "Male" else 5.4)
    bmi_category = (
        "Severe Thinness" if bmi < 16 else
        "Moderate Thinness" if bmi < 17 else
        "Mild Thinness" if bmi < 18.5 else
        "Normal" if bmi < 25 else
        "Overweight" if bmi < 30 else
        "Obese" if bmi < 35 else "Severe Obese"
    )
    return round(bmi, 2), round(bfp, 2), bmi_category

# Function to generate workout plan (placeholder)
def generate_workout(plan_id, fitness_goal, workout_type, intensity, hypertension, disability):
    return f"Workout Plan {plan_id}: {workout_type} exercises for {intensity} level. Goal: {fitness_goal}. Considerations: Hypertension={hypertension}, Disability={disability}."

# Function to save workout plan as a PDF
def save_pdf(filename, user_data, workout_plan):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, "🏋️ AI Personal Workout Plan")
    c.line(100, 745, 500, 745)
    y = 720
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "📌 User Information:")
    y -= 20
    c.setFont("Helvetica", 12)
    for key, value in user_data.items():
        c.drawString(100, y, f"• {key}: {value}")
        y -= 20
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "🏋️ Workout Plan:")
    y -= 20
    c.setFont("Helvetica", 12)
    for line in workout_plan.split("\n"):
        wrapped_lines = simpleSplit(line, "Helvetica", 12, 400)
        for wrapped_line in wrapped_lines:
            c.drawString(100, y, wrapped_line)
            y -= 15
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 750
    c.save()

st.markdown('<h1 class="emoji">🏆 FITIN APP 🏆</h1>', unsafe_allow_html=True)

# User inputs
weight = st.number_input("Enter your weight (kg):", min_value=30.0, max_value=200.0, step=0.1)
height = st.number_input("Enter your height (m):", min_value=1.0, max_value=2.5, step=0.01)
age = st.number_input("Enter your age:", min_value=10, max_value=100, step=1)
gender = st.selectbox("Select your gender:", ["Male", "Female"])
fitness_goal = st.text_input("Enter your fitness goal:")
workout_type = st.selectbox("Select workout type:", ["Gym", "Home", "Bodyweight"])
intensity = st.selectbox("Select workout intensity:", ["Beginner", "Intermediate", "Advanced"])
hypertension = st.radio("Hypertension?", ["Yes", "No"])
disability = st.radio("Disability?", ["Yes", "No"])

if st.button("🏃 Get Workout Plan"):
    if not fitness_goal:
        st.warning("⚠️ Please enter a fitness goal!")
    else:
        bmi, bfp, bmi_category = calculate_bmi_bfp_category(weight, height, age, gender)
        st.subheader("📌 Your Fitness Analysis")
        st.write(f"**BMI:** {bmi}")
        st.write(f"**BFP:** {bfp}%")
        st.write(f"**Category:** {bmi_category}")
        
        input_data = np.array([[weight, height, bmi, bfp, 0 if gender == "Male" else 1, age, 4]])
        
        try:
            predicted_plan = model.predict(input_data)[0]
        except Exception as e:
            st.error(f"Model prediction error: {e}")
            st.stop()
        
        personalized_plan = generate_workout(predicted_plan, fitness_goal, workout_type, intensity, hypertension, disability)
        
        st.subheader("🏋️ Your Personalized Workout Plan")
        st.markdown(f'<div class="output-box">{personalized_plan}</div>', unsafe_allow_html=True)
        
        user_info = {
            "Weight": weight, "Height": height, "Age": age, "Gender": gender,
            "BMI": bmi, "BFP": bfp, "Category": bmi_category
        }
        
        pdf_filename = "Workout_Plan.pdf"
        save_pdf(pdf_filename, user_info, personalized_plan)
        
        with open(pdf_filename, "rb") as pdf_file:
            st.download_button("Download Workout Plan as PDF", data=pdf_file, file_name=pdf_filename, mime="application/pdf")
