import streamlit as st
import pickle
import pandas as pd
import numpy as np
import os
import traceback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import time
import requests

# Try loading environment variables from .env file manually
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as env_file:
        for line in env_file:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    os.environ[parts[0].strip()] = parts[1].strip().strip('"').strip("'")

# Page Configuration
st.set_page_config(
    page_title="EduGuard AI | Student Retention & Counseling",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Theme CSS
st.markdown("""
<style>
    /* Dark Background */
    .stApp {
        background-color: #0B0F17;
        color: #E5E7EB;
    }
    
    /* Input Fields styling */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
        background-color: #121824 !important;
        border: 1px solid #1F2937 !important;
        border-radius: 12px !important;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #A3E635 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: none !important;
        transition: all 0.3s ease !important;
        width: 100%;
        padding: 10px 0 !important;
    }
    .stButton>button:hover {
        background-color: #BEF264 !important;
        box-shadow: 0 0 15px rgba(163, 230, 53, 0.4) !important;
        transform: scale(1.02);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #090D14 !important;
        border-right: 1px solid #1F2937 !important;
    }
    
    /* Custom Card container */
    .custom-card {
        background-color: #121824;
        border: 1px solid #1F2937;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }
    
    /* Custom badges */
    .badge-critical {
        background-color: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 11px;
    }
    .badge-medium {
        background-color: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 11px;
    }
    .badge-low {
        background-color: rgba(163, 230, 53, 0.15);
        color: #A3E635;
        border: 1px solid rgba(163, 230, 53, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 11px;
    }
</style>
""", unsafe_allow_html=True)

# Cache loading model & encoder
@st.cache_resource
def load_ml_resources():
    model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
    encoder_path = os.path.join(os.path.dirname(__file__), 'encoder.pkl')
    
    model = None
    encoder = None
    
    if os.path.exists(model_path):
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
        except Exception as e:
            st.error(f"Error loading model: {e}")
            
    if os.path.exists(encoder_path):
        try:
            with open(encoder_path, 'rb') as f:
                encoder = pickle.load(f)
        except Exception as e:
            st.error(f"Error loading encoder: {e}")
            
    return model, encoder

model, encoder = load_ml_resources()

# Session State Initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'email' not in st.session_state:
    st.session_state.email = ""
if 'otp_sent' not in st.session_state:
    st.session_state.otp_sent = False
if 'otp_code' not in st.session_state:
    st.session_state.otp_code = ""
if 'otp_expires' not in st.session_state:
    st.session_state.otp_expires = 0.0
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'active_student' not in st.session_state:
    st.session_state.active_student = None
if 'dashboard_data' not in st.session_state:
    # Seed with some static mock data
    st.session_state.dashboard_data = [
        {
            "name": "John Doe",
            "risk_probability": 87.0,
            "GPA": 1.8,
            "Attendance_Rate": 65.0,
            "Study_Hours_per_Day": 2.5,
            "Assignment_Delay_Days": 8,
            "Travel_Time_Minutes": 45,
            "Stress_Index": 7,
            "Age": 22,
            "Family_Income": 35000,
            "Education_Level": "High School"
        },
        {
            "name": "Amara Smith",
            "risk_probability": 54.0,
            "GPA": 2.4,
            "Attendance_Rate": 78.0,
            "Study_Hours_per_Day": 4.0,
            "Assignment_Delay_Days": 4,
            "Travel_Time_Minutes": 20,
            "Stress_Index": 5,
            "Age": 20,
            "Family_Income": 48000,
            "Education_Level": "Bachelor"
        }
    ]
if 'prediction_result' not in st.session_state:
    st.session_state.prediction_result = None

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_PASSKEY = os.environ.get("SMTP_PASSKEY")
if not SMTP_PASSKEY:
    try:
        SMTP_PASSKEY = st.secrets["SMTP_PASSKEY"]
    except Exception:
        pass


# --- SMTP OTP SENDER ---
def send_otp_email(target_email):
    otp = f"{random.randint(100000, 999999)}"
    
    # Prepare email body
    message = MIMEMultipart("alternative")
    message["Subject"] = "EduGuard AI - Verification Code"
    message["From"] = f"EduGuard AI Security <{target_email}>"
    message["To"] = target_email

    html = f"""
    <html>
      <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0B0F17; color: #ffffff; padding: 20px; text-align: center;">
        <div style="max-width: 500px; margin: 0 auto; background-color: #121824; border: 1px solid #1f2937; border-radius: 16px; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.3);">
          <div style="background-color: #a3e635; color: #000000; display: inline-block; padding: 8px 16px; border-radius: 8px; font-weight: bold; letter-spacing: 2px; margin-bottom: 24px; font-size: 20px;">EG</div>
          <h2 style="color: #ffffff; font-size: 24px; font-weight: 700; margin-bottom: 8px;">Security Verification</h2>
          <p style="color: #9ca3af; font-size: 14px; margin-bottom: 24px;">Use the One-Time Password (OTP) below to access the counselor console dashboard.</p>
          
          <div style="background-color: #0b0f17; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; font-size: 36px; font-weight: 800; color: #a3e635; letter-spacing: 6px; margin: 24px 0; font-family: monospace;">
            {otp}
          </div>
          
          <p style="color: #ef4444; font-size: 12px; margin-top: 24px;">This code will expire in 5 minutes. Do not share this code with anyone.</p>
          <hr style="border: 0; border-top: 1px solid #1f2937; margin: 32px 0 16px 0;">
          <p style="color: #6b7280; font-size: 11px;">EduGuard AI System Security Portal &copy; 2026</p>
        </div>
      </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(target_email, SMTP_PASSKEY)
            server.sendmail(target_email, target_email, message.as_string())
        return True, otp
    except Exception as e:
        return False, str(e)

# --- GEMINI CHAT CONNECTOR ---
def get_gemini_response(message, history, student_context):
    api_key = os.environ.get("GEMINI_API_KEY")
    # Streamlit Cloud secrets compatibility fallback
    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
            
    if not api_key:
        return "⚠️ Gemini API Key is not configured on the server. Please add it to your `.env` or Streamlit Cloud Secrets."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "You are a compassionate, professional academic counselor at EduGuard AI. Your goal is to support "
        "students who may be at risk of dropping out or experiencing academic stress. Be encouraging, "
        "practical, empathetic, and solutions-oriented. Keep responses reasonably concise (2-4 sentences per turn "
        "where possible), formatted with clear spacing or bullet points when offering suggestions."
    )

    if student_context:
        name = student_context.get('name', 'the student')
        gpa = student_context.get('GPA', 'N/A')
        attendance = student_context.get('Attendance_Rate', 'N/A')
        study_hours = student_context.get('Study_Hours_per_Day', 'N/A')
        delay = student_context.get('Assignment_Delay_Days', 'N/A')
        stress = student_context.get('Stress_Index', 'N/A')
        edu = student_context.get('Education_Level', 'N/A')
        risk = student_context.get('risk_probability', 'N/A')

        system_instruction += (
            f"\n\nYou are currently advising student: {name}."
            f"\nStudent Profile context details:"
            f"\n- Predicted Drop-out Risk: {risk}%"
            f"\n- GPA: {gpa}"
            f"\n- Attendance Rate: {attendance}%"
            f"\n- Study Hours per Day: {study_hours} hrs"
            f"\n- Assignment Delay: {delay} days"
            f"\n- Stress Index: {stress}/10"
            f"\n- Education Level: {edu}"
            f"\nUtilize these details to offer specific, empathetic recommendations. Keep the tone supportive."
        )

    contents = []
    for msg in history:
        role = 'user' if msg.get('role') == 'user' else 'model'
        contents.append({
            "role": role,
            "parts": [{"text": msg.get('text', '')}]
        })

    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        }
    }

    try:
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        if resp.status_code == 200:
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error from Gemini API: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- MAIN RENDER ROUTINE ---
if not st.session_state.authenticated:
    # --- LOGIN SCREEN ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("")
        st.write("")
        st.write("")
        
        # Show Portal Logo above name if exists
        logo_path = os.path.join(os.path.dirname(__file__), 'portal_logo.jpg')
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
            
        st.markdown("<h2 style='text-align: center; color: white;'>EduGuard AI Portal</h2>", unsafe_allow_html=True)
        
        if not st.session_state.otp_sent:
            # Stage 1: Email Input
            st.markdown("<p style='text-align: center; font-size: 13px; color: #9CA3AF;'>Enter your email address to authenticate and access the counselor board.</p>", unsafe_allow_html=True)
            email_val = st.text_input("Enter your email", placeholder="example@gmail.com")
            if st.button("Sign In / Sign Up"):
                if email_val.strip() and "@" in email_val:
                    with st.spinner("Sending verification code..."):
                        success, res = send_otp_email(email_val.strip())
                        if success:
                            st.session_state.otp_code = res
                            st.session_state.email = email_val.strip()
                            st.session_state.otp_sent = True
                            st.session_state.otp_expires = time.time() + 300
                            st.success("Verification code sent! Please check your email.")
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error(f"Failed to send verification email: {res}")
                else:
                    st.warning("Please enter a valid email address.")
        else:
            # Stage 2: OTP Input
            st.markdown(f"<p style='text-align: center; font-size: 13px; color: #9CA3AF;'>Enter the 6-digit code sent to <b>{st.session_state.email}</b></p>", unsafe_allow_html=True)
            otp_val = st.text_input("One-Time Password (OTP)", placeholder="6-digit verification code", max_chars=6)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Verify & Unlock"):
                    if time.time() > st.session_state.otp_expires:
                        st.error("Verification code has expired. Please request a new code.")
                    elif otp_val.strip() == st.session_state.otp_code:
                        st.session_state.authenticated = True
                        st.session_state.otp_sent = False
                        st.session_state.otp_code = ""
                        st.rerun()
                    else:
                        st.error("Invalid verification code. Please try again.")
            with c2:
                if st.button("Back / Change Email"):
                    st.session_state.otp_sent = False
                    st.session_state.otp_code = ""
                    st.rerun()
else:
    # --- DASHBOARD & CHAT LAYOUT ---
    
    # Header bar
    st.markdown("""
        <div style='display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1F2937; padding-bottom: 15px; margin-bottom: 25px;'>
            <div style='display: flex; align-items: center; gap: 12px;'>
                <div style='background-color: #A3E635; color: black; font-weight: bold; padding: 8px 12px; border-radius: 8px; font-size: 20px;'>EG</div>
                <h2 style='margin: 0; color: white;'>EduGuard <span style='color: #A3E635;'>AI</span></h2>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Left (Dashboard 75%) and Right (Chatbot 25%) Split
    col_dash, col_chat = st.columns([3, 1])
    
    # --- LEFT SIDE: DASHBOARD ---
    with col_dash:
        # Title banner
        st.markdown("""
            <div style='margin-bottom: 25px;'>
                <span style='background-color: #111827; border: 1px solid #1F2937; padding: 6px 12px; border-radius: 20px; color: #A3E635; font-weight: 600; font-size: 11px;'>
                    🟢 Intelligent Student Retention
                </span>
                <h1 style='margin-top: 15px; font-size: 36px; font-weight: 800; color: white; line-height: 1.2;'>
                    Innovative AI Solutions<br>
                    <span style='background: linear-gradient(to right, #a3e635, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>That Prevent Drop-outs</span>
                </h1>
            </div>
        """, unsafe_allow_html=True)
        
        # Predictor Columns: Input Form (Left) & Results Display (Right)
        st.subheader("Evaluate Student Drop-out Risk")
        p_col_in, p_col_res = st.columns([2, 1])
        
        with p_col_in:
            with st.form("prediction_form"):
                st.markdown("<p style='font-size: 12px; text-transform: uppercase; color: #9CA3AF; margin-bottom: 15px;'>Student Information</p>", unsafe_allow_html=True)
                
                f_name = st.text_input("Student Name", value="Jane Doe")
                f_edu = st.selectbox("Education Level", ["High School", "Bachelor", "Master", "PhD"], index=1)
                
                c_a, c_b = st.columns(2)
                with c_a:
                    f_age = st.number_input("Age", min_value=15, max_value=100, value=21)
                with c_b:
                    f_income = st.number_input("Family Annual Income ($)", min_value=0, value=45000)
                    
                f_hours = st.slider("Study Hours per Day", min_value=1.0, max_value=15.0, value=6.0, step=0.5)
                f_attendance = st.slider("Attendance Rate (%)", min_value=0, max_value=100, value=88)
                
                c_c, c_d = st.columns(2)
                with c_c:
                    f_delay = st.number_input("Assignment Delay Days", min_value=0, max_value=30, value=2)
                with c_d:
                    f_travel = st.number_input("Travel Time (Minutes)", min_value=0, max_value=180, value=30)
                    
                f_gpa = st.number_input("GPA (0.00 - 4.00)", min_value=0.0, max_value=4.0, value=3.15, step=0.01)
                f_stress = st.slider("Stress Index (1-10)", min_value=1, max_value=10, value=4)
                
                submit_pred = st.form_submit_button("Run AI Prediction")
                
                if submit_pred:
                    if not model:
                        st.error("ML Model not loaded.")
                    else:
                        # Prepare payload DataFrame
                        features = {
                            'Age': float(f_age),
                            'Family_Income': float(f_income),
                            'Study_Hours_per_Day': float(f_hours),
                            'Attendance_Rate': float(f_attendance),
                            'Assignment_Delay_Days': float(f_delay),
                            'Travel_Time_Minutes': float(f_travel),
                            'Stress_Index': float(f_stress),
                            'GPA': float(f_gpa)
                        }
                        
                        # Encode Education
                        encoded_edu = 0
                        if encoder:
                            try:
                                matched_class = None
                                for cls in encoder.classes_:
                                    if str(cls).strip().lower() == str(f_edu).strip().lower():
                                        matched_class = cls
                                        break
                                if matched_class is not None:
                                    encoded_edu = int(encoder.transform([matched_class])[0])
                                else:
                                    encoded_edu = int(encoder.transform([encoder.classes_[0]])[0])
                            except Exception:
                                encoded_edu = -1
                                
                        df = pd.DataFrame([features])
                        # Align feature names
                        df = df[model.feature_names_in_]
                        proba = model.predict_proba(df)[0]
                        dropout_risk_prob = float(proba[1]) * 100
                        prediction = int(model.predict(df)[0])
                        
                        st.session_state.prediction_result = {
                            "name": f_name,
                            "risk_probability": round(dropout_risk_prob, 2),
                            "prediction": prediction,
                            "Education_Level": f_edu,
                            "encoded_education_level": encoded_edu,
                            "GPA": f_gpa,
                            "Attendance_Rate": f_attendance,
                            "Study_Hours_per_Day": f_hours,
                            "Assignment_Delay_Days": f_delay,
                            "Stress_Index": f_stress,
                            "Age": f_age,
                            "Family_Income": f_income,
                            "Travel_Time_Minutes": f_travel
                        }
        
        with p_col_res:
            st.markdown("<p style='font-size: 12px; text-transform: uppercase; color: #9CA3AF; margin-bottom: 15px;'>Evaluation Result</p>", unsafe_allow_html=True)
            
            if not st.session_state.prediction_result:
                # Idle State: Worried student logo
                st.markdown("""
                    <div style='background-color: #121824; border: 1px solid #1F2937; border-radius: 16px; padding: 32px; text-align: center;'>
                        <h4 style='color: white; margin-bottom: 10px;'>System Idle</h4>
                        <p style='color: #9CA3AF; font-size: 12px; line-height: 1.5;'>Fill in student indicators and click "Run AI Prediction" to calculate drop-out risk status.</p>
                    </div>
                """, unsafe_allow_html=True)
                student_img_path = os.path.join(os.path.dirname(__file__), 'idle_student.png')
                if os.path.exists(student_img_path):
                    st.image(student_img_path, caption="Worried student avatar", width=180)
            else:
                res = st.session_state.prediction_result
                risk = res["risk_probability"]
                
                # Risk label & styling
                if risk >= 70:
                    badge_html = "<span class='badge-critical'>CRITICAL RISK</span>"
                    rec_text = "High risk cohort flagged. Recommend dispatching immediate personal counseling invites and academic tutoring support."
                elif risk >= 30:
                    badge_html = "<span class='badge-medium'>MEDIUM RISK</span>"
                    if res["Attendance_Rate"] < 75:
                        rec_text = "Attendance deficit detected. Schedule an informal review session to identify complications."
                    elif res["GPA"] < 2.5:
                        rec_text = "Academic grades require support. Recommend assignment mentoring and extra subject practice classes."
                    else:
                        rec_text = "Elevated risk signals. Suggest coordinating counseling outreach modules and periodic mentoring reviews."
                else:
                    badge_html = "<span class='badge-low'>LOW RISK</span>"
                    rec_text = "Student is currently stable. Maintain standard academic observation."
                    if res["Stress_Index"] > 7:
                        rec_text = "Student is academically sound but reports high stress levels. Advise mental wellness resources."

                st.markdown(f"""
                    <div style='background-color: #121824; border: 1px solid #1F2937; border-radius: 16px; padding: 20px;'>
                        <h3 style='color: white; margin: 0;'>{res['name']}</h3>
                        <p style='font-size: 11px; color: #9CA3AF; margin-top: 4px; margin-bottom: 20px;'>Level: {res['Education_Level']}</p>
                        
                        <div style='text-align: center; margin: 20px 0;'>
                            <h2 style='font-size: 40px; font-weight: 800; color: #A3E635; margin: 0;'>{risk}%</h2>
                            <p style='font-size: 10px; color: #9CA3AF; text-transform: uppercase;'>Dropout Risk Probability</p>
                            <div style='margin-top: 10px;'>{badge_html}</div>
                        </div>
                        
                        <div style='background-color: #0B0F17; border: 1px solid #1F2937; border-radius: 10px; padding: 12px; margin-bottom: 20px;'>
                            <p style='font-size: 10px; font-weight: bold; color: #A3E635; margin: 0 0 4px 0;'>RECOMMENDATION</p>
                            <p style='font-size: 11px; color: #E5E7EB; line-height: 1.4; margin: 0;'>{rec_text}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                c_action1, c_action2 = st.columns(2)
                with c_action1:
                    if st.button("Save to Dashboard"):
                        # Save if not already exists (checking by name/risk)
                        if not any(d['name'] == res['name'] and d['risk_probability'] == res['risk_probability'] for d in st.session_state.dashboard_data):
                            st.session_state.dashboard_data.insert(0, res)
                            st.success(f"Saved {res['name']}!")
                            time.sleep(1)
                            st.rerun()
                with c_action2:
                    if st.button("Discuss with AI"):
                        st.session_state.active_student = res
                        # Populate chatbot context welcome bubble
                        risk_lvl = "Critical Risk" if risk >= 70 else ("Medium Risk" if risk >= 30 else "Low Risk")
                        welcome_txt = (
                            f"AI Counselor has loaded **{res['name']}**'s academic profile (Risk: **{risk}% {risk_lvl}**, "
                            f"GPA: **{res['GPA']}**, Attendance: **{res['Attendance_Rate']}%**).\n\n"
                            f"How can I help you compile coping plans or analyze risk indicators for {res['name']}?"
                        )
                        st.session_state.chat_history = [{"role": "model", "text": welcome_txt}]
                        st.success("Context loaded to chatbot!")
                        time.sleep(1)
                        st.rerun()
        
        # Real-Time Counselor Dashboard
        st.write("")
        st.write("")
        st.markdown("<h3 style='color: white;'>Real-Time Counselor Dashboard</h3>", unsafe_allow_html=True)
        
        # Dashboard Table representation
        if st.session_state.dashboard_data:
            # We construct a custom clean dataframe preview
            dash_df_list = []
            for student in st.session_state.dashboard_data:
                risk_val = student['risk_probability']
                lbl = "CRITICAL" if risk_val >= 70 else ("MEDIUM" if risk_val >= 30 else "LOW")
                dash_df_list.append({
                    "Student Name": student['name'],
                    "Risk Level": f"{risk_val}% {lbl}",
                    "GPA": student['GPA'],
                    "Attendance": f"{student['Attendance_Rate']}%"
                })
            
            st.dataframe(pd.DataFrame(dash_df_list), use_container_width=True)
            
            # Selectbox to select any dashboard student to load in chatbot
            student_names = [s['name'] for s in st.session_state.dashboard_data]
            sel_student_name = st.selectbox("Select student to counseling AI discussion", student_names)
            if st.button("Load Student Context into Chatbot"):
                matched_std = next((s for s in st.session_state.dashboard_data if s['name'] == sel_student_name), None)
                if matched_std:
                    st.session_state.active_student = matched_std
                    risk_v = matched_std['risk_probability']
                    risk_lvl = "Critical Risk" if risk_v >= 70 else ("Medium Risk" if risk_v >= 30 else "Low Risk")
                    welcome_txt = (
                        f"AI Counselor has loaded **{matched_std['name']}**'s academic profile (Risk: **{risk_v}% {risk_lvl}**, "
                        f"GPA: **{matched_std['GPA']}**, Attendance: **{matched_std['Attendance_Rate']}%**).\n\n"
                        f"How can I help you compile coping plans or analyze risk indicators for {matched_std['name']}?"
                    )
                    st.session_state.chat_history = [{"role": "model", "text": welcome_txt}]
                    st.success(f"Loaded {sel_student_name}!")
                    time.sleep(1)
                    st.rerun()
                    
    # --- RIGHT SIDE: PERSISTENT SIDEBAR CHATBOT ---
    with col_chat:
        st.markdown("""
            <div style='background-color: #0B0F17; border-left: 1px solid #1F2937; padding-left: 15px; height: 100%;'>
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 20px; border-bottom: 1px solid #1F2937; padding-bottom: 10px;'>
                    <h4 style='color: white; margin: 0;'>AI Counselor</h4>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Show counselor avatar above feed
        avatar_path = os.path.join(os.path.dirname(__file__), 'counselor_avatar.jpg')
        if os.path.exists(avatar_path):
            st.image(avatar_path, width=70, caption="counselor_avatar.jpg")
            
        # Suggestions Chips
        st.markdown("<p style='font-size: 10px; color: #9CA3AF; margin-bottom: 5px; text-transform: uppercase;'>Quick Suggestions</p>", unsafe_allow_html=True)
        c_s1, c_s2 = st.columns(2)
        with c_s1:
            if st.button("Stress Recovery", key="chip_stress"):
                st.session_state.chat_history.append({"role": "user", "text": "How can I reduce academic stress?"})
                with st.spinner("Typing..."):
                    resp = get_gemini_response("How can I reduce academic stress?", st.session_state.chat_history[:-1], st.session_state.active_student)
                    st.session_state.chat_history.append({"role": "model", "text": resp})
                st.rerun()
        with c_s2:
            if st.button("GPA Recovery", key="chip_gpa"):
                st.session_state.chat_history.append({"role": "user", "text": "GPA recovery plan"})
                with st.spinner("Typing..."):
                    resp = get_gemini_response("GPA recovery plan", st.session_state.chat_history[:-1], st.session_state.active_student)
                    st.session_state.chat_history.append({"role": "model", "text": resp})
                st.rerun()
        
        st.write("")
        
        # Chat Messages Feed
        chat_box = st.container(height=350)
        with chat_box:
            # Welcome greeting default if empty
            if not st.session_state.chat_history:
                st.session_state.chat_history = [{
                    "role": "model",
                    "text": "Hello! I am your AI Counselor. Once you analyze a student's risk, click 'Discuss with AI' or load their profile below to compile coping recommendations."
                }]
                
            for msg in st.session_state.chat_history:
                role = msg.get('role', 'model')
                # Map role representation to streamlit chat
                st_role = "user" if role == 'user' else "assistant"
                
                # Set custom counselor avatar
                avatar_img = None
                if st_role == "assistant" and os.path.exists(avatar_path):
                    avatar_img = avatar_path
                    
                with st.chat_message(st_role, avatar=avatar_img):
                    st.markdown(msg.get('text', ''))
                    
        # Chat Input
        chat_input_message = st.chat_input("Type a counseling query...")
        if chat_input_message:
            # Add user message
            st.session_state.chat_history.append({"role": "user", "text": chat_input_message})
            
            # Fetch Gemini response
            with st.spinner("Typing..."):
                response_text = get_gemini_response(chat_input_message, st.session_state.chat_history[:-1], st.session_state.active_student)
                st.session_state.chat_history.append({"role": "model", "text": response_text})
            st.rerun()

    # --- SIDEBAR ACCESSORIES & LOGOUT ---
    with st.sidebar:
        st.markdown("<h3 style='color: white;'>Counselor Portal</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 12px; color: #10B981;'>🟢 Session: <b>{st.session_state.email}</b></p>", unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        
        # Clear dashboard action
        if st.button("Clear Dashboard"):
            st.session_state.dashboard_data = []
            st.success("Dashboard reset!")
            time.sleep(1)
            st.rerun()
            
        # Log out action
        if st.button("Sign Out / Logout"):
            st.session_state.authenticated = False
            st.session_state.email = ""
            st.session_state.otp_sent = False
            st.session_state.otp_code = ""
            st.session_state.chat_history = []
            st.session_state.active_student = None
            st.session_state.prediction_result = None
            st.success("Logged out successfully.")
            time.sleep(1)
            st.rerun()
