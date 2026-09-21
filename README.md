# 🚗 AI Agent for Automated Vehicle Document Renewal Reminder

An intelligent, full-stack vehicle compliance and document renewal reminder system built with **Python**, **Gradio**, and the **xAI Grok API** using `python-dotenv`.

---

## 🎯 Objective & Overview
Helps vehicle owners track important vehicle-related documents and automatically identifies documents that are expired or approaching their expiry date.

### 📋 Documents Tracked
1. **Vehicle Registration Certificate (RC)**
2. **Vehicle Insurance**
3. **Pollution Under Control Certificate (PUC)**
4. **Driving Licence (DL)**

---

## ⚙️ Key Technical Features

1. **Deterministic Python Date Arithmetic**:
   - Days remaining are calculated strictly in pure Python (`document_evaluator.py`) rather than relying on AI guessing.
   - Categorization:
     - 🔴 **EXPIRED**: Expiry date has passed (`days < 0`)
     - 🟠 **URGENT**: Expires within 7 days (`0 <= days <= 7`)
     - 🟡 **RENEW SOON**: Expires within 30 days (`8 <= days <= 30`)
     - 🟢 **VALID**: More than 30 days remaining (`days > 30`)

2. **Grok AI Agent (`grok-2-latest`)**:
   - Securely loads `XAI_API_KEY` via `python-dotenv` from `.env`.
   - Never invents document dates or vehicle details.
   - Generates the exact structured response format required:
     ```
     Vehicle: [vehicle number]

     Document Status:
     - RC: [status] – [days remaining]
     - Insurance: [status] – [days remaining]
     - PUC: [status] – [days remaining]
     - Driving Licence: [status] – [days remaining]

     Priority:
     [Identifies which document needs attention first based on the earliest expiry date]

     Reminder:
     [Generates a short, clear and professional reminder for the vehicle owner]
     ```

3. **Interactive AI Vehicle Assistant Chatbot**:
   - Ready with preset query prompts:
     - *"Which document should I renew first?"*
     - *"Which documents are expiring soon?"*
     - *"Give me a renewal reminder."*
     - *"What is the status of my vehicle documents?"*

4. **College Project Features**:
   - 📝 **1-Click "Load Demo Vehicle Data"** button to instantly populate realistic dates (demonstrating all 4 categories: Expired, Urgent, Renew Soon, and Valid).
   - 🔄 **Reset / Clear** button to easily reset inputs and cards.
   - Modern, clean layout with visual cards and status badges.
   - 🛡️ Disclaimer banner: *"This system is an automated reminder tool, not a legal or government verification system."*

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Grok API Key (Optional)
Create or edit the `.env` file:
```env
XAI_API_KEY=your_xai_api_key_here
```
*(Note: If no key is set, the application operates seamlessly using its built-in intelligent fallback agent without errors.)*

### 3. Run the Web Application
```bash
python app.py
```
Open your browser at:
```
http://127.0.0.1:7860
```

### 4. Run the Test Suite
```bash
python -m unittest tests/test_renewal_system.py
```

---

## 📁 Project Structure

```
vehicle_renewal_agent/
│
├── app.py                     # Gradio UI with form, cards, AI output, and chatbot
├── document_evaluator.py      # Pure Python date calculations & priority logic
├── grok_agent.py              # Grok AI agent integration, strict formatting & chatbot
├── requirements.txt           # Project dependencies (gradio, httpx, python-dotenv)
├── .env.example               # Environment variable template
├── .env                       # Local environment file for XAI_API_KEY
├── README.md                  # Documentation and setup instructions
└── tests/
    └── test_renewal_system.py # Complete unit test suite
```
