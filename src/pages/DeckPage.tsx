import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { createCard, fetchCards } from '../api/client'
import { getDecksForUser } from '../lib/storage'
import { useAuth } from '../state/AuthProvider'
import { StudyTrainer } from '../components/StudyTrainer'

export function DeckPage() {
  const params = useParams()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const deckId = Number(params.deckId)
  const [status, setStatus] = useState('')

  const [frontside, setFrontside] = useState('')
  const [backside, setBackside] = useState('')
  const [frontsideExplain, setFrontsideExplain] = useState('')
  const [backsideExplain, setBacksideExplain] = useState('')

  const deck = useMemo(() => {
    if (!user || Number.isNaN(deckId)) return null
    return getDecksForUser(user.id).find((item) => item.id === deckId) ?? null
  }, [user, deckId])

  const cardsQuery = useQuery({
    queryKey: ['cards', deckId],
    queryFn: () => fetchCards(deckId),
    enabled: Number.isFinite(deckId) && deckId > 0,
  })

  const cardMutation = useMutation({
    mutationFn: createCard,
    onSuccess: () => {
      setStatus('Card created.')
      setFrontside('')
      setBackside('')
      setFrontsideExplain('')
      setBacksideExplain('')
      void queryClient.invalidateQueries({ queryKey: ['cards', deckId] })
    },
    onError: (error) => {
      setStatus(`Card creation failed: ${extractError(error)}`)
    },
  })

  if (!Number.isFinite(deckId) || deckId <= 0) {
    return <p className="status">Invalid deck id.</p>
  }

  return (
    <section className="deck-space">
      <article className="glass panel">
        <div className="row-between">
          <div>
            <h2>{deck?.name ?? `Deck #${deckId}`}</h2>
            <p className="muted">Create cards and launch practice modes.</p>
          </div>
          <div className="button-row">
            <Link className="button" to={`/deck/${deckId}/game/memory`}>
              Memory game
            </Link>
            <Link className="button" to={`/deck/${deckId}/game/quiz`}>
              Quiz game
            </Link>
          </div>
        </div>
      </article>

      <article className="glass panel">
        <h3>Add card</h3>
        <form
          className="form-grid"
          onSubmit={(event) => {
            event.preventDefault()
            cardMutation.mutate({
              deck_id: deckId,
              frontside,
              backside,
              frontside_explain: frontsideExplain || null,
              backside_explain: backsideExplain || null,
            })
          }}
        >
          <label>
            Front
            <input value={frontside} maxLength={70} onChange={(event) => setFrontside(event.target.value)} required />
          </label>
          <label>
            Back
            <input value={backside} maxLength={70} onChange={(event) => setBackside(event.target.value)} required />
          </label>
          <label>
            Front explanation
            <textarea
              value={frontsideExplain}
              maxLength={2000}
              onChange={(event) => setFrontsideExplain(event.target.value)}
            />
          </label>
          <label>
            Back explanation
            <textarea
              value={backsideExplain}
              maxLength={2000}
              onChange={(event) => setBacksideExplain(event.target.value)}
            />
          </label>
          <button className="button" type="submit" disabled={cardMutation.isPending}>
            Add card
          </button>
        </form>
        {status ? <p className="status">{status}</p> : null}
      </article>

      <article className="glass panel">
        <div className="row-between">
          <h3>Cards</h3>
          <p className="muted">{cardsQuery.data?.length ?? 0} total</p>
        </div>
        {cardsQuery.isLoading ? <p className="muted">Loading cards...</p> : null}
        {cardsQuery.isError ? <p className="status">{extractError(cardsQuery.error)}</p> : null}
        <div className="card-list">
          {cardsQuery.data?.map((card) => (
            <div key={card.id} className="card-row">
              <p>
                <strong>{card.frontside}</strong> {'->'} {card.backside}
              </p>
              {card.frontside_explain ? <p className="muted">{card.frontside_explain}</p> : null}
              {card.backside_explain ? <p className="muted">{card.backside_explain}</p> : null}
            </div>
          ))}
        </div>
      </article>

      <StudyTrainer cards={cardsQuery.data ?? []} />
    </section>
  )
}

function extractError(error: unknown) {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const maybeResponse = error as { response?: { data?: { detail?: string } } }
    return maybeResponse.response?.data?.detail ?? 'Unknown error'
  }
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return String((error as { message?: string }).message)
  }
  return 'Unknown error'
}
