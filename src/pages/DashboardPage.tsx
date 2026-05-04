import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { createDeck, deleteDeck, updateDeck } from '../api/client'
import { removeDeckForUser, saveDeckForUser, getDecksForUser, setDecksForUser } from '../lib/storage'
import { useAuth } from '../state/AuthProvider'
import type { Deck } from '../types/api'

export function DashboardPage() {
  const { user } = useAuth()
  const [name, setName] = useState('')
  const [isPublic, setIsPublic] = useState(true)
  const [status, setStatus] = useState('')
  const [decks, setDecks] = useState<Deck[]>(() => (user ? getDecksForUser(user.id) : []))

  useEffect(() => {
    if (user) {
      setDecks(getDecksForUser(user.id))
    }
  }, [user])

  const createMutation = useMutation({
    mutationFn: createDeck,
    onSuccess: (deck) => {
      if (!user) return
      const next = saveDeckForUser(user.id, deck)
      setDecks(next)
      setName('')
      setStatus('Deck created.')
    },
    onError: (error) => {
      setStatus(`Could not create deck: ${extractError(error)}`)
    },
  })

  const renameMutation = useMutation({
    mutationFn: ({ deck, nextName }: { deck: Deck; nextName: string }) =>
      updateDeck('rename', { id: deck.id, name: nextName, public: deck.public }),
    onSuccess: (_, variables) => {
      if (!user) return
      const nextDecks = decks.map((item) =>
        item.id === variables.deck.id ? { ...item, name: variables.nextName } : item,
      )
      setDecks(nextDecks)
      setDecksForUser(user.id, nextDecks)
      setStatus('Deck renamed.')
    },
    onError: (error) => setStatus(`Rename failed: ${extractError(error)}`),
  })

  const visibilityMutation = useMutation({
    mutationFn: (deck: Deck) =>
      updateDeck('public', { id: deck.id, name: deck.name, public: !deck.public }),
    onSuccess: (_, deck) => {
      if (!user) return
      const nextDecks = decks.map((item) =>
        item.id === deck.id ? { ...item, public: !item.public } : item,
      )
      setDecks(nextDecks)
      setDecksForUser(user.id, nextDecks)
      setStatus('Deck visibility updated.')
    },
    onError: (error) => setStatus(`Visibility update failed: ${extractError(error)}`),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteDeck,
    onSuccess: (_, deckId) => {
      if (!user) return
      const next = removeDeckForUser(user.id, deckId)
      setDecks(next)
      setStatus('Deck deleted.')
    },
    onError: (error) => setStatus(`Delete failed: ${extractError(error)}`),
  })

  return (
    <section className="deck-grid">
      <article className="glass panel">
        <h2>Create deck</h2>
        <form
          className="form-grid"
          onSubmit={(event) => {
            event.preventDefault()
            createMutation.mutate({ name, public: isPublic })
          }}
        >
          <label>
            Deck name
            <input value={name} maxLength={40} onChange={(event) => setName(event.target.value)} required />
          </label>
          <label className="checkbox">
            <input type="checkbox" checked={isPublic} onChange={(event) => setIsPublic(event.target.checked)} />
            Public deck
          </label>
          <button className="button" type="submit" disabled={createMutation.isPending}>
            Create
          </button>
        </form>
        {status ? <p className="status">{status}</p> : null}
      </article>

      <article className="glass panel">
        <div className="row-between">
          <h2>Your decks</h2>
          <p className="muted">{decks.length} saved</p>
        </div>

        <div className="deck-list">
          {decks.map((deck) => (
            <div key={deck.id} className="deck-item">
              <div>
                <h3>{deck.name}</h3>
                <p className="muted">ID #{deck.id}</p>
              </div>
              <span className={`pill ${deck.public ? 'public' : 'private'}`}>
                {deck.public ? 'Public' : 'Private'}
              </span>
              <div className="deck-actions">
                <Link className="button" to={`/deck/${deck.id}`}>
                  Open
                </Link>
                <button
                  className="button ghost"
                  onClick={() => {
                    const nextName = prompt('New deck name', deck.name)
                    if (!nextName || nextName.trim() === deck.name) return
                    renameMutation.mutate({ deck, nextName: nextName.trim() })
                  }}
                >
                  Rename
                </button>
                <button className="button ghost" onClick={() => visibilityMutation.mutate(deck)}>
                  Toggle visibility
                </button>
                <button className="button danger" onClick={() => deleteMutation.mutate(deck.id)}>
                  Delete
                </button>
              </div>
            </div>
          ))}

          {!decks.length ? <p className="muted">Create your first deck to start studying.</p> : null}
        </div>
      </article>
    </section>
  )
}

function extractError(error: unknown) {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const maybeResponse = error as { response?: { data?: { detail?: string } } }
    return maybeResponse.response?.data?.detail ?? 'Unknown error'
  }
  return 'Unknown error'
}
