import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navigation = [{ label: 'Dashboard', to: '/dashboard' }, { label: 'Scans', to: '/scans' }, { label: 'New Scan', to: '/scans/new' }]

function Sidebar() {
  const { user } = useAuth()
  return <aside className="flex w-full shrink-0 flex-col border-b border-slate-800 bg-slate-950 md:min-h-screen md:w-64 md:border-b-0 md:border-r"><div className="flex h-16 items-center px-5"><NavLink to="/dashboard" className="flex items-center gap-3" aria-label="Axlero dashboard"><span className="grid h-8 w-8 place-items-center rounded-lg bg-cyan-400 text-sm font-black text-slate-950">A</span><span className="text-lg font-semibold tracking-tight text-white">Axlero</span></NavLink></div><nav className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col" aria-label="Primary navigation">{navigation.map((item) => <NavLink key={item.to} to={item.to} className={({ isActive }) => `whitespace-nowrap rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${isActive ? 'bg-cyan-400/10 text-cyan-300 ring-1 ring-inset ring-cyan-400/20' : 'text-slate-400 hover:bg-slate-900 hover:text-slate-100'}`}>{item.label}</NavLink>)}</nav>{user && <div className="mt-auto hidden border-t border-slate-800 px-5 py-5 md:block"><p className="truncate text-sm font-medium text-slate-200">{user.username}</p><p className="mt-1 text-xs font-medium tracking-wide text-cyan-400">{user.role}</p></div>}</aside>
}

export default Sidebar
