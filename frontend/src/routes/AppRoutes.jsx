import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import DashboardLayout from '../layouts/DashboardLayout'
import Dashboard from '../pages/Dashboard'
import Login from '../pages/Login'
import NewScan from '../pages/NewScan'
import Register from '../pages/Register'
import ScanDetails from '../pages/ScanDetails'
import Scans from '../pages/Scans'
import ProtectedRoute from './ProtectedRoute'

function PublicOnlyRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return null
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : children
}

function AppRoutes() {
  return <Routes><Route path="/login" element={<PublicOnlyRoute><Login /></PublicOnlyRoute>} /><Route path="/register" element={<PublicOnlyRoute><Register /></PublicOnlyRoute>} /><Route element={<ProtectedRoute />}><Route element={<DashboardLayout />}><Route path="/dashboard" element={<Dashboard />} /><Route path="/scans" element={<Scans />} /><Route path="/scans/new" element={<NewScan />} /><Route path="/scans/:scanId" element={<ScanDetails />} /></Route></Route><Route path="*" element={<Navigate to="/dashboard" replace />} /></Routes>
}

export default AppRoutes
