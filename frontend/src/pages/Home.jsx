import { useState } from 'react'
import PredictionForm from '../components/PredictionForm'
import PredictionCard from '../components/PredictionCard'
import ExplanationPanel from '../components/ExplanationPanel'
import { explainPrediction } from '../services/api'

export default function Home() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(formData) {
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const payload = {
        ...formData,
        model_type: formData.model_type || 'baseline',
      }

      const data = await explainPrediction(payload)
      setResult(data)
    } catch (err) {
      console.error('Prediction error:', err)
      setError(err.response?.data?.error || err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="container">
        <h1>NBA AI Analytics Assistant</h1>
        <p className="subtitle">
          Predict a player's point total and generate a grounded explanation.
        </p>

        <PredictionForm onSubmit={handleSubmit} loading={loading} />

        {error && <div className="error">{error}</div>}

        {loading && (
          <div className="loading-overlay">
            <div className="spinner" />
            <p className="loading-text">Analyzing player data…</p>
          </div>
        )}

        {result && !loading && (
          <>
            <PredictionCard result={result} />
            <ExplanationPanel
              explanation={result.explanation}
              explanationType={result.explanation_type}
              context={result.context}
            />
          </>
        )}
      </div>
    </div>
  )
}
