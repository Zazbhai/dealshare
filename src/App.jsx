import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Dashboard from './pages/Dashboard'
import Admin from './pages/Admin'
import Login from './pages/Login'
import Settings from './pages/Settings'
import { LayoutDashboard, Settings as SettingsIcon, LogOut, UserCog } from 'lucide-react'

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full"
        />
      </div>
    )
  }
  
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Navbar />
                  <AnimatePresence mode="wait">
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/admin" element={<Admin />} />
                      <Route path="/settings" element={<Settings />} />
                    </Routes>
                  </AnimatePresence>
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  )
}

function Navbar() {
  const location = useLocation()
  const { user, logout } = useAuth()
  
  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-lg border-b border-purple-500/20"
    >
      <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4">
        <div className="flex items-center justify-between">
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="text-lg sm:text-xl md:text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent truncate"
          >
            <span className="hidden sm:inline">DealShare Automation</span>
            <span className="sm:hidden">DealShare</span>
          </motion.div>
          
          <div className="flex items-center gap-2 sm:gap-4">
            <NavLink to="/" icon={<LayoutDashboard />} label="Dashboard" active={location.pathname === '/'} />
            {user?.role === 'admin' && (
              <NavLink to="/admin" icon={<SettingsIcon />} label="Admin" active={location.pathname === '/admin'} />
            )}
            <NavLink to="/settings" icon={<UserCog />} label="Settings" active={location.pathname === '/settings'} />
            
            {/* User Info & Logout */}
            <div className="flex items-center gap-2 sm:gap-3 pl-2 sm:pl-4 border-l border-gray-700">
              <span className="hidden sm:inline text-sm text-gray-300">{user?.username}</span>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={logout}
                className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-2 text-gray-300 hover:text-white hover:bg-gray-800 rounded-lg transition-all text-sm"
              >
                <LogOut className="w-4 h-4 sm:w-5 sm:h-5" />
                <span className="hidden sm:inline">Logout</span>
              </motion.button>
            </div>
          </div>
        </div>
      </div>
    </motion.nav>
  )
}

function NavLink({ to, icon, label, active }) {
  return (
    <Link to={to}>
      <motion.div
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-4 py-2 rounded-lg transition-all ${
          active
            ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/50'
            : 'text-gray-300 hover:bg-gray-800'
        }`}
      >
        <div className="w-5 h-5 sm:w-6 sm:h-6">{icon}</div>
        <span className="hidden sm:inline text-sm sm:text-base">{label}</span>
      </motion.div>
    </Link>
  )
}

export default App

