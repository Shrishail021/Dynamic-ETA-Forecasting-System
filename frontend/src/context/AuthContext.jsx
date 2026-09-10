import React, { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api/client.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('eta_token'))
  const [role, setRole] = useState(() => localStorage.getItem('eta_role') || 'public')
  const [username, setUsername] = useState(() => localStorage.getItem('eta_user') || '')

  useEffect(() => {
    if (token) {
      api.getMe(token)
        .then((user) => {
          setRole(user.role)
          setUsername(user.username)
          localStorage.setItem('eta_role', user.role)
          localStorage.setItem('eta_user', user.username)
        })
        .catch(() => {
          // If token expired or invalid, reset
          logout()
        })
    }
  }, [token])

  const login = (newToken, newRole, newUsername = '') => {
    localStorage.setItem('eta_token', newToken)
    localStorage.setItem('eta_role', newRole)
    if (newUsername) localStorage.setItem('eta_user', newUsername)
    setToken(newToken)
    setRole(newRole)
    setUsername(newUsername)
  }

  const logout = () => {
    localStorage.removeItem('eta_token')
    localStorage.removeItem('eta_role')
    localStorage.removeItem('eta_user')
    setToken(null)
    setRole('public')
    setUsername('')
  }

  return (
    <AuthContext.Provider value={{ token, role, username, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
