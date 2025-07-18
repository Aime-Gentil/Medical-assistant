import streamlit as st
import pandas as pd
from io import BytesIO
import google.generativeai as genai
import os # Import os for file path operations

# --- Gemini API Configuration ---
# Configure the genai library with the API key from Streamlit secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"Failed to configure Gemini API. Please ensure 'GEMINI_API_KEY' is set in Streamlit secrets. Error: {e}")
    st.stop() # Stop the app if API key is not configured

model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

# --- Function to format the AI generated recommendation text ---
def format_recommendation_text(text):
    """
    Formats the AI-generated text with colors, icons, and improved readability.
    """
    # Add Font Awesome icons and apply custom styling to sections
    text = text.replace("Medication Recommendations", '<h4 class="sub-section-header"><i class="fas fa-pills section-icon"></i> Medication Recommendations</h4>')
    text = text.replace("Dosage Guidelines", '<h4 class="sub-section-header"><i class="fas fa-syringe section-icon"></i> Dosage Guidelines</h4>')
    text = text.replace("Practical Activities", '<h4 class="sub-section-header"><i class="fas fa-walking section-icon"></i> Practical Activities</h4>')

    # If you want to color the *content* of each section, you'd need more advanced parsing
    # of the AI's output structure (e.g., splitting by "Medication Recommendations:", etc.)
    # For this example, we'll focus on styling the headers and the overall box.

    return text

# --- Streamlit UI Setup ---
st.set_page_config(page_title="AI Medical Assistant", layout="centered")

# Inject Font Awesome and custom CSS from style.css
st.markdown(
    """
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    """,
    unsafe_allow_html=True
)

# Read the custom CSS file content and inject it
css_file_path = os.path.join(os.path.dirname(__file__), "style.css")
try:
    with open(css_file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.error("`style.css` not found. Please ensure it's in the same directory as `med_assistant.py` in your repository.")


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
            st.warning("DOCX file detected. Direct parsing of DOCX content requires the 'python-docx' library. "
                       "For this demo, please manually copy relevant text from the DOCX file into the 'Symptoms / Condition' box for best results, or consider converting DOCX to TXT/PDF.")
            file_content = f"Uploaded DOCX file: {uploaded_file.name}. Content not parsed automatically in this demo."
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

        # Call the Gemini API using the genai model
        try:
            with st.spinner("Generating recommendations... Please wait. This may take a moment."):
                response = model.generate_content("".join(prompt_parts))
                recommendation_text = response.text

                # Format the text for display with colors and icons
                formatted_recommendation = format_recommendation_text(recommendation_text)

                st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
                st.markdown('<h3 class="sub-header">Generated Recommendation:</h3>', unsafe_allow_html=True)
                st.markdown(formatted_recommendation, unsafe_allow_html=True) # Use st.markdown for HTML content
                st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred while generating recommendations: {e}")
            st.write("Please check your input or try again later.")

st.markdown("---")
st.write("Disclaimer: This AI agent provides suggestions for informational purposes only and should not replace professional medical advice. Always consult with a qualified healthcare professional for diagnosis and treatment.")
