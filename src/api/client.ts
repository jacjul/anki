import { http } from '../lib/http'
import { getCookieValue, setAccessToken } from '../lib/storage'
import type {
  ApiMessage,
  AuthTokenResponse,
  Card,
  CardCreatePayload,
  Deck,
  DeckCreatePayload,
  DeckUpdatePayload,
  LoginPayload,
  RegisterPayload,
  UserProfile,
} from '../types/api'

export async function registerUser(payload: RegisterPayload) {
  const { data } = await http.post<ApiMessage>('/auth/register', payload)
  return data
}

export async function loginUser(payload: LoginPayload) {
  const body = new URLSearchParams()
  body.set('username', payload.username)
  body.set('password', payload.password)

  const { data } = await http.post<AuthTokenResponse>('/auth/login', body, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })

  setAccessToken(data.access_token)
  return data
}

export async function fetchProfile() {
  const { data } = await http.get<UserProfile>('/auth/me')
  return data
}

export async function logoutUser() {
  const csrf = getCookieValue('csrf_token')
  const { data } = await http.post<ApiMessage>(
    '/auth/logout',
    {},
    {
      headers: {
        origin: window.location.origin,
        'x-csrf-token': csrf,
      },
    },
  )
  return data
}

export async function createDeck(payload: DeckCreatePayload) {
  const { data } = await http.post<Deck>('/deck/create', payload)
  return data
}

export async function updateDeck(action: 'rename' | 'public', payload: DeckUpdatePayload) {
  const { data } = await http.patch<ApiMessage>(`/deck/update/${action}`, payload)
  return data
}

export async function deleteDeck(deckId: number) {
  const { data } = await http.delete<ApiMessage>(`/deck/delete/${deckId}`)
  return data
}

export async function fetchCards(deckId: number) {
  const { data } = await http.get<Card[]>(`/card/all/${deckId}`)
  return data
}

export async function createCard(payload: CardCreatePayload) {
  const { data } = await http.post<ApiMessage>('/card/create', payload)
  return data
}
