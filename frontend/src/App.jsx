import { useState } from 'react'
import PredictionForm from './components/PredictionForm'
import { explainPrediction } from './services/api'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(formData) {
    setLoading(true)
    setError('')

    try {
      const payload = {
        ...formData,
        model_type: formData.model_type || 'baseline',
      }

      const data = await explainPrediction(payload)
      console.log('API result:', data)
      setResult(data)
    } catch (err) {
      console.error('Prediction error:', err)
      setError(err.response?.data?.error || err.message || 'Request failed')
      setResult(null)
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

        {result && (
          <div className="card">
            <h2>Prediction Result</h2>
            <p><strong>Player:</strong> {result.player_name ?? 'N/A'}</p>
            <p><strong>Stat:</strong> {result.stat ?? 'N/A'}</p>
            <p><strong>Threshold:</strong> {result.threshold ?? 'N/A'}</p>
            <p><strong>Model Used:</strong> {result.model_type ?? 'baseline'}</p>
            <p><strong>Predicted Value:</strong> {result.predicted_value ?? 'N/A'}</p>
            <p><strong>Probability:</strong> {result.probability_over_threshold ?? 'N/A'}</p>
            <p><strong>Explanation Type:</strong> {result.explanation_type ?? 'N/A'}</p>
            <p><strong>Explanation:</strong> {result.explanation ?? 'No explanation returned.'}</p>

            {result.context && (
              <>
                <h3>Context</h3>
                <p><strong>Last 5 Avg:</strong> {result.context.last_5_avg ?? 'N/A'}</p>
                <p><strong>Season Avg:</strong> {result.context.season_avg ?? 'N/A'}</p>
                <p>
                  <strong>Recent Values:</strong>{' '}
                  {Array.isArray(result.context.recent_values)
                    ? result.context.recent_values.join(', ')
                    : 'N/A'}
                </p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}