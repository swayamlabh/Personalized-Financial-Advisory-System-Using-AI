🚀 Personalized Financial Advisory System using AI

An AI-powered financial assistant that helps users manage, analyze, and optimize their finances through intelligent insights, predictive modeling, and conversational guidance.

---

📌 Overview

The Personalized Financial Advisory System leverages Machine Learning, Time Series Forecasting, Anomaly Detection, and LLM-based interaction to deliver personalized financial insights.

It supports two user types:

- 👤 Individual Users
- 🏢 Organizations

The system provides:

- Financial tracking
- Predictive analytics
- Intelligent recommendations
- AI chatbot assistance

---

🎥 Demo
<img width="1901" height="908" alt="Screenshot 2026-04-18 052806" src="https://github.com/user-attachments/assets/b43afcb7-77d4-49f8-a113-440b16e42c5e" />

<img width="1421" height="912" alt="Screenshot 2026-04-18 053241" src="https://github.com/user-attachments/assets/2537c14c-5a2b-4a5c-a0e9-50f805e701a3" />


<img width="1733" height="902" alt="Screenshot 2026-04-18 053142" src="https://github.com/user-attachments/assets/1bb4873e-6cb2-4dee-9d97-1f0ae1569edb" />


<img width="1829" height="906" alt="Screenshot 2026-04-18 053152" src="https://github.com/user-attachments/assets/944a1eaa-3b78-43f1-b668-c7cbdabe45fe" />


<img width="1857" height="897" alt="Screenshot 2026-04-18 053232" src="https://github.com/user-attachments/assets/f620f386-6ade-4dd7-9079-55c19fbe5b59" />



---

🧠 Key Features

👤 Individual Dashboard

- Expense tracking & visualization
- Goal planning & monitoring
- Investment insights
- AI Financial Coach (LLM chatbot)

🏢 Organization Dashboard

- Manual financial data input
- Business insights & metrics
- Growth forecasting
- Advisory recommendations

🤖 AI Capabilities

- 📊 Prophet → Time-series forecasting
- 🧩 Isolation Forest → Anomaly detection
- 🔮 LSTM → Pattern recognition (future scope)
- 🧠 LLM Chatbot → Context-aware financial assistant
- 💡 XAI → Explainable insights

---

🏗️ Tech Stack

Frontend

- HTML, CSS, JavaScript
- Vercel Deployment

Backend

- FastAPI
- Uvicorn

Machine Learning

- Scikit-learn
- Pandas, NumPy
- Joblib

AI / LLM

- Google Generative AI (Gemini)

Auth & Security

- JWT (python-jose)
- Passlib (bcrypt)

Database

- SQLite (with persistent disk on Render)

---

📁 Project Structure

├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── chat_api.py
│   ├── engine.py
│   ├── ml/
│   ├── data/
│   ├── requirements.txt
│   └── database.sqlite
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── assets/
│
└── README.md

---

⚙️ Installation & Setup

1️⃣ Clone the Repository

[git clone https://github.com/YOUR_REPO_LINK](https://github.com/swayamlabh/Personalized-Financial-Advisory-System-Using-AI)
cd YOUR_PROJECT

---

2️⃣ Backend Setup

cd backend
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate (Windows)

pip install -r requirements.txt

---

3️⃣ Environment Variables

Create ".env" inside "backend/":

GOOGLE_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key

---

4️⃣ Run Backend

uvicorn main:app --reload

---

5️⃣ Run Frontend

Open:

frontend/index.html

OR deploy via Vercel.

---

🚀 Deployment

Backend (Render)

- Connect GitHub repo
- Root directory: "backend"
- Start command:

uvicorn main:app --host 0.0.0.0 --port 10000

- Add persistent disk:
  - Mount path: "/data"

---

Frontend (Vercel)

- Import GitHub repo
- Root directory: "frontend"
- Auto deploy enabled

---

🔐 Authentication Flow

- Individual:
  
  - "/signup"
  - "/login"

- Organization:
  
  - "/org_signup"
  - "/org_login"

JWT tokens are used for session handling.

---

📊 ML Pipeline Overview

1. Data Collection (manual / dataset)
2. Preprocessing
3. Feature Engineering
4. Model Execution:
   - Forecasting
   - Anomaly Detection
5. Insight Generation
6. Explanation Layer (XAI)

---

🤖 AI Chatbot

- Context-aware responses
- Uses financial insights as input
- Handles:
  - Savings strategies
  - Growth predictions
  - Expense optimization

---

⚠️ Limitations

- SQLite used (not ideal for large-scale production)
- Free-tier backend may sleep
- LSTM not fully integrated (future scope)

---

🔮 Future Improvements

- Replace SQLite with PostgreSQL (Supabase/Neon)
- Real-time data ingestion
- Advanced portfolio optimization
- Full LSTM integration
- Better explainability dashboard

---

👨‍💻 Contributors

- Vaibhav Kumar
- Swayam Labh
- Md Danish Nadeem
- Saurabh Dwivedi

---

📜 License

This project is for educational and hackathon purposes.

---

⚠️ Disclaimer

This system provides AI-based financial guidance and does not replace professional financial advice.

---

⭐ If you like this project, consider giving it a star!
