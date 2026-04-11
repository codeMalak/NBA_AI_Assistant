# Architecture Overview

User -> React UI -> Flask API -> Prediction Service + Retrieval Service + Explanation Service

## Prediction Service
- Loads trained regression model
- Predicts expected points
- Converts expected points into threshold probability using residual error

## Retrieval Service
- Pulls recent player game stats from processed dataset
- Builds grounded context for the explanation system

## Explanation Service
- Currently template-based fallback
- Intended upgrade: Hugging Face model/API using retrieved context in the prompt
