import streamlit as st
import pandas as pd
import numpy as np
import groq
import joblib
import os

# Load trained model
model_path = "Model/workout_recommender.pkl"

if os.path.exists(model_path):
    model = joblib.load(model_path)
else:
    st.error("Error: Model file not found!")
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
    if gender == "Male":
        bfp = (1.20 * bmi) + (0.23 * age) - 16.2
    else:
        bfp = (1.20 * bmi) + (0.23 * age) - 5.4

    # Categorizing BMI
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

# Function to generate workout plan using Groq API
def generate_workout(plan_id, fitness_goal):
    api_key = "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"  # Replace with your actual API key
    client = groq.Client(api_key=api_key)

    prompt = f"Generate a detailed workout plan for someone assigned to exercise plan {plan_id} with the goal of {fitness_goal}."
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a fitness expert."},
            {"role": "user", "content": prompt},
        ]
    )
    return response.choices[0].message.content

# Streamlit UI
st.markdown('<h1 class="emoji">🏆 FITIN APP 🏆</h1>', unsafe_allow_html=True)

# User inputs
with st.container():
    weight = st.number_input("Enter your weight (kg):", min_value=30.0, max_value=200.0, step=0.1)
    height = st.number_input("Enter your height (m):", min_value=1.0, max_value=2.5, step=0.01)
    age = st.number_input("Enter your age:", min_value=10, max_value=100, step=1)
    gender = st.selectbox("Select your gender:", ["Male", "Female"])
    fitness_goal = st.text_input("Enter your fitness goal (e.g., weight loss, muscle gain):")

if st.button("🏃 Get Workout Plan"):
    if not fitness_goal:
        st.warning("⚠️ Please enter a fitness goal!")
    else:
        bmi, bfp, bmi_category = calculate_bmi_bfp_category(weight, height, age, gender)

        st.subheader("📌 Your Fitness Analysis")
        st.markdown(f"<p style='color: white;'>🔥 <b>BMI:</b> {bmi} kg/m²</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: white;'>💧 <b>Body Fat Percentage (BFP):</b> {bfp}%</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: white;'>📊 <b>BMI Category:</b> {bmi_category}</p>", unsafe_allow_html=True)

        input_data = np.array([[weight, height, bmi, bfp, 0 if gender == "Male" else 1, age, 4]])
        predicted_plan = model.predict(input_data)[0]

        with st.spinner("⏳ Generating your workout plan..."):
            personalized_plan = generate_workout(predicted_plan, fitness_goal)

        st.subheader("🏋️ Your Personalized Workout Plan")
        st.markdown(f"<div class='output-box'>{personalized_plan}</div>", unsafe_allow_html=True)
