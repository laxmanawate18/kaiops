import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login({ username, password })
      navigate('/')
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Login failed'
      setError(Array.isArray(detail) ? detail.join(' ') : detail)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-6">
      <div className="glass-panel relative w-full max-w-md overflow-hidden rounded-3xl border border-white/10 p-8 shadow-2xl">
        <div className="pointer-events-none absolute inset-0 opacity-30" style={{ background: 'radial-gradient(circle at top right, rgba(0,240,255,0.4), transparent 50%)' }} />
        
        <div className="relative z-10">
          <div className="mb-2">
            <p className="text-xs font-semibold tracking-[0.4em] text-kaiops-primary">AUTHENTICATION</p>
            <h2 className="mt-3 text-3xl font-black tracking-tight text-white">Sign In</h2>
            <p className="mt-1 text-xs font-semibold text-kaiops-primary/80 tracking-wider">Incidents End Here</p>
            <p className="mt-2 text-sm text-slate-300">Enter your credentials to access KaiOPS.</p>
          </div>

          {error && (
            <div className="glass-card mt-6 rounded-2xl border border-rose-400/30 bg-rose-500/10 p-4 text-sm text-rose-200">
              <div className="flex gap-3">
                <svg className="h-5 w-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{error}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-5">
            <div>
              <label className="block text-xs font-semibold tracking-[0.3em] text-kaiops-primary/80">USERNAME</label>
              <input
                type="text"
                placeholder="operator_alpha"
                className="glass-card mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-slate-400 transition focus:border-kaiops-primary/40 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold tracking-[0.3em] text-kaiops-primary/80">PASSWORD</label>
              <input
                type="password"
                placeholder="••••••••••••"
                className="glass-card mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-slate-400 transition focus:border-kaiops-primary/40 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="relative mt-8 w-full overflow-hidden rounded-2xl border border-kaiops-primary/40 bg-gradient-to-r from-kaiops-primary/20 to-kaiops-secondary/10 px-5 py-3 text-sm font-semibold text-white transition hover:border-kaiops-primary/60 hover:from-kaiops-primary/30 hover:to-kaiops-secondary/20 disabled:cursor-not-allowed disabled:from-slate-600/20 disabled:to-slate-700/20"
            >
              {loading ? 'Verifying…' : 'Engage Mission Control'}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-slate-400">
            New operator?{' '}
            <Link to="/register" className="font-semibold text-kaiops-primary/80 transition hover:text-kaiops-primary">
              Register here
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login
