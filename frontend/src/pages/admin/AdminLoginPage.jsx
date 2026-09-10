import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client.js'
import { useAuth } from '../../context/AuthContext.jsx'

export default function AdminLoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const auth = useAuth()
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const res = await api.login(username, password)
      auth.login(res.access_token, res.role, username)
      if (res.role === 'admin') {
        navigate('/admin/trains')
      } else {
        navigate('/control-room')
      }
    } catch (err) {
      setError(err.message || 'Login failed. Please verify credentials.')
    } finally {
      setLoading(false)
    }
  }

  const fillCredentials = (u, p) => {
    setUsername(u)
    setPassword(p)
  }

  return (
    <div className="w-full flex-1 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md glass-panel-elevated p-8 rounded-2xl flex flex-col items-center gap-6 relative">
        
        {/* Brand Emblem */}
        <div className="w-14 h-14 rounded-2xl bg-primary-container/20 border border-primary-container/50 flex items-center justify-center shadow-[0_0_20px_rgba(51,194,255,0.35)]">
          <span className="material-symbols-outlined text-primary text-3xl">lock</span>
        </div>

        <div className="text-center space-y-1">
          <h1 className="font-display font-bold text-2xl text-on-surface">
            Control Portal Access
          </h1>
          <p className="text-xs text-on-surface-variant">
            Authorized operations dispatch and system administration.
          </p>
        </div>

        {/* Error Callout */}
        {error && (
          <div className="w-full p-3 rounded-xl bg-hazard-coral/15 border border-hazard-coral/40 text-hazard-coral text-xs flex items-center gap-2">
            <span className="material-symbols-outlined text-base shrink-0">error</span>
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleLogin} className="w-full flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-display font-semibold text-outline uppercase tracking-wider">
              Operator Username
            </label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[18px]">
                badge
              </span>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin or staff"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-surface-container-lowest border border-outline-variant/40 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:border-primary"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-display font-semibold text-outline uppercase tracking-wider">
              Security Key / Password
            </label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[18px]">
                key
              </span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-surface-container-lowest border border-outline-variant/40 text-sm text-on-surface placeholder:text-outline focus:outline-none focus:border-primary"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 rounded-xl bg-primary-container hover:bg-primary text-black font-display font-bold text-sm tracking-wide transition-all shadow-[0_0_16px_rgba(51,194,255,0.4)] flex items-center justify-center gap-2"
          >
            {loading ? (
              <span className="material-symbols-outlined animate-spin text-lg">progress_activity</span>
            ) : (
              <>
                <span className="material-symbols-outlined text-[18px]">login</span>
                <span>Authenticate Session</span>
              </>
            )}
          </button>
        </form>

        {/* Demo Fast Autofill */}
        <div className="w-full pt-4 border-t border-outline-variant/30 flex flex-col gap-2">
          <span className="text-[10px] font-display font-bold text-outline uppercase tracking-wider text-center">
            One-Click Demo Credentials:
          </span>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => fillCredentials('admin', 'admin123')}
              className="px-2.5 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container-highest border border-outline-variant/40 text-left text-xs text-on-surface transition-colors"
            >
              <span className="font-display font-bold text-primary block">Admin</span>
              <span className="text-[10px] text-outline">admin / admin123</span>
            </button>
            <button
              type="button"
              onClick={() => fillCredentials('staff', 'staff123')}
              className="px-2.5 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container-highest border border-outline-variant/40 text-left text-xs text-on-surface transition-colors"
            >
              <span className="font-display font-bold text-secondary block">Staff</span>
              <span className="text-[10px] text-outline">staff / staff123</span>
            </button>
          </div>
          <p className="text-[10px] text-center text-on-surface-variant/70 mt-1">
            Admin has Train Master CRUD + Model Benchmarks. Staff has Control Room access.
          </p>
        </div>

      </div>
    </div>
  )
}
