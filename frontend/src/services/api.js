import axios from 'axios'

const API_BASE = 'http://127.0.0.1:5001/api'

export async function explainPrediction(payload) {
  const response = await axios.post(`${API_BASE}/explain`, payload)
  return response.data
}

export async function getGamesByDate(date) {
  const response = await axios.get(`${API_BASE}/games`, {
    params: { date },
  })
  return response.data
}

export async function getPlayers(team) {
  const response = await axios.get(`${API_BASE}/players`, {
    params: { team },
  })
  return response.data
}