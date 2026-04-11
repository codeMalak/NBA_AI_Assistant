import { useState } from 'react'

const PLAYERS = ['Stephen Curry', 'LeBron James', 'Jayson Tatum', 'Nikola Jokic']

export default function PredictionForm({ onSubmit, loading }) {
  const [playerName, setPlayerName] = useState(PLAYERS[0])
  const [threshold, setThreshold] = useState('28.5')

  function handleSubmit(event) {
    event.preventDefault()
    onSubmit({
      player_name: playerName,
      stat: 'points',
      threshold: Number(threshold),
    })
  }

  return (
    <form className="card form" onSubmit={handleSubmit}>
      <label>
        Player
        <select value={playerName} onChange={(e) => setPlayerName(e.target.value)}>
          {PLAYERS.map((player) => (
            <option key={player} value={player}>{player}</option>
          ))}
        </select>
      </label>

      <label>
        Stat
        <input value="points" disabled />
      </label>

      <label>
        Threshold
        <input
          type="number"
          step="0.5"
          value={threshold}
          onChange={(e) => setThreshold(e.target.value)}
        />
      </label>

      <button type="submit" disabled={loading}>
        {loading ? 'Analyzing...' : 'Predict'}
      </button>
    </form>
  )
}
