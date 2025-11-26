import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: ''
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    // Frontend validation
    if (!form.username.trim()) {
      setError('Username is required')
      return
    }

    if (form.username.length < 3) {
      setError('Username must be at least 3 characters long')
      return
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(form.username)) {
      setError('Username can only contain letters, numbers, hyphens, and underscores')
      return
    }

    if (!form.email.trim()) {
      setError('Email is required')
      return
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      setError('Please enter a valid email address')
      return
    }

    if (!form.password) {
      setError('Password is required')
      return
    }

    if (form.password.length < 6) {
      setError('Password must be at least 6 characters long')
      return
    }

    if (!/[A-Za-z]/.test(form.password)) {
      setError('Password must contain at least one letter')
      return
    }

    if (!/[0-9]/.test(form.password)) {
      setError('Password must contain at least one number')
      return
    }

    if (form.password !== form.confirmPassword) {
      setError('Passwords must match')
      return
    }

    setLoading(true)
    try {
      await register({
        username: form.username,
        email: form.email,
        password: form.password,
        full_name: form.full_name
      })
      setSuccess(true)
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      let errorMessage = 'Registration failed'
      
      // Handle FastAPI validation errors (array of objects)
      if (err?.response?.data?.detail && Array.isArray(err.response.data.detail)) {
        const details = err.response.data.detail
        const messages = details
          .map(item => {
            // FastAPI validation error format: { loc: [...], msg: "...", type: "..." }
            if (typeof item === 'object' && item.msg) {
              const field = item.loc?.[1] || item.loc?.[0] || 'field'
              return `${field}: ${item.msg}`
            }
            return String(item)
          })
          .filter(Boolean)
        errorMessage = messages.length > 0 ? messages.join('; ') : errorMessage
      }
      // Handle simple string error messages
      else if (typeof err?.response?.data?.detail === 'string') {
        errorMessage = err.response.data.detail
      }
      // Handle generic error messages
      else if (err?.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4 py-6">
        <div className="glass-panel relative w-full max-w-md overflow-hidden rounded-3xl border border-emerald-400/30 p-8 text-center shadow-2xl">
          <div className="pointer-events-none absolute inset-0 opacity-20" style={{ background: 'radial-gradient(circle at top, rgba(0,255,148,0.3), transparent 50%)' }} />
          <div className="relative z-10">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/30 mx-auto">
              <svg className="h-8 w-8 text-emerald-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-black text-white">Registration Complete</h2>
            <p className="mt-3 text-sm text-slate-300">Your account is ready. Redirecting to login…</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-6">
      <div className="glass-panel relative w-full max-w-2xl overflow-hidden rounded-3xl border border-white/10 p-8 shadow-2xl">
        <div className="pointer-events-none absolute inset-0 opacity-30" style={{ background: 'radial-gradient(circle at top right, rgba(0,240,255,0.4), transparent 50%)' }} />
        
        <div className="relative z-10">
          <div className="mb-2">
            <p className="text-xs font-semibold tracking-[0.4em] text-kaiops-primary">CREATE ACCOUNT</p>
            <h2 className="mt-3 text-3xl font-black tracking-tight text-white">Join KaiOPS</h2>
            <p className="mt-1 text-xs font-semibold text-kaiops-primary/80 tracking-wider">Incidents End Here</p>
            <p className="mt-2 text-sm text-slate-300">Set up your operator credentials to begin.</p>
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

          <form onSubmit={handleSubmit} className="mt-6 grid gap-5 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold tracking-[0.3em] text-kaiops-primary/80">USERNAME</label>
              <input
                name="username"
                type="text"
                placeholder="operator_alpha"
                value={form.username}
                onChange={handleChange}
                required
                disabled={loading}
                className="glass-card mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-slate-400 transition focus:border-kaiops-primary/40 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold tracking-[0.3em] text-kaiops-primary/80">EMAIL</label>
              <input
                name="email"
                type="email"
                placeholder="operator@kaiops.dev"
                value={form.email}
                onChange={handleChange}
                required
                disabled={loading}
                className="glass-card mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-slate-400 transition focus:border-kaiops-primary/40 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold tracking-[0.3em] text-kaiops-primary/80">FULL NAME</label>
              <input
                name="full_name"
                type="text"
                placeholder="Your Name"
                value={form.full_name}
                onChange={handleChange}
                disabled={loading}
                className="glass-card mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-slate-400 transition focus:border-kaiops-primary/40 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold tracking-[0.3em] text-kaiops-primary/80">PASSWORD</label>
              <input
                name="password"
                type="password"
                placeholder="••••••••••••"
                value={form.password}
                onChange={handleChange}
                required
                disabled={loading}
                className="glass-card mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-slate-400 transition focus:border-kaiops-primary/40 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold tracking-[0.3em] text-kaiops-primary/80">CONFIRM PASSWORD</label>
              <input
                name="confirmPassword"
                type="password"
                placeholder="••••••••••••"
                value={form.confirmPassword}
                onChange={handleChange}
                required
                disabled={loading}
                className="glass-card mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-slate-400 transition focus:border-kaiops-primary/40 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="relative mt-2 w-full overflow-hidden rounded-2xl border border-kaiops-primary/40 bg-gradient-to-r from-kaiops-primary/20 to-kaiops-secondary/10 px-5 py-3 text-sm font-semibold text-white transition hover:border-kaiops-primary/60 hover:from-kaiops-primary/30 hover:to-kaiops-secondary/20 disabled:cursor-not-allowed disabled:from-slate-600/20 disabled:to-slate-700/20 sm:col-span-2"
            >
              {loading ? 'Creating Account…' : 'Begin Your Mission'}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-slate-400">
            Already registered?{' '}
            <Link to="/login" className="font-semibold text-kaiops-primary/80 transition hover:text-kaiops-primary">
              Sign in here
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Register
