export default function PredictionCard({ result }) {
  if (!result) return null

  const probability =
    result.probability_over_threshold != null
      ? `${(result.probability_over_threshold * 100).toFixed(1)}%`
      : 'N/A'

  return (
    <div className="card result-card">
      <div className="card-header">
        <div>
          <h2>Prediction Result</h2>
          <p>Model output for the selected player and threshold.</p>
        </div>
      </div>

      <div className="result-grid">
        <div className="result-item">
          <span className="result-label">Player</span>
          <span className="result-value">{result.player_name ?? 'N/A'}</span>
        </div>

        <div className="result-item">
          <span className="result-label">Stat</span>
          <span className="result-value">{result.stat ?? 'N/A'}</span>
        </div>

        <div className="result-item">
          <span className="result-label">Model</span>
          <span className="result-value">{result.model_type ?? 'N/A'}</span>
        </div>

        <div className="result-item">
          <span className="result-label">Threshold</span>
          <span className="result-value">{result.threshold ?? 'N/A'}</span>
        </div>

        <div className="result-item">
          <span className="result-label">Predicted Points</span>
          <span className="result-value">{result.predicted_value ?? 'N/A'}</span>
        </div>

        <div className="result-item">
          <span className="result-label">Probability Over Threshold</span>
          <span className="result-value">{probability}</span>
        </div>
      </div>
    </div>
  )
}