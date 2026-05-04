import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { getAccessToken, setAccessToken, getCookieValue } from './storage'
import type { AuthTokenResponse } from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'

type RetriableRequest = InternalAxiosRequestConfig & {
  _retry?: boolean
}

export const http = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
})

let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken() {
  const csrf = getCookieValue('csrf_token')
  const response = await http.post<AuthTokenResponse>(
    '/auth/refresh',
    {},
    {
      headers: {
        origin: window.location.origin,
        'x-csrf-token': csrf,
      },
    },
  )

  const nextToken = response.data.access_token
  setAccessToken(nextToken)
  return nextToken
}

http.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetriableRequest | undefined
    const status = error.response?.status

    if (!config || status !== 401 || config._retry) {
      return Promise.reject(error)
    }

    const path = config.url ?? ''
    const isAuthEndpoint = path.includes('/auth/login') || path.includes('/auth/register')
    if (isAuthEndpoint) {
      return Promise.reject(error)
    }

    config._retry = true

    try {
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null
        })
      }

      const token = await refreshPromise

      if (!token) {
        return Promise.reject(error)
      }

      config.headers.Authorization = `Bearer ${token}`
      return http.request(config)
    } catch (refreshError) {
      setAccessToken(null)
      return Promise.reject(refreshError)
    }
  },
)
