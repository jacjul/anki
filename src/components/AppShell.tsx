import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthProvider'

export function AppShell() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="app-shell">
      <header className="app-header glass">
        <div>
          <Link className="brand" to="/">
            CardForge
          </Link>
          <p className="subtitle">Learn faster with decks, drills, and games.</p>
        </div>
        <div className="header-actions">
          <p className="muted">{user?.username}</p>
          <button
            className="button ghost"
            onClick={async () => {
              await signOut()
              navigate('/auth', { replace: true })
            }}
          >
            Logout
          </button>
        </div>
      </header>

      <nav className="top-nav">
        <NavLink to="/" end>
          Decks
        </NavLink>
      </nav>

      <main>
        <Outlet />
      </main>
    </div>
  )
}
