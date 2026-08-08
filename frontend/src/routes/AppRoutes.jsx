import { Navigate, Route, Routes } from 'react-router-dom'
import DashboardLayout from '../layouts/DashboardLayout'
import Dashboard from '../pages/Dashboard'
import Login from '../pages/Login'
import NewScan from '../pages/NewScan'
import Register from '../pages/Register'
import ScanDetails from '../pages/ScanDetails'
import Scans from '../pages/Scans'
function AppRoutes() { return <Routes><Route path="/login" element={<Login />} /><Route path="/register" element={<Register />} /><Route element={<DashboardLayout />}><Route path="/dashboard" element={<Dashboard />} /><Route path="/scans" element={<Scans />} /><Route path="/scans/new" element={<NewScan />} /><Route path="/scans/:scanId" element={<ScanDetails />} /></Route><Route path="*" element={<Navigate to="/dashboard" replace />} /></Routes> }
export default AppRoutes
