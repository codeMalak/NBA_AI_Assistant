# NBA AI Analytics Assistant

NBA AI Analytics Assistant is a CSC 603/803 capstone project focused on NBA player performance prediction and grounded AI explanations.

The app allows users to select an NBA game, choose a player, enter a points threshold, and receive:
1. an expected points prediction
2. the probability of exceeding the threshold
3. a grounded explanation based on retrieved NBA context

## Project Goal

Given an NBA player, stat, game context, and threshold, the app predicts whether the player is likely to exceed the selected stat threshold.

The current version focuses on **points predictions** and uses both historical player performance and enriched live-context features.

## Current Features

- NBA game selection by date
- Player selection by team/game
- Baseline and enriched model selection
- Points prediction
- Probability of exceeding threshold
- Grounded explanation using retrieved context
- Recent performance context
- Team and opponent context
- Injury and lineup-aware features
- Odds and advanced-stat feature support when available

## Tech Stack

- Backend: Flask, pandas, numpy, scikit-learn
- Frontend: React + Vite
- Data: BALLDONTLIE API
- Models: scikit-learn Random Forest regressors
- Explanation layer: Hugging Face model with template fallback
- Feature store: locally generated CSV pipeline

## Folder Structure

- `backend/` Flask API, model code, data pipeline, retrieval services, explanation services
- `backend/scripts/` data fetching, feature-store building, and model retraining scripts
- `backend/data/raw/` raw API data
- `backend/data/raw/context/` context data such as odds, injuries, lineups, and advanced stats
- `backend/data/processed/` processed feature store
- `backend/models/` trained model files
- `frontend/` React user interface
- `docs/` architecture notes, API contract, and implementation notes

## Requirements

Recommended:

- Python 3.12.10
- Node.js 20.19+ or 22.12+
- BALLDONTLIE API key
- Hugging Face token, optional but recommended for AI-generated explanations

## Quick Start

### Backend

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv .venv

# 3. Activate environment

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
# source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```


# Create a .env file inside backend/:
BALLDONTLIE_API_KEY=your_balldontlie_key
HF_API_TOKEN=your_huggingface_token


### Data Setup
# Run the scripts below from inside the backend/ folder.

```bash
# 1. Fetch NBA games/schedule
python scripts/fetch_historical_games.py

# 2. Fetch player game stats
python scripts/fetch_historical_stats.py

# 3. Fetch context snapshots: season averages, team averages, standings, injuries
python scripts/fetch_context_snapshots.py

# 4. Fetch betting odds when available
python scripts/fetch_odds.py

# 5. Fetch lineup data when available
python scripts/fetch_lineups.py

# 6. Fetch advanced game/player stats
python scripts/fetch_advanced_stats.py

# 7. Build the final feature store
python scripts/build_feature_store.py

# Train the baseline model(support has been discontinued)
python scripts/retrain_baseline_model.py

# Train the enriched model:
python scripts/retrain_enriched_model.py

# Run Backend API
python app.py
```


### Frontend
```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```


## Team Workflow
- Carlos: data pipeline, feature engineering, model training, Flask prediction API
- Jonathan: retrieval logic, prompts, grounded explanation system
- Joshua: React UI, API integration, result presentation
