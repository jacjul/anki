export type ApiMessage = {
  message: string
}

export type UserProfile = {
  id: number
  name: string
  lastname: string
  username: string
  email: string
}

export type RegisterPayload = {
  name: string
  lastname: string
  username: string
  email: string
  password: string
}

export type LoginPayload = {
  username: string
  password: string
}

export type AuthTokenResponse = {
  access_token: string
  token_type: string
}

export type Deck = {
  id: number
  name: string
  public: boolean
  owner_id: number
}

export type DeckCreatePayload = {
  name: string
  public: boolean
}

export type DeckUpdatePayload = {
  id: number
  name: string
  public: boolean
}

export type Card = {
  id: number
  frontside: string
  frontside_explain: string | null
  backside: string
  backside_explain: string | null
  audio_front: string | null
  audio_back: string | null
  deck_id: number
}

export type CardCreatePayload = {
  frontside: string
  frontside_explain?: string | null
  backside: string
  backside_explain?: string | null
  audio_front?: string | null
  audio_back?: string | null
  deck_id: number
}
