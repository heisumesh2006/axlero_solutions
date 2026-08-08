import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import ErrorMessage from '../components/ErrorMessage'
import { useAuth } from '../context/AuthContext'

function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { login, isAuthenticated, loading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const destination = location.state?.from?.pathname || '/dashboard'

  if (!loading && isAuthenticated) return <Navigate to="/dashboard" replace />

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try { await login({ username, password }); navigate(destination, { replace: true }) }
    catch (loginError) { setError(loginError.message) }
    finally { setSubmitting(false) }
  }

  return <main className="grid min-h-screen place-items-center bg-slate-950 p-6"><section className="surface w-full max-w-md p-8"><div className="mb-8 flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-lg bg-cyan-400 font-black text-slate-950">A</span><span className="text-xl font-semibold text-white">Axlero</span></div><h1 className="page-title">Welcome back</h1><p className="page-copy">Sign in to your Axlero security workspace.</p><form className="mt-8 space-y-5" onSubmit={handleSubmit}>{error && <ErrorMessage>{error}</ErrorMessage>}<label className="block text-sm font-medium text-slate-300">Username<input required autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white outline-none transition focus:border-cyan-400" /></label><label className="block text-sm font-medium text-slate-300">Password<input required type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white outline-none transition focus:border-cyan-400" /></label><button disabled={submitting} className="w-full rounded-lg bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60">{submitting ? 'Signing in...' : 'Sign in'}</button></form><p className="mt-6 text-sm text-slate-400">New to Axlero? <Link className="text-cyan-300 hover:text-cyan-200" to="/register">Create an account</Link></p></section></main>
}

export default Login
