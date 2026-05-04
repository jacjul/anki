import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { fetchCards } from '../api/client'

export function QuizGamePage() {
  const { deckId } = useParams()
  const numericDeckId = Number(deckId)
  const [index, setIndex] = useState(0)
  const [score, setScore] = useState(0)
  const [feedback, setFeedback] = useState('')

  const cardsQuery = useQuery({
    queryKey: ['cards', numericDeckId],
    queryFn: () => fetchCards(numericDeckId),
    enabled: Number.isFinite(numericDeckId) && numericDeckId > 0,
  })

  const cards = cardsQuery.data ?? []
  const current = cards[index]

  const options = useMemo(() => {
    if (!current) return []
    const distractors = cards
      .filter((card) => card.id !== current.id)
      .slice(0, 3)
      .map((card) => card.backside)

    const candidate = [current.backside, ...distractors]

    for (let i = candidate.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[candidate[i], candidate[j]] = [candidate[j], candidate[i]]
    }

    return candidate
  }, [cards, current])

  const answer = (value: string) => {
    if (!current) return

    if (value === current.backside) {
      setScore((old) => old + 1)
      setFeedback('Correct')
    } else {
      setFeedback(`Wrong. Correct answer: ${current.backside}`)
    }

    setTimeout(() => {
      setFeedback('')
      setIndex((old) => {
        if (!cards.length) return 0
        return (old + 1) % cards.length
      })
    }, 700)
  }

  return (
    <section className="game-layout">
      <div className="row-between">
        <h2>Quick Quiz</h2>
        <Link className="button ghost" to={`/deck/${numericDeckId}`}>
          Back to deck
        </Link>
      </div>
      <p className="muted">Score: {score}</p>

      {cardsQuery.isLoading ? <p className="muted">Loading cards...</p> : null}
      {cards.length < 4 ? <p className="status">Add at least 4 cards for better quiz variety.</p> : null}

      {current ? (
        <div className="quiz-panel glass">
          <p className="label">Question</p>
          <h3>{current.frontside}</h3>
          <div className="quiz-options">
            {options.map((option) => (
              <button key={option} className="button" onClick={() => answer(option)}>
                {option}
              </button>
            ))}
          </div>
          {feedback ? <p className="status">{feedback}</p> : null}
        </div>
      ) : null}
    </section>
  )
}
