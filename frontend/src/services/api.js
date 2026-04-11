import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
})

export async function explainPrediction(payload) {
  const response = await api.post('/explain', payload)
  return response.data
}
