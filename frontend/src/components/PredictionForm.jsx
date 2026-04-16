import { useEffect, useMemo, useState, useRef } from 'react'
import { getGamesByDate, getPlayers } from '../services/api'

function formatDate(date) {
  return date.toISOString().slice(0, 10)
}

function buildNext7Days() {
  const days = []
  const base = new Date()

  for (let i = 0; i < 7; i++) {
    const d = new Date(base)
    d.setDate(base.getDate() + i)
    days.push(formatDate(d))
  }

  return days
}

export default function PredictionForm({ onSubmit, loading }) {
  const dateOptions = useMemo(() => buildNext7Days(), [])
  const [selectedDate, setSelectedDate] = useState(dateOptions[0])

  const [games, setGames] = useState([])
  const lastFetchedDateRef = useRef(null)
  const [gamesError, setGamesError] = useState('')
  const [selectedGameId, setSelectedGameId] = useState('')

  const [players, setPlayers] = useState([])
  const [playersError, setPlayersError] = useState('')
  const [playerName, setPlayerName] = useState('')
  const [threshold, setThreshold] = useState('20')
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

    const selectedPlayerObj = players.find((p) => p.player_name === playerName)
    const team_abbr = selectedPlayerObj?.team_abbr || homeAbbr
    const opponent_abbr = team_abbr === homeAbbr ? awayAbbr : homeAbbr

    onSubmit({
      player_name: playerName,
      stat: 'points',
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
          {dateOptions.map((date) => (
            <option key={date} value={date}>
              {date}
            </option>
          ))}
        </select>
      </label>

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