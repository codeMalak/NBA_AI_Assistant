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
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
python scripts_create_sample_data.py
python train_model.py
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Recommended Team Workflow
- Carlos: data pipeline, feature engineering, model training, Flask prediction API
- Jonathan: retrieval logic, prompts, grounded explanation system
- Joshua: React UI, API integration, result presentation

## Important Notes
- This scaffold uses a tiny generated sample dataset so the app can run end-to-end.
- Replace the sample data with real NBA game logs as your next step.
- The explanation service currently uses a template fallback. Plug in Hugging Face after the data + prediction path is working.
