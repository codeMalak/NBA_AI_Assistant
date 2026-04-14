# NBA AI Analytics Assistant

Starter scaffold for a CSC 603/803 capstone project focused on NBA player performance prediction and grounded AI explanations.

## Project Goal
Given an NBA player, a stat, and a threshold, the app should:
1. predict an expected stat value
2. estimate the probability of exceeding the threshold
3. generate a short grounded explanation using retrieved NBA statistics

## Suggested V1 Scope
- Sport: NBA
- Stats supported first: points
- Input: player name + threshold
- Output: expected points, probability over threshold, explanation

## Tech Stack
- Backend: Flask, pandas, numpy, scikit-learn
- Frontend: React + Vite
- Explanation layer: Hugging Face model or API, grounded with retrieved stats

## Folder Structure
- `backend/` Flask API, model code, data pipeline, retrieval and explanation services
- `frontend/` React user interface
- `docs/` architecture, API contract, implementation notes

## Quick Start
### Backend
```bash
# 1️⃣ Navigate to backend
cd backend

# 2️⃣ Create virtual environment
python -m venv .venv

# 3️⃣ Activate environment
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
# source .venv/bin/activate

# 4️⃣ Install dependencies
pip install -r requirements.txt

# 5️⃣ Create a .env file inside backend/:
# HF_API_TOKEN=your_huggingface_token
# BALLDONTLIE_API_KEY=your_balldontlie_key

# 6️⃣ Prepare Historical Dataset (Hugging Face)
python scripts/convert_hf_dataset.py

# 7️⃣ Fetch Live NBA Data
python scripts/fetch_recent_games.py

# 8️⃣ Merge Datasets
python scripts/merge_datasets.py

# 9️⃣ Train / Retrain Model
python scripts/retrain_model.py

# 🔟 Run Backend API
python app.py
```

### Frontend
```bash
# 1️⃣ Navigate to frontend
cd frontend

# 2️⃣ Install dependencies
npm install

# 3️⃣ Start development server
npm run dev
```


## Team Workflow
- Carlos: data pipeline, feature engineering, model training, Flask prediction API
- Jonathan: retrieval logic, prompts, grounded explanation system
- Joshua: React UI, API integration, result presentation
