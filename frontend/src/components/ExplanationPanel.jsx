export default function ExplanationPanel({ explanation, context }) {
  return (
    <div className="card">
      <h2>Grounded Explanation</h2>
      <p>{explanation}</p>
      <h3>Supporting Context</h3>
      <ul>
        <li>Season average points: {context.season_avg_points}</li>
        <li>Last 5 average points: {context.last_5_avg_points}</li>
        <li>Last game points: {context.last_game_points}</li>
        <li>Recent points: {context.recent_points.join(', ')}</li>
      </ul>
    </div>
  )
}
