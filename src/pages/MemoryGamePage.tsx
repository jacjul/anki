import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { fetchCards } from '../api/client'

type Tile = {
  id: string
  cardId: number
  label: string
}

export function MemoryGamePage() {
  const { deckId } = useParams()
  const numericDeckId = Number(deckId)
  const [flipped, setFlipped] = useState<string[]>([])
  const [matched, setMatched] = useState<number[]>([])
  const [moves, setMoves] = useState(0)

  const cardsQuery = useQuery({
    queryKey: ['cards', numericDeckId],
    queryFn: () => fetchCards(numericDeckId),
    enabled: Number.isFinite(numericDeckId) && numericDeckId > 0,
  })

  const tiles = useMemo<Tile[]>(() => {
    const subset = (cardsQuery.data ?? []).slice(0, 8)
    const pairs = subset.flatMap((card) => [
      { id: `f-${card.id}`, cardId: card.id, label: card.frontside },
      { id: `b-${card.id}`, cardId: card.id, label: card.backside },
    ])

    const clone = [...pairs]
    for (let i = clone.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[clone[i], clone[j]] = [clone[j], clone[i]]
    }
    return clone
  }, [cardsQuery.data])

  const completed = matched.length > 0 && matched.length * 2 === tiles.length

  const onFlip = (tile: Tile) => {
    if (flipped.includes(tile.id) || matched.includes(tile.cardId) || flipped.length === 2) {
      return
    }

    const next = [...flipped, tile.id]
    setFlipped(next)

    if (next.length === 2) {
      setMoves((value) => value + 1)
      const first = tiles.find((item) => item.id === next[0])
      const second = tiles.find((item) => item.id === next[1])

      if (first && second && first.cardId === second.cardId) {
        setMatched((value) => [...value, first.cardId])
        setTimeout(() => setFlipped([]), 200)
      } else {
        setTimeout(() => setFlipped([]), 700)
      }
    }
  }

  return (
    <section className="game-layout">
      <div className="row-between">
        <h2>Memory Match</h2>
        <Link className="button ghost" to={`/deck/${numericDeckId}`}>
          Back to deck
        </Link>
      </div>

      <p className="muted">Find front-back pairs of the same card. Moves: {moves}</p>

      {cardsQuery.isLoading ? <p className="muted">Loading cards...</p> : null}
      {tiles.length < 4 ? <p className="status">Add at least 2 cards to play this mode.</p> : null}

      <div className="memory-grid">
        {tiles.map((tile) => {
          const visible = flipped.includes(tile.id) || matched.includes(tile.cardId)
          return (
            <button
              className={`memory-tile ${visible ? 'open' : ''}`}
              key={tile.id}
              onClick={() => onFlip(tile)}
            >
              {visible ? tile.label : '?'}
            </button>
          )
        })}
      </div>

      {completed ? <p className="status">Perfect run. You solved it in {moves} moves.</p> : null}
    </section>
  )
}
