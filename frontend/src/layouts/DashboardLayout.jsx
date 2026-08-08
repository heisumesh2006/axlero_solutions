import { Outlet } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
function DashboardLayout() { return <div className="min-h-screen bg-slate-950 md:flex"><Sidebar /><div className="min-w-0 flex-1"><Navbar /><main className="mx-auto w-full max-w-7xl p-4 sm:p-6 lg:p-8"><Outlet /></main></div></div> }
export default DashboardLayout
