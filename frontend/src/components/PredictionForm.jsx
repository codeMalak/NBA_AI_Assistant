import { useEffect, useMemo, useState, useRef } from 'react'
import { getGamesByDate, getPlayers } from '../services/api'

function formatDate(date) {
  return date.toISOString().slice(0, 10)
}

export default function PredictionForm({ onSubmit, loading }) {
  const today = formatDate(new Date())
  const tomorrowDate = new Date()
  tomorrowDate.setDate(tomorrowDate.getDate() + 1)
  const tomorrow = formatDate(tomorrowDate)

  const [selectedDate, setSelectedDate] = useState(today)
  const [games, setGames] = useState([])
  const lastFetchedDateRef = useRef(null)
  const [gamesError, setGamesError] = useState('')
  const [selectedGameId, setSelectedGameId] = useState('')

  const [players, setPlayers] = useState([])
  const [playersError, setPlayersError] = useState('')
  const [playerName, setPlayerName] = useState('')
  const [threshold, setThreshold] = useState('20')

  // ✅ NEW: model selector state
  const [modelType, setModelType] = useState('baseline')

  const selectedGame = useMemo(() => {
    return games.find((game) => String(game.id) === String(selectedGameId)) || null
  }, [games, selectedGameId])

  useEffect(() => {
    async function loadGames() {
      if (lastFetchedDateRef.current === selectedDate) return
      lastFetchedDateRef.current = selectedDate

      try {
        setGamesError('')
        const data = await getGamesByDate(selectedDate)

        const gamesList = data.games || []
        setGames(gamesList)

        if (gamesList.length > 0) {
          setSelectedGameId(String(gamesList[0].id))
        } else {
          setSelectedGameId('')
        }
      } catch (err) {
        console.error(err)
        setGames([])
        setSelectedGameId('')
        setGamesError(err.response?.data?.error || err.message || 'Failed to load games')
      }
    }

    loadGames()
  }, [selectedDate])

  useEffect(() => {
    async function loadPlayersForGame() {
      if (!selectedGame) {
        setPlayers([])
        setPlayerName('')
        return
      }

      try {
        setPlayersError('')
        const homeAbbr = selectedGame.home_team?.abbreviation
        const awayAbbr = selectedGame.visitor_team?.abbreviation

        const [homePlayersRes, awayPlayersRes] = await Promise.all([
          getPlayers(homeAbbr),
          getPlayers(awayAbbr),
        ])

        const merged = [
          ...(homePlayersRes.players || []),
          ...(awayPlayersRes.players || []),
        ]

        setPlayers(merged)

        if (merged.length > 0) {
          setPlayerName(merged[0].player_name)
        } else {
          setPlayerName('')
        }
      } catch (err) {
        console.error(err)
        setPlayers([])
        setPlayerName('')
        setPlayersError(err.response?.data?.error || err.message || 'Failed to load players')
      }
    }

    loadPlayersForGame()
  }, [selectedGame])

  function handleSubmit(event) {
    event.preventDefault()
    if (!selectedGame || !playerName) return

    const homeAbbr = selectedGame.home_team?.abbreviation
    const awayAbbr = selectedGame.visitor_team?.abbreviation

    // determine which team player is on
    const isHomePlayer = players.find(p => p.player_name === playerName && homeAbbr)
    const team_abbr = isHomePlayer ? homeAbbr : awayAbbr
    const opponent_abbr = isHomePlayer ? awayAbbr : homeAbbr

    onSubmit({
      player_name: playerName,
      stat: "points",
      threshold: parseFloat(threshold),
      model_type: modelType,
      team_abbr,
      opponent_abbr,
      game_id: selectedGame.id,
      game_date: selectedGame.date,
    })
  }

  return (
    <form className="card form" onSubmit={handleSubmit}>
      <label>
        Date
        <select value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)}>
          <option value={today}>Today ({today})</option>
          <option value={tomorrow}>Tomorrow ({tomorrow})</option>
        </select>
      </label>

      {/* ✅ FIXED MODEL DROPDOWN */}
      <label>
        Model
        <select value={modelType} onChange={(e) => setModelType(e.target.value)}>
          <option value="baseline">Baseline</option>
          <option value="enriched">Enriched</option>
        </select>
      </label>

      <label>
        Game
        <select
          value={selectedGameId}
          onChange={(e) => setSelectedGameId(e.target.value)}
          disabled={games.length === 0}
        >
          {games.length === 0 ? (
            <option value="">No games available</option>
          ) : (
            games.map((game) => (
              <option key={game.id} value={game.id}>
                {game.visitor_team?.full_name} @ {game.home_team?.full_name}
              </option>
            ))
          )}
        </select>
      </label>

      {gamesError && <div className="error">{gamesError}</div>}

      <label>
        Player
        <select
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
          disabled={players.length === 0}
        >
          {players.length === 0 ? (
            <option value="">No players available</option>
          ) : (
            players.map((player, index) => (
              <option key={`${player.player_name}-${index}`} value={player.player_name}>
                {player.player_name}
              </option>
            ))
          )}
        </select>
      </label>

      {playersError && <div className="error">{playersError}</div>}

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

      <button type="submit" disabled={loading || !selectedGame || !playerName}>
        {loading ? 'Analyzing...' : 'Predict'}
      </button>
    </form>
  )
}