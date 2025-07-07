import streamlit as st
import json
import requests
import pandas as pd
from io import BytesIO

# Define the API key
# This line attempts to fetch the API_KEY from Streamlit's secrets management.
# For deployed apps (e.g., Streamlit Cloud), this means the key must be set in the app's secrets dashboard.
# For local development, it looks for a .streamlit/secrets.toml file.
# If the key is not found in either place, it defaults to an empty string.
API_KEY = st.secrets.get("API_KEY", "")

# --- Streamlit UI Setup ---
st.set_page_config(page_title="AI Medical Assistant", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        font-size: 2.5em;
        color: #2e8b57; /* SeaGreen */
        text-align: center;
        margin-bottom: 20px;
        font-weight: bold;
        padding-top: 10px;
    }
    .sub-header {
        font-size: 1.6em;
        color: #3cb371; /* MediumSeaGreen */
        margin-top: 25px;
        margin-bottom: 15px;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 5px;
    }
    .stButton>button {
        background-color: #4CAF50; /* Green */
        color: white;
        padding: 12px 25px;
        border-radius: 10px;
        border: none;
        font-size: 1.1em;
        font-weight: 600;
        cursor: pointer;
        transition: background-color 0.3s ease, transform 0.2s ease;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        margin-top: 20px;
    }
    .stButton>button:hover {
        background-color: #45a049; /* Darker Green */
        transform: translateY(-2px);
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stFileUploader>div>div>button {
        border-radius: 8px;
        border: 1px solid #dcdcdc;
        padding: 10px;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
    }
    .stSelectbox>div>div>div {
        border-radius: 8px;
        border: 1px solid #dcdcdc;
        padding: 5px;
    }
    .recommendation-box {
        background-color: #f0fff0; /* Honeydew */
        border-left: 6px solid #3cb371; /* MediumSeaGreen */
        padding: 25px;
        border-radius: 12px;
        margin-top: 35px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    .stAlert {
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="main-header">🩺 AI Medical Assistant for Doctors 💊</h1>', unsafe_allow_html=True)
st.write("This agent assists in recommending medicines, dosages, and practical activities for patient healing, now with support for exam result uploads.")

# --- Patient Information Input ---
st.markdown('<h2 class="sub-header">Patient Information</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    patient_name = st.text_input("Patient Name (Optional)", "", help="Enter the patient's full name.")
    patient_age = st.number_input("Patient Age (Years, Optional)", min_value=0, max_value=120, value=None, placeholder="e.g., 35", help="Patient's age in years.")
with col2:
    patient_gender = st.selectbox("Patient Gender (Optional)", ["", "Male", "Female", "Other"], help="Select the patient's biological gender.")
    patient_weight = st.number_input("Patient Weight (kg, Optional)", min_value=0.0, value=None, placeholder="e.g., 70.5", help="Patient's weight in kilograms.")

patient_history = st.text_area("Relevant Medical History / Existing Conditions (Optional)", "", height=100, help="Any pre-existing conditions, allergies, or past significant medical events.")

st.markdown('<h2 class="sub-header">Upload Exam Results (Optional)</h2>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload patient exam results (CSV, XLSX, DOCX)", type=["csv", "xlsx", "docx"], help="Upload files containing laboratory results, imaging reports, etc.")

file_content = ""
if uploaded_file is not None:
    file_extension = uploaded_file.name.split('.')[-1].lower()
    try:
        if file_extension == "csv":
            df = pd.read_csv(uploaded_file)
            file_content = df.to_string()
            st.success("CSV file uploaded and processed successfully!")
        elif file_extension == "xlsx":
            df = pd.read_excel(uploaded_file)
            file_content = df.to_string()
            st.success("XLSX file uploaded and processed successfully!")
        elif file_extension == "docx":
            # For DOCX, we need a library like python-docx.
            # For simplicity in this example, we'll advise the user.
            # In a real application, you'd parse the docx content here.
            # Example:
            # from docx import Document
            # doc = Document(uploaded_file)
            # file_content = "\n".join([para.text for para in doc.paragraphs])
            st.warning("DOCX file detected. Direct parsing of DOCX content is complex and requires specific libraries (e.g., 'python-docx'). "
                       "For this demo, please manually copy relevant text into the 'Symptoms / Condition' box for best results, or consider converting DOCX to TXT/PDF.")
            file_content = f"Uploaded DOCX file: {uploaded_file.name}. Please refer to its content manually if needed."
        else:
            st.error("Unsupported file type. Please upload CSV, XLSX, or DOCX.")
            file_content = ""
    except Exception as e:
        st.error(f"Error processing file: {e}. Please ensure the file format is correct.")
        file_content = ""

st.markdown('<h2 class="sub-header">Symptoms / Condition</h2>', unsafe_allow_html=True)
symptoms = st.text_area("Describe the patient's symptoms or condition:", height=150, help="Provide a detailed description of the patient's current symptoms, complaints, and observations.")

# --- Generate Recommendation ---
if st.button("Generate Recommendation"):
    if not symptoms and not file_content:
        st.warning("Please describe the patient's symptoms/condition or upload relevant exam results to get a recommendation.")
    else:
        # Construct the prompt for the LLM
        prompt_parts = [
            "As a highly knowledgeable medical AI assistant, provide comprehensive recommendations for a patient based on the following information. "
            "Include suggested medicines, appropriate dosages, and practical activities the patient can do to aid healing. "
            "If any crucial patient information (like age or weight) is missing and relevant for better recommendations, please explicitly state what information is needed and why. "
            "Format your response clearly with sections for 'Medication Recommendations', 'Dosage Guidelines', and 'Practical Activities'.\n\n"
            f"Patient Name: {patient_name if patient_name else 'Not provided'}\n"
            f"Patient Age: {patient_age if patient_age is not None else 'Not provided'}\n"
            f"Patient Weight: {patient_weight if patient_weight is not None else 'Not provided'} kg\n"
            f"Patient Gender: {patient_gender if patient_gender else 'Not provided'}\n"
            f"Medical History: {patient_history if patient_history else 'None provided'}\n"
        ]

        if file_content:
            prompt_parts.append(f"Uploaded Exam Results:\n{file_content}\n\n")

        prompt_parts.append(f"Symptoms/Condition: {symptoms}\n\nRecommendations:")

        # Call the Gemini API
        try:
            # This check ensures the API_KEY is available before making the API call.
            # If you see "API Key not found" in your deployed app, it means the 'API_KEY'
            # secret needs to be configured in your Streamlit Cloud dashboard.
            if not API_KEY:
                st.error("API Key not found. Please set it in Streamlit secrets as 'API_KEY' in your deployment environment (e.g., Streamlit Cloud dashboard).")
            else:
                st.info("Generating recommendations... Please wait. This may take a moment.")
                chat_history = []
                chat_history.append({"role": "user", "parts": [{"text": "".join(prompt_parts)}]})

                payload = {"contents": chat_history}
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

                response = requests.post(api_url, headers={'Content-Type': 'application/json'}, json=payload)
                response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
                result = response.json()

                if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                    recommendation_text = result["candidates"][0]["content"]["parts"][0]["text"]
                    st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
                    st.markdown('<h3 class="sub-header">Generated Recommendation:</h3>', unsafe_allow_html=True)
                    st.write(recommendation_text)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error("Could not retrieve a valid recommendation from the AI. Please try again or refine your input.")
                    st.json(result) # Display the full response for debugging
        except requests.exceptions.RequestException as e:
            st.error(f"An error occurred while connecting to the AI service: {e}")
            st.write("Please check your internet connection or try again later.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

st.markdown("---")
st.write("Disclaimer: This AI agent provides suggestions for informational purposes only and should not replace professional medical advice. Always consult with a qualified healthcare professional for diagnosis and treatment.")

