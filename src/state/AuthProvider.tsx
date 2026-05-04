import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { fetchProfile, loginUser, logoutUser, registerUser } from '../api/client'
import { getAccessToken, setAccessToken } from '../lib/storage'
import type { LoginPayload, RegisterPayload, UserProfile } from '../types/api'

type AuthContextValue = {
  user: UserProfile | null
  isLoading: boolean
  isAuthenticated: boolean
  signIn: (payload: LoginPayload) => Promise<void>
  signUp: (payload: RegisterPayload) => Promise<void>
  signOut: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

type AuthProviderProps = {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const token = getAccessToken()
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }

    try {
      const profile = await fetchProfile()
      setUser(profile)
    } catch {
      setAccessToken(null)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshUser()
  }, [refreshUser])

  const signIn = useCallback(async (payload: LoginPayload) => {
    await loginUser(payload)
    const profile = await fetchProfile()
    setUser(profile)
  }, [])

  const signUp = useCallback(async (payload: RegisterPayload) => {
    await registerUser(payload)
  }, [])

  const signOut = useCallback(async () => {
    try {
      await logoutUser()
    } finally {
      setAccessToken(null)
      setUser(null)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      signIn,
      signUp,
      signOut,
      refreshUser,
    }),
    [user, isLoading, signIn, signUp, signOut, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
