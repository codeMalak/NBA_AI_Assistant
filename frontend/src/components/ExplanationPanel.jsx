export default function ExplanationPanel({ explanation, explanationType, context }) {
  return (
    <div className="card explanation-card">
      <div className="section-title-row">
        <div>
          <h2>Grounded Explanation</h2>
          <p>Context-aware explanation based on model output and retrieved stats.</p>
        </div>

        <span className="pill">{explanationType ?? 'N/A'}</span>
      </div>

      <div className="explanation-box">
        <p>{explanation ?? 'No explanation returned.'}</p>
      </div>

      {context && (
        <div className="context-box">
          <h3>Supporting Context</h3>

          <div className="result-grid">
            <div className="result-item">
              <span className="result-label">Season Average</span>
              <span className="result-value">{context.season_avg ?? 'N/A'} pts</span>
            </div>

            <div className="result-item">
              <span className="result-label">Last 5 Games Avg</span>
              <span className="result-value">{context.last_5_avg ?? 'N/A'} pts</span>
            </div>
          </div>

          <div className="recent-games">
            <span className="result-label">Recent Games</span>

            <div className="recent-values">
              {Array.isArray(context.recent_values) && context.recent_values.length > 0 ? (
                context.recent_values.map((value, index) => (
                  <span key={index} className="recent-chip">
                    {value}
                  </span>
                ))
              ) : (
                <span className="result-value">N/A</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}