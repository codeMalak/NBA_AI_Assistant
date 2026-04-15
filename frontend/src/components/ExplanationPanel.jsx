export default function ExplanationPanel({ explanation, explanationType, context }) {
  const isLLM = explanationType === 'llm'

  return (
    <div className="card">
      <div className="explanation-header">
        <h2>Grounded Explanation</h2>
        <span className={`badge ${isLLM ? 'badge-llm' : 'badge-template'}`}>
          {isLLM ? 'AI Generated' : 'Template'}
        </span>
      </div>

      <p className="explanation-text">{explanation ?? 'No explanation available.'}</p>

      {context && (
        <>
          <h3>Supporting Context</h3>
          <ul className="stat-list">
            <li>
              <span className="stat-label">Season Average</span>
              <span className="stat-value">
                {context.season_avg != null ? Number(context.season_avg).toFixed(1) : 'N/A'} pts
              </span>
            </li>
            <li>
              <span className="stat-label">Last 5 Games Avg</span>
              <span className="stat-value">
                {context.last_5_avg != null ? Number(context.last_5_avg).toFixed(1) : 'N/A'} pts
              </span>
            </li>
            {Array.isArray(context.recent_values) && context.recent_values.length > 0 && (
              <li>
                <span className="stat-label">Recent Games</span>
                <span className="stat-value">
                  {context.recent_values.map((v, i) => (
                    <span key={i} className="recent-pip">{v}</span>
                  ))}
                </span>
              </li>
            )}
          </ul>
        </>
      )}
    </div>
  )
}
