import { createContext, useContext, useEffect, useState } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)
const TOKEN_KEY = 'axlero_access_token'

function decodeUser(token) {
  try {
    const payload = token.split('.')[1]
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const json = decodeURIComponent(
      atob(base64)
        .split('')
        .map((character) => `%${(`00${character.charCodeAt(0).toString(16)}`).slice(-2)}`)
        .join(''),
    )
    const { username, role } = JSON.parse(json)
    return username ? { username, role: role || 'USER' } : null
  } catch {
    return null
  }
}

function getErrorMessage(error, fallback) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(', ')
  return detail || error.response?.data?.error || fallback
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY)
    const savedUser = savedToken && decodeUser(savedToken)
    if (savedUser) {
      setToken(savedToken)
      setUser(savedUser)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
    setLoading(false)
  }, [])

  const login = async (credentials) => {
    try {
      const { data } = await api.post('/auth/login', credentials)
      const nextUser = data.access_token && decodeUser(data.access_token)
      if (!nextUser || data.token_type !== 'bearer') {
        throw new Error('Invalid username or password.')
      }
      localStorage.setItem(TOKEN_KEY, data.access_token)
      setToken(data.access_token)
      setUser(nextUser)
      return nextUser
    } catch (error) {
      throw new Error(error.message === 'Invalid username or password.' ? error.message : getErrorMessage(error, 'Unable to sign in. Please try again.'))
    }
  }

  const register = async (details) => {
    try {
      const { data } = await api.post('/auth/register', details)
      if (data.error) throw new Error(data.error)
      return data
    } catch (error) {
      throw new Error(error.response ? getErrorMessage(error, 'Unable to create your account.') : error.message || 'Unable to create your account.')
    }
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }

  return <AuthContext.Provider value={{ token, user, login, register, logout, isAuthenticated: Boolean(token && user), loading }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within an AuthProvider.')
  return context
}
