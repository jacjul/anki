import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AppShell } from './components/AppShell'
import { AuthPage } from './pages/AuthPage'
import { DashboardPage } from './pages/DashboardPage'
import { DeckPage } from './pages/DeckPage'
import { MemoryGamePage } from './pages/MemoryGamePage'
import { QuizGamePage } from './pages/QuizGamePage'
import './App.css'

function App() {
  return (
    <Routes>
      <Route path="/auth" element={<AuthPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/deck/:deckId" element={<DeckPage />} />
          <Route path="/deck/:deckId/game/memory" element={<MemoryGamePage />} />
          <Route path="/deck/:deckId/game/quiz" element={<QuizGamePage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
