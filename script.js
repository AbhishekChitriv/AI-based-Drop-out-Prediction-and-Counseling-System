// --- AUTH OVERLAY SELECTORS ---
const authOverlay = document.getElementById('auth-overlay');
const authEmailForm = document.getElementById('auth-email-form');
const authEmailInput = document.getElementById('auth-email');
const authEmailSubmit = document.getElementById('auth-email-submit');
const authOtpForm = document.getElementById('auth-otp-form');
const authOtpInput = document.getElementById('auth-otp');
const authOtpSubmit = document.getElementById('auth-otp-submit');
const authOtpTimer = document.getElementById('auth-otp-timer');
const authBackBtn = document.getElementById('auth-back-btn');
const authResendBtn = document.getElementById('auth-resend-btn');

let verifiedEmail = "";
let timerInterval = null;

// Lock page scrolling initially when auth overlay is visible
if (authOverlay && !authOverlay.classList.contains('hidden')) {
    document.body.style.overflow = 'hidden';
}

// --- OTP TIMER MANAGEMENT ---
function startOTPTimer(durationSeconds) {
    clearInterval(timerInterval);
    let timeRemaining = durationSeconds;
    
    function updateTimerDisplay() {
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        if (authOtpTimer) {
            authOtpTimer.innerText = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        
        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            if (authOtpTimer) {
                authOtpTimer.innerText = "EXPIRED";
                authOtpTimer.className = "text-xs font-bold text-red-500 bg-red-500/10 px-2 py-0.5 rounded";
            }
            alert("Your verification code has expired. Please request a new code.");
        }
        timeRemaining--;
    }
    
    if (authOtpTimer) {
        authOtpTimer.className = "text-xs font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded";
    }
    updateTimerDisplay();
    timerInterval = setInterval(updateTimerDisplay, 1000);
}

// --- AUTHENTICATION INTERACTION FLOWS ---

// Stage 1: Send OTP Request
if (authEmailForm) {
    authEmailForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = authEmailInput.value.trim();
        if (!email) return;

        // UI Feedback - Disable button and input
        authEmailSubmit.disabled = true;
        authEmailInput.disabled = true;
        const originalBtnText = authEmailSubmit.innerHTML;
        authEmailSubmit.innerHTML = `<span>Sending Code...</span> <i class="fa-solid fa-circle-notch animate-spin text-xs"></i>`;

        try {
            const response = await fetch('/auth/send-otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email: email })
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                verifiedEmail = email;
                
                // Show Step 2 (OTP code input)
                authEmailForm.classList.add('hidden');
                authOtpForm.classList.remove('hidden');
                
                // Start 5-minute timer
                startOTPTimer(300);
                alert(result.message);
            } else {
                throw new Error(result.message || 'Failed to send OTP.');
            }
        } catch (err) {
            console.error('OTP send error:', err);
            alert(`Send Failed: ${err.message}`);
            
            // Re-enable inputs
            authEmailInput.disabled = false;
        } finally {
            authEmailSubmit.disabled = false;
            authEmailSubmit.innerHTML = originalBtnText;
        }
    });
}

// Stage 2: Verify OTP
if (authOtpForm) {
    authOtpForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const otp = authOtpInput.value.trim();
        if (!otp || otp.length !== 6) {
            alert('Please enter a valid 6-digit code.');
            return;
        }

        // UI Feedback
        authOtpSubmit.disabled = true;
        authOtpInput.disabled = true;
        const originalBtnText = authOtpSubmit.innerHTML;
        authOtpSubmit.innerHTML = `<span>Verifying...</span> <i class="fa-solid fa-circle-notch animate-spin text-xs"></i>`;

        try {
            const response = await fetch('/auth/verify-otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: verifiedEmail,
                    otp: otp
                })
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                clearInterval(timerInterval);
                
                // Hide Auth overlay and unlock dashboard
                authOverlay.classList.add('hidden');
                document.body.style.overflow = 'auto'; // Re-engage background scroll
                
                // Shrink dashboard layout to leave 25% space for chatbot
                document.querySelector('header')?.classList.add('with-sidebar');
                document.querySelector('main')?.classList.add('with-sidebar');
                document.querySelector('footer')?.classList.add('with-sidebar');
                
                // Show chatbot floating widget after login
                const chatbotFloatingContainer = document.getElementById('chatbot-floating-container');
                if (chatbotFloatingContainer) {
                    chatbotFloatingContainer.classList.remove('hidden');
                }
                
                // Show logout button
                const logoutBtnElement = document.getElementById('logout-btn');
                if (logoutBtnElement) {
                    logoutBtnElement.classList.remove('hidden');
                }
                
                // Update header login button to show verified email and remove listener
                const currentOpenLoginBtn = document.getElementById('open-login-btn');
                if (currentOpenLoginBtn) {
                    currentOpenLoginBtn.innerHTML = `
                      <div class="user-profile-inner" style="background-color: #0b0f17; border: 1px solid #10b981; color: #10b981; width: auto; max-width: 250px; padding: 0 16px;">
                        <svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="fill: #10b981;">
                          <g data-name="Layer 2" id="Layer_2">
                            <path d="m15.626 11.769a6 6 0 1 0 -7.252 0 9.008 9.008 0 0 0 -5.374 8.231 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 9.008 9.008 0 0 0 -5.374-8.231zm-7.626-4.769a4 4 0 1 1 4 4 4 4 0 0 1 -4-4zm10 14h-12a1 1 0 0 1 -1-1 7 7 0 0 1 14 0 1 1 0 0 1 -1 1z"></path>
                          </g>
                        </svg>
                        <p style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 12px; font-weight: 600;">${verifiedEmail}</p>
                      </div>
                    `;
                    currentOpenLoginBtn.style.width = "auto";
                    currentOpenLoginBtn.style.background = "linear-gradient(to bottom right, #10b981 0%, rgba(16, 185, 129, 0) 30%)";
                    currentOpenLoginBtn.style.backgroundColor = "rgba(16, 185, 129, 0.2)";
                    currentOpenLoginBtn.className = "user-profile cursor-default";
                    const newOpenLoginBtn = currentOpenLoginBtn.cloneNode(true);
                    currentOpenLoginBtn.parentNode.replaceChild(newOpenLoginBtn, currentOpenLoginBtn);
                }
            } else {
                throw new Error(result.message || 'Invalid verification code.');
            }
        } catch (err) {
            console.error('Verification error:', err);
            alert(`Verification Failed: ${err.message}`);
            
            // Re-enable inputs
            authOtpInput.disabled = false;
        } finally {
            authOtpSubmit.disabled = false;
            authOtpSubmit.innerHTML = originalBtnText;
        }
    });
}

// Back Button Action
if (authBackBtn) {
    authBackBtn.addEventListener('click', () => {
        clearInterval(timerInterval);
        authOtpForm.classList.add('hidden');
        authEmailForm.classList.remove('hidden');
        authEmailInput.disabled = false;
        authOtpInput.disabled = false;
        authOtpInput.value = "";
    });
}

// Resend OTP Action
if (authResendBtn) {
    authResendBtn.addEventListener('click', async () => {
        authResendBtn.disabled = true;
        const originalText = authResendBtn.innerText;
        authResendBtn.innerText = "Sending...";

        try {
            const response = await fetch('/auth/send-otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email: verifiedEmail })
            });

            const result = await response.json();
            if (response.ok && result.status === 'success') {
                startOTPTimer(300);
                alert('A new verification code has been sent.');
            } else {
                throw new Error(result.message || 'Failed to resend code.');
            }
        } catch (err) {
            console.error('Resend error:', err);
            alert(`Resend Failed: ${err.message}`);
        } finally {
            authResendBtn.disabled = false;
            authResendBtn.innerText = originalText;
        }
    });
}


// --- MAIN APP CODE (PREDICTORS & DASHBOARD) ---

// Document Selection Selectors Setup
const loginModal = document.getElementById('login-modal');
const openLoginBtn = document.getElementById('open-login-btn');
const heroGetStartedBtn = document.getElementById('hero-get-started-btn');
const closeModalBtn = document.getElementById('close-modal-btn');
const loginForm = document.getElementById('login-form');

// --- PREDICTOR SELECTORS ---
const predictionForm = document.getElementById('prediction-form');
const predictorName = document.getElementById('predictor-name');
const predictorEducation = document.getElementById('predictor-education');
const predictorAge = document.getElementById('predictor-age');
const predictorIncome = document.getElementById('predictor-income');
const predictorStudyHours = document.getElementById('predictor-study-hours');
const predictorAttendance = document.getElementById('predictor-attendance');
const predictorDelay = document.getElementById('predictor-delay');
const predictorTravel = document.getElementById('predictor-travel');
const predictorGpa = document.getElementById('predictor-gpa');
const predictorStress = document.getElementById('predictor-stress');

// Slider Values Labels
const studyHoursVal = document.getElementById('study-hours-val');
const attendanceVal = document.getElementById('attendance-val');
const stressVal = document.getElementById('stress-val');

// Results Panel States
const resultsPlaceholder = document.getElementById('results-placeholder');
const resultsLoading = document.getElementById('results-loading');
const resultsDisplay = document.getElementById('results-display');

// Prediction Output Fields
const resultStudentTitle = document.getElementById('result-student-title');
const resultEducationLevel = document.getElementById('result-education-level');
const resultProgressRing = document.getElementById('result-progress-ring');
const resultRiskPercentage = document.getElementById('result-risk-percentage');
const resultRiskBadge = document.getElementById('result-risk-badge');
const resultRecommendation = document.getElementById('result-recommendation');

const resetPredictionBtn = document.getElementById('reset-prediction-btn');
const addToDashboardBtn = document.getElementById('add-to-dashboard-btn');
const discussCounselorBtn = document.getElementById('discuss-counselor-btn');
const dashboardTableBody = document.querySelector('#analytics tbody');

// Cache last prediction details for dashboard save action
let lastPredictionResult = null;

// Modal Toggling Action Functions
function toggleModal(show) {
    if (show) {
        loginModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Lock context background scroll
    } else {
        loginModal.classList.add('hidden');
        document.body.style.overflow = 'auto'; // Re-engage background scroll
    }
}

// Event Listeners Assignments
if (openLoginBtn) openLoginBtn.addEventListener('click', () => toggleModal(true));
if (heroGetStartedBtn) {
    heroGetStartedBtn.addEventListener('click', () => {
        const predictorSection = document.getElementById('predictor');
        if (predictorSection) {
            predictorSection.scrollIntoView({ behavior: 'smooth' });
        }
    });
}
if (closeModalBtn) closeModalBtn.addEventListener('click', () => toggleModal(false));

// Close Modal if user clicks on the dark background mask
if (loginModal) {
    loginModal.addEventListener('click', (event) => {
        if (event.target === loginModal) {
            toggleModal(false);
        }
    });
}

// Mock Authentication Submission Handler
if (loginForm) {
    loginForm.addEventListener('submit', (event) => {
        event.preventDefault();
        alert('Logged in securely! Redirecting to counselor prediction console indices...');
        toggleModal(false);
    });
}

// Interactive Dashboard Row Trigger Confirmation Action 
function bindCounselButtons() {
    const dispatchCounselBtns = document.querySelectorAll('.dispatch-counsel-btn');
    dispatchCounselBtns.forEach((btn) => {
        // Remove old listener to prevent duplicates
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        newBtn.addEventListener('click', (event) => {
            const row = event.target.closest('tr');
            const studentRowName = row.querySelector('td').innerText.trim();
            const riskText = row.querySelectorAll('td')[1].innerText;

            // Extract risk percentage
            const pctMatch = riskText.match(/(\d+)%/);
            const riskPct = pctMatch ? parseFloat(pctMatch[1]) : 50;

            // Student profile definitions
            const staticStudentData = {
                "John Doe": {
                    name: "John Doe",
                    risk_probability: 87,
                    GPA: 1.8,
                    Attendance_Rate: 65.0,
                    Study_Hours_per_Day: 2.5,
                    Assignment_Delay_Days: 8,
                    Travel_Time_Minutes: 45,
                    Stress_Index: 7,
                    Age: 22,
                    Family_Income: 35000,
                    Education_Level: "High School"
                },
                "Amara Smith": {
                    name: "Amara Smith",
                    risk_probability: 54,
                    GPA: 2.4,
                    Attendance_Rate: 78.0,
                    Study_Hours_per_Day: 4.0,
                    Assignment_Delay_Days: 4,
                    Travel_Time_Minutes: 20,
                    Stress_Index: 5,
                    Age: 20,
                    Family_Income: 48000,
                    Education_Level: "Bachelor"
                }
            };

            // Retrieve context from static profiles or prediction cache
            if (staticStudentData[studentRowName]) {
                activeStudentContext = staticStudentData[studentRowName];
            } else if (lastPredictionResult && lastPredictionResult.name === studentRowName) {
                activeStudentContext = lastPredictionResult;
            } else {
                // Construct fallback default context
                activeStudentContext = {
                    name: studentRowName,
                    risk_probability: riskPct,
                    GPA: 2.8,
                    Attendance_Rate: 85.0,
                    Study_Hours_per_Day: 5.0,
                    Assignment_Delay_Days: 2,
                    Travel_Time_Minutes: 30,
                    Stress_Index: 4,
                    Age: 21,
                    Family_Income: 40000,
                    Education_Level: "Bachelor"
                };
            }

            // Reset chat history and messages stream
            chatHistory = [];
            chatMessagesContainer.innerHTML = "";

            // Open chat panel and clear badge
            chatWidgetPanel.classList.remove('hidden');
            chatNotificationBadge.classList.add('hidden');

            // Add context load welcome message
            const riskLabel = activeStudentContext.risk_probability >= 70 ? "Critical Risk" : (activeStudentContext.risk_probability >= 30 ? "Medium Risk" : "Low Risk");
            const welcomeText = `AI Counselor has loaded **${activeStudentContext.name}**'s academic profile (Risk: **${activeStudentContext.risk_probability}% ${riskLabel}**, GPA: **${activeStudentContext.GPA}**, Attendance: **${activeStudentContext.Attendance_Rate}%**).\n\nHow can I help you compile coping plans or analyze risk indicators for ${activeStudentContext.name}?`;
            
            appendMessage('model', welcomeText);
            chatHistory.push({ role: 'model', text: welcomeText });
            scrollToBottom();

            // Scroll to the chatbot floating trigger area smoothly
            chatWidgetPanel.scrollIntoView({ behavior: 'smooth', block: 'end' });
        });
    });
}

// Bind initial buttons
bindCounselButtons();

// --- PREDICTOR INTERACTION INTERFACES ---

// Update Slider value displays in real time
if (predictorStudyHours) {
    predictorStudyHours.addEventListener('input', (e) => {
        studyHoursVal.innerText = `${parseFloat(e.target.value).toFixed(1)} hrs`;
    });
}

if (predictorAttendance) {
    predictorAttendance.addEventListener('input', (e) => {
        attendanceVal.innerText = `${e.target.value}%`;
    });
}

if (predictorStress) {
    predictorStress.addEventListener('input', (e) => {
        stressVal.innerText = `${e.target.value}/10`;
    });
}

// Form Submission & ML Predict API call
if (predictionForm) {
    predictionForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 1. Shift UI state to loading
        resultsPlaceholder.classList.add('hidden');
        resultsDisplay.classList.add('hidden');
        resultsLoading.classList.remove('hidden');

        // 2. Fetch input parameters
        const payload = {
            Age: parseInt(predictorAge.value),
            Family_Income: parseFloat(predictorIncome.value),
            Study_Hours_per_Day: parseFloat(predictorStudyHours.value),
            Attendance_Rate: parseFloat(predictorAttendance.value),
            Assignment_Delay_Days: parseInt(predictorDelay.value),
            Travel_Time_Minutes: parseInt(predictorTravel.value),
            Stress_Index: parseInt(predictorStress.value),
            GPA: parseFloat(predictorGpa.value),
            Education_Level: predictorEducation.value
        };

        const studentName = predictorName.value || "Jane Doe";

        try {
            // 3. Make POST request to Flask Predict endpoint
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Server returned an error status.');
            }

            const result = await response.json();

            if (result.status === 'success') {
                // Store result for dashboard addition and chat context
                lastPredictionResult = {
                    name: studentName,
                    risk_probability: result.risk_probability,
                    prediction: result.prediction,
                    education_level: payload.Education_Level,
                    encoded_education_level: result.encoded_education_level,
                    GPA: payload.GPA,
                    Attendance_Rate: payload.Attendance_Rate,
                    Study_Hours_per_Day: payload.Study_Hours_per_Day,
                    Assignment_Delay_Days: payload.Assignment_Delay_Days,
                    Stress_Index: payload.Stress_Index,
                    Age: payload.Age,
                    Family_Income: payload.Family_Income,
                    Travel_Time_Minutes: payload.Travel_Time_Minutes
                };

                // 4. Update display fields
                resultStudentTitle.innerText = studentName;
                resultEducationLevel.innerText = `Education Level: ${payload.Education_Level} (Encoded Code: ${result.encoded_education_level})`;
                resultRiskPercentage.innerText = `${result.risk_probability}%`;

                // Update Progress Ring (radius = 42, circumference = 263.89)
                const circumference = 2 * Math.PI * 42;
                const offset = circumference - (circumference * result.risk_probability) / 100;
                resultProgressRing.style.strokeDasharray = `${circumference}`;
                resultProgressRing.style.strokeDashoffset = `${offset}`;

                // Update risk badge classes and recommendations
                let badgeText = "LOW RISK";
                let badgeClasses = ["bg-lime-500/10", "text-lime-400", "border-lime-500/30"];
                let recommendationText = "Student is currently stable. Maintain standard academic observation and periodic progress checks.";

                // Clear previous badge classes
                resultRiskBadge.className = "mt-4 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border";

                if (result.risk_probability >= 70) {
                    badgeText = "CRITICAL RISK";
                    badgeClasses = ["bg-red-500/10", "text-red-400", "border-red-500/30"];
                    recommendationText = "High risk cohort flagged. Recommend dispatching immediate personal counseling invites and academic tutoring support.";
                    
                    // Show notification badge on chat floating trigger
                    if (chatNotificationBadge) {
                        chatNotificationBadge.innerText = "!";
                        chatNotificationBadge.classList.remove('hidden');
                    }
                } else if (result.risk_probability >= 30) {
                    badgeText = "MEDIUM RISK";
                    badgeClasses = ["bg-amber-500/10", "text-amber-400", "border-amber-500/30"];
                    
                    if (payload.Attendance_Rate < 75) {
                        recommendationText = "Attendance deficit detected. Schedule an informal review session to identify transportation or family complications.";
                    } else if (payload.GPA < 2.5) {
                        recommendationText = "Academic grades require support. Recommend assignment mentoring and extra subject practice classes.";
                    } else {
                        recommendationText = "Elevated risk signals. Suggest coordinating counseling outreach modules and periodic mentoring reviews.";
                    }
                } else {
                    // Low risk recommendation enhancements
                    if (payload.Stress_Index > 7) {
                        recommendationText = "Student is academically sound but reports high stress levels. Advise mental wellness resources or counselor chats.";
                    }
                }

                resultRiskBadge.innerText = badgeText;
                badgeClasses.forEach(c => resultRiskBadge.classList.add(c));
                resultRecommendation.innerText = recommendationText;

                // Transition states
                resultsLoading.classList.add('hidden');
                resultsDisplay.classList.remove('hidden');
            } else {
                throw new Error(result.message || 'Failed to analyze prediction.');
            }

        } catch (error) {
            console.error('Prediction error:', error);
            alert(`Prediction Failed: ${error.message}`);
            
            // Revert state
            resultsLoading.classList.add('hidden');
            resultsPlaceholder.classList.remove('hidden');
        }
    });
}

// Reset Predictor panel
if (resetPredictionBtn) {
    resetPredictionBtn.addEventListener('click', () => {
        resultsDisplay.classList.add('hidden');
        resultsPlaceholder.classList.remove('hidden');
        lastPredictionResult = null;
        predictionForm.reset();
        
        // Reset slider displays
        studyHoursVal.innerText = "6.0 hrs";
        attendanceVal.innerText = "88%";
        stressVal.innerText = "4/10";
    });
}

// Save student prediction to local dashboard view list
if (addToDashboardBtn) {
    addToDashboardBtn.addEventListener('click', () => {
        if (!lastPredictionResult) return;

        const { name, risk_probability } = lastPredictionResult;

        // Create elements based on risk level
        let badgeColorClass = "bg-lime-500/10 text-lime-400";
        let badgeLabel = "LOW";
        let btnBorderClass = "border border-gray-700 text-gray-300 hover:border-lime-400";

        if (risk_probability >= 70) {
            badgeColorClass = "bg-red-500/10 text-red-400";
            badgeLabel = "CRITICAL";
            btnBorderClass = "bg-lime-400 text-black hover:bg-lime-500";
        } else if (risk_probability >= 30) {
            badgeColorClass = "bg-amber-500/10 text-amber-400";
            badgeLabel = "MEDIUM";
            btnBorderClass = "border border-gray-700 text-gray-300 hover:border-lime-400";
        }

        // Generate new row elements
        const newRow = document.createElement('tr');
        newRow.innerHTML = `
            <td class="py-4 font-medium text-white">${name}</td>
            <td class="py-4"><span class="${badgeColorClass} px-2 py-0.5 rounded font-bold">${risk_probability}% ${badgeLabel}</span></td>
            <td class="py-4 text-right">
                <button class="${btnBorderClass} px-3 py-1 rounded font-bold transition dispatch-counsel-btn">Counsel AI</button>
            </td>
        `;

        // Prepend row to table
        if (dashboardTableBody) {
            dashboardTableBody.insertBefore(newRow, dashboardTableBody.firstChild);
            
            // Re-bind actions
            bindCounselButtons();

            alert(`Successfully added ${name} (${risk_probability}% Risk) to the Real-Time Counselor Dashboard!`);
            
            // Auto scroll or focus down to analytics section
            document.getElementById('analytics').scrollIntoView({ behavior: 'smooth' });
        }
    });
}


// --- CHATBOT WIDGET INTERACTION HANDLING ---
const chatWidgetPanel = document.getElementById('chat-widget-panel');
const chatTriggerBtn = document.getElementById('chat-trigger-btn');
const chatCloseBtn = document.getElementById('chat-close-btn');
const chatMessagesContainer = document.getElementById('chat-messages-container');
const chatInputForm = document.getElementById('chat-input-form');
const chatMessageInput = document.getElementById('chat-message-input');
const chatSendBtn = document.getElementById('chat-send-btn');
const chatNotificationBadge = document.getElementById('chat-notification-badge');

let chatHistory = [];
let activeStudentContext = null;

// Toggle Chat Widget Window
if (chatTriggerBtn) {
    chatTriggerBtn.addEventListener('click', () => {
        chatWidgetPanel.classList.toggle('hidden');
        if (!chatWidgetPanel.classList.contains('hidden')) {
            // Hide notification badge when opened
            chatNotificationBadge.classList.add('hidden');
            // Scroll message log to bottom
            scrollToBottom();
            chatMessageInput.focus();
        }
    });
}

if (chatCloseBtn) {
    chatCloseBtn.addEventListener('click', () => {
        chatWidgetPanel.classList.add('hidden');
    });
}

// Discuss with AI button integration from predictor results
if (discussCounselorBtn) {
    discussCounselorBtn.addEventListener('click', () => {
        if (!lastPredictionResult) {
            alert("Please complete a drop-out risk prediction first.");
            return;
        }

        // Set the active student context
        activeStudentContext = lastPredictionResult;

        // Reset chat history and messages stream
        chatHistory = [];
        chatMessagesContainer.innerHTML = "";

        // Open chat panel
        chatWidgetPanel.classList.remove('hidden');
        chatNotificationBadge.classList.add('hidden');

        // Add context load intro
        const riskLabel = activeStudentContext.risk_probability >= 70 ? "Critical Risk" : (activeStudentContext.risk_probability >= 30 ? "Medium Risk" : "Low Risk");
        const initText = `AI Counselor has loaded **${activeStudentContext.name}**'s academic profile (Risk: **${activeStudentContext.risk_probability}% ${riskLabel}**, GPA: **${activeStudentContext.GPA}**, Attendance: **${activeStudentContext.Attendance_Rate}%**).\n\nHow can I help you compile coping plans or analyze risk indicators for ${activeStudentContext.name}?`;
        
        appendMessage('model', initText);
        chatHistory.push({ role: 'model', text: initText });
        scrollToBottom();
    });
}

// Handle sending messages
if (chatInputForm) {
    chatInputForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = chatMessageInput.value.trim();
        if (!message) return;

        // Clear input
        chatMessageInput.value = "";

        // 1. Add user message bubble
        appendMessage('user', message);
        chatHistory.push({ role: 'user', text: message });
        scrollToBottom();

        // 2. Add typing indicator
        const typingIndicator = appendTypingIndicator();
        scrollToBottom();

        try {
            // 3. POST to /chat endpoint
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    history: chatHistory,
                    student_context: activeStudentContext
                })
            });

            if (!response.ok) {
                throw new Error('Chat API returned an error status.');
            }

            const result = await response.json();

            // Remove typing indicator
            typingIndicator.remove();

            if (result.status === 'success') {
                appendMessage('model', result.response);
                chatHistory.push({ role: 'model', text: result.response });
                scrollToBottom();
            } else {
                throw new Error(result.message || 'Verification error.');
            }

        } catch (error) {
            console.error('Chat error:', error);
            typingIndicator.remove();
            appendMessage('model', "⚠️ Failed to connect to AI Counselor server. Please verify connections.");
            scrollToBottom();
        }
    });
}

// Bind quick suggestion chips
const suggestionChips = document.querySelectorAll('.chat-suggestion-chip');
suggestionChips.forEach(chip => {
    chip.addEventListener('click', (e) => {
        e.preventDefault();
        chatMessageInput.value = chip.innerText.trim();
        if (chatSendBtn) {
            chatSendBtn.click();
        } else {
            chatInputForm.dispatchEvent(new Event('submit', { cancelable: true }));
        }
    });
});

// Helper: Scroll messages container to bottom
function scrollToBottom() {
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

// Helper: Append msg bubble to container
function appendMessage(role, text) {
    const bubbleWrapper = document.createElement('div');
    bubbleWrapper.className = role === 'user' ? 'flex justify-end w-full' : 'flex items-start gap-2.5 max-w-[85%]';
    
    // Convert basic markdown tags (**bold**) to html
    const formattedText = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    if (role === 'user') {
        bubbleWrapper.innerHTML = `
            <div class="bg-lime-400 text-black p-3 rounded-2xl rounded-tr-none leading-relaxed max-w-[85%] break-words">
                ${formattedText}
            </div>
        `;
    } else {
        bubbleWrapper.innerHTML = `
            <img src="counselor_avatar.jpg" class="w-6 h-6 rounded-md object-cover shrink-0" alt="Counselor Avatar">
            <div class="bg-gray-950 border border-gray-800 text-gray-300 p-3 rounded-2xl rounded-tl-none leading-relaxed break-words">
                ${formattedText}
            </div>
        `;
    }

    chatMessagesContainer.appendChild(bubbleWrapper);
}

// Helper: Append typing dots
function appendTypingIndicator() {
    const indicatorWrapper = document.createElement('div');
    indicatorWrapper.className = 'flex items-start gap-2.5 max-w-[85%]';
    indicatorWrapper.innerHTML = `
        <img src="counselor_avatar.jpg" class="w-6 h-6 rounded-md object-cover shrink-0" alt="Counselor Avatar">
        <div class="bg-gray-950 border border-gray-800 text-gray-400 p-3 rounded-2xl rounded-tl-none flex items-center gap-1">
            <span class="w-1.5 h-1.5 bg-lime-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
            <span class="w-1.5 h-1.5 bg-lime-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
            <span class="w-1.5 h-1.5 bg-lime-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
        </div>
    `;
    chatMessagesContainer.appendChild(indicatorWrapper);
    return indicatorWrapper;
}

// Logout Action Trigger Handler
const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        // Clear session details
        verifiedEmail = "";
        
        // Restore standard dashboard full width
        document.querySelector('header')?.classList.remove('with-sidebar');
        document.querySelector('main')?.classList.remove('with-sidebar');
        document.querySelector('footer')?.classList.remove('with-sidebar');
        
        // Hide chatbot floating page and dashboard controls overlay block
        const chatbotFloatingContainer = document.getElementById('chatbot-floating-container');
        if (chatbotFloatingContainer) {
            chatbotFloatingContainer.classList.add('hidden');
        }
        
        // Hide logout button
        logoutBtn.classList.add('hidden');
        
        // Restore standard login button HTML and styles in header
        const currentOpenLoginBtn = document.getElementById('open-login-btn');
        if (currentOpenLoginBtn) {
            currentOpenLoginBtn.innerHTML = `
              <div class="user-profile-inner">
                <svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                  <g data-name="Layer 2" id="Layer_2">
                    <path d="m15.626 11.769a6 6 0 1 0 -7.252 0 9.008 9.008 0 0 0 -5.374 8.231 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 9.008 9.008 0 0 0 -5.374-8.231zm-7.626-4.769a4 4 0 1 1 4 4 4 4 0 0 1 -4-4zm10 14h-12a1 1 0 0 1 -1-1 7 7 0 0 1 14 0 1 1 0 0 1 -1 1z"></path>
                  </g>
                </svg>
                <p>Log In</p>
              </div>
            `;
            // Reset styles
            currentOpenLoginBtn.style.width = "";
            currentOpenLoginBtn.style.background = "";
            currentOpenLoginBtn.style.backgroundColor = "";
            currentOpenLoginBtn.className = "user-profile";
            
            // Re-clone or re-enable the click listener to open modal
            const newOpenLoginBtn = currentOpenLoginBtn.cloneNode(true);
            newOpenLoginBtn.addEventListener('click', () => toggleModal(true));
            currentOpenLoginBtn.parentNode.replaceChild(newOpenLoginBtn, currentOpenLoginBtn);
        }
        
        // Show Auth Overlay back (lock portal)
        const authOverlay = document.getElementById('auth-overlay');
        const authEmailInput = document.getElementById('auth-email');
        const authOtpInput = document.getElementById('auth-otp');
        const authOtpForm = document.getElementById('auth-otp-form');
        const authEmailForm = document.getElementById('auth-email-form');
        const authEmailSubmit = document.getElementById('auth-email-submit');
        
        if (authOverlay) {
            // Reset input values
            if (authEmailInput) {
                authEmailInput.value = "";
                authEmailInput.disabled = false;
            }
            if (authOtpInput) {
                authOtpInput.value = "";
                authOtpInput.disabled = false;
            }
            if (authOtpForm) authOtpForm.classList.add('hidden');
            if (authEmailForm) authEmailForm.classList.remove('hidden');
            if (authEmailSubmit) authEmailSubmit.disabled = false;
            
            authOverlay.classList.remove('hidden');
            document.body.style.overflow = 'hidden'; // Lock context background scroll
        }
    });
}