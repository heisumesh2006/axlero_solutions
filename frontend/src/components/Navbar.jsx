import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const handleLogout = () => { logout(); navigate('/login', { replace: true }) }

  return <header className="flex h-16 items-center justify-between border-b border-slate-800 bg-slate-950/80 px-4 backdrop-blur sm:px-6"><div><p className="text-sm font-medium text-slate-200">Security Operations</p><p className="text-xs text-slate-500">{user?.username ? `${user.username} · ${user.role}` : 'Monitor and assess your attack surface'}</p></div><button type="button" onClick={handleLogout} className="rounded-lg border border-slate-700 px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-800 hover:text-white">Log out</button></header>
}

export default Navbar
