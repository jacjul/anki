import type { Deck } from '../types/api'

const ACCESS_TOKEN_KEY = 'anki.accessToken'

type DeckRegistry = Record<string, Deck[]>

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function setAccessToken(token: string | null) {
  if (!token) {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    return
  }
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

function loadRegistry(): DeckRegistry {
  const raw = localStorage.getItem('anki.deckRegistry')
  if (!raw) {
    return {}
  }
  try {
    return JSON.parse(raw) as DeckRegistry
  } catch {
    return {}
  }
}

function saveRegistry(registry: DeckRegistry) {
  localStorage.setItem('anki.deckRegistry', JSON.stringify(registry))
}

export function getDecksForUser(userId: number) {
  const registry = loadRegistry()
  return registry[String(userId)] ?? []
}

export function saveDeckForUser(userId: number, deck: Deck) {
  const registry = loadRegistry()
  const key = String(userId)
  const existing = registry[key] ?? []
  const next = existing.some((item) => item.id === deck.id)
    ? existing.map((item) => (item.id === deck.id ? deck : item))
    : [deck, ...existing]

  registry[key] = next
  saveRegistry(registry)
  return next
}

export function removeDeckForUser(userId: number, deckId: number) {
  const registry = loadRegistry()
  const key = String(userId)
  const existing = registry[key] ?? []
  const next = existing.filter((deck) => deck.id !== deckId)
  registry[key] = next
  saveRegistry(registry)
  return next
}

export function setDecksForUser(userId: number, decks: Deck[]) {
  const registry = loadRegistry()
  registry[String(userId)] = decks
  saveRegistry(registry)
}

export function getCookieValue(name: string) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = document.cookie.match(new RegExp(`(?:^|; )${escaped}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : ''
}
