import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# Load both datasets and merge them
data1 = pd.read_csv("../Data-set/final_dataset_BFP .csv")
data2 = pd.read_csv("../Data-set/final_dataset.csv")
data = pd.concat([data1, data2], ignore_index=True)

# Data Cleaning: Handle missing values (only for numeric columns)
data.fillna(data.select_dtypes(include=np.number).median(), inplace=True)

# Data Integration: Encode categorical variables
label_encoders = {}
categorical_columns = ["Gender", "BMIcase", "BFPcase"]

for col in categorical_columns:
    le = LabelEncoder()
    data[col] = le.fit_transform(data[col])
    label_encoders[col] = le

# Define features and labels
X = data[["Weight", "Height", "BMI", "Body Fat Percentage", "Gender", "Age", "BMIcase"]]
y = data["Exercise Recommendation Plan"]

# Data Transformation: Normalize the data
scaler = MinMaxScaler()
X = scaler.fit_transform(X)

# Save the scaler for future use
joblib.dump(scaler, "scaler.pkl")

# Split data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Define the machine learning model (Random Forest)
model = RandomForestClassifier(n_estimators=100, random_state=42)

# Train the model
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy * 100:.2f}%")

# Save the trained model
joblib.dump(model, "workout_recommender.pkl")
print("Model saved successfully!")
