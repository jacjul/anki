import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthProvider'

const registerSchema = z.object({
  name: z.string().min(1),
  lastname: z.string().min(1),
  username: z.string().min(3),
  email: z.email(),
  password: z.string().min(8),
})

const loginSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
})

type RegisterForm = z.infer<typeof registerSchema>
type LoginForm = z.infer<typeof loginSchema>

export function AuthPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [status, setStatus] = useState('')
  const { signIn, signUp } = useAuth()
  const navigate = useNavigate()

  const registerForm = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      name: '',
      lastname: '',
      username: '',
      email: '',
      password: '',
    },
  })

  const loginForm = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  })

  const handleRegister = registerForm.handleSubmit(async (values) => {
    try {
      await signUp(values)
      setStatus('Account created. Please log in.')
      setMode('login')
    } catch (error) {
      setStatus(`Registration failed: ${extractError(error)}`)
    }
  })

  const handleLogin = loginForm.handleSubmit(async (values) => {
    try {
      await signIn(values)
      navigate('/')
    } catch (error) {
      setStatus(`Login failed: ${extractError(error)}`)
    }
  })

  return (
    <div className="auth-layout">
      <section className="auth-card glass">
        <h1>CardForge</h1>
        <p>Create decks, add cards, train memory, and play.</p>

        <div className="mode-switch">
          <button
            className={mode === 'login' ? 'active' : ''}
            onClick={() => setMode('login')}
            type="button"
          >
            Login
          </button>
          <button
            className={mode === 'register' ? 'active' : ''}
            onClick={() => setMode('register')}
            type="button"
          >
            Register
          </button>
        </div>

        {mode === 'login' ? (
          <form className="form-grid" onSubmit={handleLogin}>
            <label>
              Username
              <input {...loginForm.register('username')} />
            </label>
            <label>
              Password
              <input type="password" {...loginForm.register('password')} />
            </label>
            <button className="button" type="submit">
              Enter workspace
            </button>
          </form>
        ) : (
          <form className="form-grid" onSubmit={handleRegister}>
            <label>
              Name
              <input {...registerForm.register('name')} />
            </label>
            <label>
              Last name
              <input {...registerForm.register('lastname')} />
            </label>
            <label>
              Username
              <input {...registerForm.register('username')} />
            </label>
            <label>
              Email
              <input {...registerForm.register('email')} />
            </label>
            <label>
              Password
              <input type="password" {...registerForm.register('password')} />
            </label>
            <button className="button" type="submit">
              Create account
            </button>
          </form>
        )}

        {status ? <p className="status">{status}</p> : null}
      </section>
    </div>
  )
}

function extractError(error: unknown) {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const maybeResponse = error as { response?: { data?: { detail?: string } } }
    return maybeResponse.response?.data?.detail ?? 'Unknown error'
  }
  return 'Unknown error'
}
