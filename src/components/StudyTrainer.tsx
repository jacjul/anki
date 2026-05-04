import { useMemo, useState } from 'react'
import type { Card } from '../types/api'

type StudyTrainerProps = {
  cards: Card[]
}

type Rating = 'again' | 'hard' | 'good' | 'easy'

export function StudyTrainer({ cards }: StudyTrainerProps) {
  const [index, setIndex] = useState(0)
  const [revealed, setRevealed] = useState(false)
  const [ratings, setRatings] = useState<Record<Rating, number>>({
    again: 0,
    hard: 0,
    good: 0,
    easy: 0,
  })
  const [seed, setSeed] = useState(0)

  const deck = useMemo(() => {
    const clone = [...cards]
    for (let i = clone.length - 1; i > 0; i -= 1) {
      const j = Math.floor((Math.sin(seed + i) * 10000) % (i + 1))
      const normalized = Math.abs(j)
      const next = normalized % (i + 1)
      ;[clone[i], clone[next]] = [clone[next], clone[i]]
    }
    return clone
  }, [cards, seed])

  const current = deck[index]

  if (!current) {
    return <p className="muted">Create cards to unlock study mode.</p>
  }

  const nextCard = () => {
    setRevealed(false)
    setIndex((value) => (value + 1) % deck.length)
  }

  const mark = (rating: Rating) => {
    setRatings((prev) => ({ ...prev, [rating]: prev[rating] + 1 }))
    nextCard()
  }

  return (
    <section className="study-panel glass">
      <div className="row-between">
        <h3>Study Session</h3>
        <p className="muted">
          Card {index + 1} / {deck.length}
        </p>
      </div>

      <button className="study-card" onClick={() => setRevealed((value) => !value)}>
        <p className="label">Front</p>
        <h4>{current.frontside}</h4>
        {revealed ? (
          <>
            <p className="label">Back</p>
            <h4>{current.backside}</h4>
          </>
        ) : (
          <p className="muted">Tap to reveal answer</p>
        )}
      </button>

      <div className="rating-grid">
        <button className="button danger" onClick={() => mark('again')}>
          Again ({ratings.again})
        </button>
        <button className="button" onClick={() => mark('hard')}>
          Hard ({ratings.hard})
        </button>
        <button className="button" onClick={() => mark('good')}>
          Good ({ratings.good})
        </button>
        <button className="button success" onClick={() => mark('easy')}>
          Easy ({ratings.easy})
        </button>
      </div>

      <button className="button ghost" onClick={() => setSeed((value) => value + 1)}>
        Shuffle deck
      </button>
    </section>
  )
}
