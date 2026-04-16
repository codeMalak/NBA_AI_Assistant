export default function PredictionCard({ result }) {
  const prob = result.probability_over_threshold
  const probPct = prob != null ? (prob * 100).toFixed(1) : null
  const probColor = prob == null ? '#9ca3af' : prob >= 0.6 ? '#16a34a' : prob >= 0.4 ? '#d97706' : '#dc2626'

  return (
    <div className="card">
      <h2>Prediction Result</h2>

      <div className="result-grid">
        <div className="result-item">
          <span className="result-label">Player</span>
          <span className="result-value">{result.player_name ?? 'N/A'}</span>
        </div>
        <div className="result-item">
          <span className="result-label">Stat</span>
          <span className="result-value">{result.stat ?? 'points'}</span>
        </div>
        <div className="result-item">
          <span className="result-label">Model</span>
          <span className="result-value badge badge-model">{result.model_type ?? 'baseline'}</span>
        </div>
        <div className="result-item">
          <span className="result-label">Threshold</span>
          <span className="result-value">{result.threshold ?? 'N/A'}</span>
        </div>
        <div className="result-item result-item--wide">
          <span className="result-label">Predicted Points</span>
          <span className="result-value result-value--large">
            {result.predicted_value != null ? Number(result.predicted_value).toFixed(1) : 'N/A'}
          </span>
        </div>
      </div>

      {probPct != null && (
        <div className="prob-section">
          <div className="prob-header">
            <span className="result-label">Probability over {result.threshold}</span>
            <span className="prob-pct" style={{ color: probColor }}>{probPct}%</span>
          </div>
          <div className="prob-track">
            <div
              className="prob-fill"
              style={{ width: `${probPct}%`, background: probColor }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
