from flask import Flask, request, jsonify, send_from_directory
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
    print("Loading environment variables from .env...")
    with open(env_path, 'r') as env_file:
        for line in env_file:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    os.environ[parts[0].strip()] = parts[1].strip().strip('"').strip("'")

app = Flask(__name__, static_url_path='', static_folder='.')

# OTP Storage Schema: { email: { "otp": "123456", "expires": timestamp } }
otp_store = {}

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_PASSKEY = os.environ.get("SMTP_PASSKEY", "mkau nktl usqs puwb")

# Load model and encoder
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pkl')
ENCODER_PATH = os.path.join(os.path.dirname(__file__), 'encoder.pkl')

print(f"Loading model from {MODEL_PATH}...")
try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    print("Model loaded successfully!")
    print("Expected features:", model.feature_names_in_)
except Exception as e:
    print("Error loading model:", e)
    model = None

print(f"Loading encoder from {ENCODER_PATH}...")
try:
    with open(ENCODER_PATH, 'rb') as f:
        encoder = pickle.load(f)
    print("Encoder loaded successfully!")
    print("Encoder classes:", encoder.classes_)
except Exception as e:
    print("Error loading encoder:", e)
    encoder = None

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/auth/send-otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Email address is required.'
            }), 400

        email = data['email'].strip()
        if not email or '@' not in email:
            return jsonify({
                'status': 'error',
                'message': 'Please provide a valid email address.'
            }), 400

        # Generate a 6-digit OTP code
        otp = f"{random.randint(100000, 999999)}"
        
        # Prepare email body
        message = MIMEMultipart("alternative")
        message["Subject"] = "EduGuard AI - Verification Code"
        message["From"] = f"EduGuard AI Security <{email}>"
        message["To"] = email

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

        # Send email using Gmail SMTP SSL
        print(f"Attempting to send OTP email to {email}...")
        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(email, SMTP_PASSKEY)
                server.sendmail(email, email, message.as_string())
        except smtplib.SMTPAuthenticationError:
            return jsonify({
                'status': 'error',
                'message': 'SMTP Authentication failed. Ensure the email address is the Gmail account associated with this App Password.'
            }), 401
        except Exception as smtp_err:
            print("SMTP sending failed:", smtp_err)
            return jsonify({
                'status': 'error',
                'message': f'SMTP Error: {str(smtp_err)}'
            }), 500

        # Store OTP with a 5 minute expiration
        otp_store[email] = {
            'otp': otp,
            'expires': time.time() + 300
        }

        print(f"Successfully sent and saved OTP for {email}")
        return jsonify({
            'status': 'success',
            'message': 'A 6-digit verification code has been sent to your email.'
        })

    except Exception as e:
        print("Error in /auth/send-otp:")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Server authentication error: {str(e)}'
        }), 500

@app.route('/auth/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'otp' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Email and verification code are required.'
            }), 400

        email = data['email'].strip()
        otp = data['otp'].strip()

        if email not in otp_store:
            return jsonify({
                'status': 'error',
                'message': 'No verification code was sent for this email.'
            }), 400

        record = otp_store[email]

        # Check expiration
        if time.time() > record['expires']:
            del otp_store[email]
            return jsonify({
                'status': 'error',
                'message': 'Verification code has expired. Please request a new one.'
            }), 400

        # Verify OTP
        if record['otp'] == otp:
            # Clear OTP after successful verification
            del otp_store[email]
            return jsonify({
                'status': 'success',
                'message': 'Verification successful.'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid verification code. Please check and try again.'
            }), 400

    except Exception as e:
        print("Error in /auth/verify-otp:")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Server verification error: {str(e)}'
        }), 500

@app.route('/predict', methods=['POST'])
def predict():
    if not model:
        return jsonify({
            'status': 'error',
            'message': 'Machine learning model is not loaded on the server.'
        }), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No input data provided'
            }), 400

        # Extract numerical features in correct order
        try:
            features = {
                'Age': float(data.get('Age')),
                'Family_Income': float(data.get('Family_Income')),
                'Study_Hours_per_Day': float(data.get('Study_Hours_per_Day')),
                'Attendance_Rate': float(data.get('Attendance_Rate')),
                'Assignment_Delay_Days': float(data.get('Assignment_Delay_Days')),
                'Travel_Time_Minutes': float(data.get('Travel_Time_Minutes')),
                'Stress_Index': float(data.get('Stress_Index')),
                'GPA': float(data.get('GPA'))
            }
        except (ValueError, TypeError) as e:
            return jsonify({
                'status': 'error',
                'message': f'Invalid value for a numerical feature: {str(e)}'
            }), 400

        # Encode Education Level using encoder.pkl if provided
        education_level = data.get('Education_Level', 'Bachelor')
        encoded_edu = None
        if encoder:
            try:
                # Align value with encoder classes (strip, match case)
                matched_class = None
                for cls in encoder.classes_:
                    if str(cls).strip().lower() == str(education_level).strip().lower():
                        matched_class = cls
                        break
                
                if matched_class is not None:
                    encoded_edu = int(encoder.transform([matched_class])[0])
                else:
                    # Fallback to the first class or default
                    encoded_edu = int(encoder.transform([encoder.classes_[0]])[0])
            except Exception as edu_err:
                print(f"Error encoding education level '{education_level}': {edu_err}")
                encoded_edu = -1

        # Create DataFrame for model prediction
        df = pd.DataFrame([features])
        # Ensure correct column order
        df = df[model.feature_names_in_]

        # Predict probability
        proba = model.predict_proba(df)[0]
        # proba[1] is the probability of dropout (class 1)
        dropout_risk_prob = float(proba[1]) * 100
        prediction = int(model.predict(df)[0])

        return jsonify({
            'status': 'success',
            'prediction': prediction,
            'risk_probability': round(dropout_risk_prob, 2),
            'encoded_education_level': encoded_edu
        })

    except Exception as e:
        print("Error during prediction:")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Server prediction error: {str(e)}'
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Message parameter is required.'
            }), 400

        user_message = data['message'].strip()
        student_context = data.get('student_context', {})
        chat_history = data.get('history', [])

        # Gemini configuration
        gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_api_key:
            return jsonify({
                'status': 'error',
                'message': 'Gemini API key is not configured on the server.'
            }), 500

        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"

        # Construct System Instruction based on student context
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
                f"\nUtilize these details to offer specific, empathetic recommendations (e.g., if attendance is low, "
                f"ask about transport/commitments; if stress is high, recommend wellness resources; if GPA is low, "
                f"suggest academic tutoring; etc.). Keep the tone supportive and conversational."
            )

        # Build contents array with history and current message
        contents = []
        for msg in chat_history:
            role = 'user' if msg.get('role') == 'user' else 'model'
            contents.append({
                "role": role,
                "parts": [{"text": msg.get('text', '')}]
            })

        # Append the new user message
        contents.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })

        # Construct payload
        payload = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        # Make call to Gemini API
        print(f"Calling Gemini API for counselor response...")
        resp = requests.post(gemini_url, headers=headers, json=payload)
        
        if resp.status_code != 200:
            print("Gemini API call failed with status:", resp.status_code)
            print("Response:", resp.text)
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch counseling response from Gemini API.'
            }), 500

        resp_data = resp.json()
        
        try:
            model_response = resp_data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError) as parse_err:
            print("Error parsing Gemini API response format:", parse_err)
            print("Response raw:", resp_data)
            return jsonify({
                'status': 'error',
                'message': 'Error parsing counselor response format.'
            }), 500

        return jsonify({
            'status': 'success',
            'response': model_response
        })

    except Exception as e:
        print("Error in /chat:")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Server chat error: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Start flask app
    app.run(host='127.0.0.1', port=5000, debug=True)
