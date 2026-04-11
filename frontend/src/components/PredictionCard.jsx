export default function PredictionCard({ result }) {
  return (
    <div className="card">
      <h2>Prediction Result</h2>
      <p><strong>Player:</strong> {result.player_name}</p>
      <p><strong>Predicted points:</strong> {result.predicted_value}</p>
      <p><strong>Threshold:</strong> {result.threshold}</p>
      <p><strong>Probability over threshold:</strong> {(result.probability_over_threshold * 100).toFixed(1)}%</p>
      <p><strong>Model residual std:</strong> {result.model_residual_std}</p>
    </div>
  )
}
