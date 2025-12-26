import { createContext, useContext, useState, useEffect } from 'react'
import { login, getCurrentUser, updateSettings } from '../services/auth'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('token'))

  useEffect(() => {
    // Check if user is logged in on mount
    if (token) {
      checkAuth()
    } else {
      setLoading(false)
    }
  }, [])

  const checkAuth = async () => {
    try {
      const result = await getCurrentUser()
      if (result.success) {
        setUser(result.user)
      } else {
        // Token invalid, clear it
        localStorage.removeItem('token')
        setToken(null)
      }
    } catch (error) {
      localStorage.removeItem('token')
      setToken(null)
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = async (username, password) => {
    const result = await login(username, password)
    if (result.success) {
      setToken(result.token)
      setUser(result.user)
      localStorage.setItem('token', result.token)
      return { success: true }
    }
    return result
  }


  const handleLogout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  const handleUpdateSettings = async (settings) => {
    const result = await updateSettings(settings)
    if (result.success) {
      // Refresh user data
      await checkAuth()
    }
    return result
  }

  const value = {
    user,
    token,
    loading,
    login: handleLogin,
    logout: handleLogout,
    updateSettings: handleUpdateSettings,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin'
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}


