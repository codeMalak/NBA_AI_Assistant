import { useEffect, useMemo, useState, useRef } from 'react'
import { getGamesByDate, getPlayers } from '../services/api'

function formatDate(date) {
  return date.toISOString().slice(0, 10)
}

function buildNext7Days() {
  const days = []
  const today = new Date()

  for (let i = 0; i < 7; i++) {
    const d = new Date(today)
    d.setDate(today.getDate() + i)

    days.push({
      value: formatDate(d),
      label:
        i === 0
          ? `Today (${formatDate(d)})`
          : i === 1
            ? `Tomorrow (${formatDate(d)})`
            : d.toLocaleDateString(undefined, {
                weekday: 'short',
                month: 'short',
                day: 'numeric',
              }),
    })
  }

  return days
}


export default function PredictionForm({ onSubmit, loading }) {

  const [games, setGames] = useState([])
  const [gamesLoading, setGamesLoading] = useState(false)
  const lastFetchedDateRef = useRef(null)
  const [gamesError, setGamesError] = useState('')
  const [selectedGameId, setSelectedGameId] = useState('')

  const [homePlayers, setHomePlayers] = useState([])
  const [awayPlayers, setAwayPlayers] = useState([])
  const [playersLoading, setPlayersLoading] = useState(false)
  const [playersError, setPlayersError] = useState('')
  const [playerName, setPlayerName] = useState('')
  const [threshold, setThreshold] = useState('20')
  const [thresholdError, setThresholdError] = useState('')

  const dateOptions = useMemo(() => buildNext7Days(), [])
  const [selectedDate, setSelectedDate] = useState(dateOptions[0]?.value || '')
  const [playerSearch, setPlayerSearch] = useState('')

  const [modelType, setModelType] = useState('baseline')

  const selectedGame = useMemo(() => {
    return games.find((game) => String(game.id) === String(selectedGameId)) || null
  }, [games, selectedGameId])

  const allPlayers = useMemo(() => [...homePlayers, ...awayPlayers], [homePlayers, awayPlayers])

  useEffect(() => {
    async function loadGames() {
      if (!selectedDate) return

      try {
        setGamesLoading(true)
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
      } finally {
        setGamesLoading(false)
      }
    }

    loadGames()
  }, [selectedDate])

  useEffect(() => {
      async function loadPlayersForGame() {
        if (!selectedGame) {
          setHomePlayers([])
          setAwayPlayers([])
          setPlayerName('')
          return
        }

        try {
          setPlayersLoading(true)
          setPlayersError('')

          const homeAbbr = selectedGame.home_team?.abbreviation
          const awayAbbr = selectedGame.visitor_team?.abbreviation

          const [homeRes, awayRes] = await Promise.all([
            getPlayers(homeAbbr, selectedGame.id),
            getPlayers(awayAbbr, selectedGame.id),
          ])

          const home = homeRes.players || []
          const away = awayRes.players || []

          setHomePlayers(home)
          setAwayPlayers(away)

          const merged = [...home, ...away]
          if (merged.length > 0) {
            setPlayerName(merged[0].player_name)
          } else {
            setPlayerName('')
          }
        } catch (err) {
          console.error(err)
          setHomePlayers([])
          setAwayPlayers([])
          setPlayerName('')
          setPlayersError(err.response?.data?.error || err.message || 'Failed to load players')
        } finally {
          setPlayersLoading(false)
        }
      }

      loadPlayersForGame()
    }, [selectedGame])



  function handleSubmit(event) {
    event.preventDefault()
    if (!selectedGame || !playerName) return

    const parsedThreshold = parseFloat(threshold)
    if (!threshold || isNaN(parsedThreshold) || parsedThreshold <= 0) {
      setThresholdError('Threshold must be a positive number.')
      return
    }
    setThresholdError('')

    const homeAbbr = selectedGame.home_team?.abbreviation
    const awayAbbr = selectedGame.visitor_team?.abbreviation

    const isHomePlayer = homePlayers.some((p) => p.player_name === playerName)
    const team_abbr = isHomePlayer ? homeAbbr : awayAbbr
    const opponent_abbr = isHomePlayer ? awayAbbr : homeAbbr

    onSubmit({
      player_name: playerName,
      stat: 'points',
      threshold: parsedThreshold,
      model_type: modelType,
      team_abbr,
      opponent_abbr,
      game_id: selectedGame.id,
      game_date: selectedGame.date,
    })
  }

    const filteredHomePlayers = homePlayers.filter((player) =>
      player.player_name.toLowerCase().includes(playerSearch.toLowerCase())
    )

    const filteredAwayPlayers = awayPlayers.filter((player) =>
      player.player_name.toLowerCase().includes(playerSearch.toLowerCase())
    )

  return (
    <form className="card form" onSubmit={handleSubmit}>
      <label>
        Date
        <select value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)}>
          {dateOptions.map((date) => (
            <option key={date.value} value={date.value}>
              {date.label}
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
          disabled={gamesLoading || games.length === 0}
        >
          {gamesLoading ? (
            <option value="">Loading games…</option>
          ) : games.length === 0 ? (
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
      Search Player
      <input
        type="text"
        placeholder="Search player..."
        value={playerSearch}
        onChange={(e) => setPlayerSearch(e.target.value)}
      />
    </label>

    <label>
      Player
      <select
        value={playerName}
        onChange={(e) => setPlayerName(e.target.value)}
        disabled={playersLoading || (homePlayers.length === 0 && awayPlayers.length === 0)}
      >
        {playersLoading ? (
          <option value="">Loading players...</option>
        ) : homePlayers.length === 0 && awayPlayers.length === 0 ? (
          <option value="">No players available</option>
        ) : (
          <>
            <optgroup label={selectedGame?.home_team?.full_name || 'Home Team'}>
              {filteredHomePlayers.map((player, index) => (
                <option key={`home-${player.player_name}-${index}`} value={player.player_name}>
                  {player.player_name}
                </option>
              ))}
            </optgroup>

            <optgroup label={selectedGame?.visitor_team?.full_name || 'Away Team'}>
              {filteredAwayPlayers.map((player, index) => (
                <option key={`away-${player.player_name}-${index}`} value={player.player_name}>
                  {player.player_name}
                </option>
              ))}
            </optgroup>
          </>
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
          min="0.5"
          value={threshold}
          onChange={(e) => {
            setThreshold(e.target.value)
            setThresholdError('')
          }}
          className={thresholdError ? 'input-error' : ''}
        />
        {thresholdError && <span className="field-error">{thresholdError}</span>}
      </label>

      <button type="submit" disabled={loading || !selectedGame || !playerName || playersLoading}>
        {loading ? 'Analyzing…' : 'Predict'}
      </button>
    </form>
  )
}
