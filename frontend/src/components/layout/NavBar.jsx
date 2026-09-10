import React, { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'

export default function NavBar() {
  const { role, username, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
    setMobileOpen(false)
  }

  const navLinkClass = ({ isActive }) =>
    `px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-1.5 ${
      isActive
        ? 'bg-primary text-white shadow-md'
        : 'text-on-surface-variant hover:text-primary hover:bg-surface-container-high'
    }`

  const mobileNavLinkClass = ({ isActive }) =>
    `px-4 py-3 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 ${
      isActive
        ? 'bg-primary text-white'
        : 'text-on-surface-variant hover:bg-surface-container-high hover:text-primary'
    }`

  return (
    <header className="fixed top-0 w-full z-50 bg-white/90 backdrop-blur-xl border-b border-outline-variant shadow-sm">
      <div className="max-w-7xl mx-auto h-16 px-4 sm:px-6 flex items-center justify-between">
        
        {/* Brand & Emblem */}
        <Link to="/" className="flex items-center gap-3 group" onClick={() => setMobileOpen(false)}>
          <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center shadow-md group-hover:scale-105 transition-transform">
            <span className="material-symbols-outlined text-white text-[22px]">train</span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-display font-bold text-lg tracking-tight text-navy">RailPulse</span>
            </div>
            <span className="text-[10px] text-on-surface-variant tracking-wider uppercase font-semibold">
              Dynamic ETA Engine
            </span>
          </div>
        </Link>

        {/* Center Nav Links (Desktop) */}
        <nav className="hidden md:flex items-center gap-1">
          <NavLink to="/" end className={navLinkClass}>
            <span className="material-symbols-outlined text-[17px]">radar</span>
            Radar
          </NavLink>
          <NavLink to="/trains" className={navLinkClass}>
            <span className="material-symbols-outlined text-[17px]">grid_view</span>
            Browse Trains
          </NavLink>
          <NavLink to="/station-master" className={navLinkClass}>
            <span className="material-symbols-outlined text-[17px]">meeting_room</span>
            Station Master
          </NavLink>
          <NavLink to="/control-room" className={navLinkClass}>
            <span className="material-symbols-outlined text-[17px]">monitoring</span>
            Control Room
          </NavLink>
          <NavLink to="/admin/models" className={navLinkClass}>
            <span className="material-symbols-outlined text-[17px]">analytics</span>
            Benchmarks
          </NavLink>
          {role === 'admin' && (
            <NavLink to="/admin/trains" className={navLinkClass}>
              <span className="material-symbols-outlined text-[17px]">settings_input_component</span>
              Train Master
            </NavLink>
          )}
        </nav>

        {/* Right Section: Live Badge & Auth */}
        <div className="flex items-center gap-3">
          {/* Live Sync Badge */}
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-green-50 border border-green-200">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            <span className="text-[10px] font-display font-bold text-green-700 tracking-widest uppercase">
              LIVE
            </span>
          </div>

          {/* User Status / Login Button */}
          {isAuthenticated ? (
            <div className="flex items-center gap-2">
              <div className="px-2.5 py-1 rounded-lg bg-surface-container-high border border-outline-variant flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px] text-primary">account_circle</span>
                <span className="text-xs font-medium text-on-surface">{username || role}</span>
                <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-primary text-white font-bold">
                  {role}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="p-1.5 rounded-lg hover:bg-red-50 text-on-surface-variant hover:text-red-600 transition-colors"
                title="Log out"
              >
                <span className="material-symbols-outlined text-[18px]">logout</span>
              </button>
            </div>
          ) : (
            <Link
              to="/admin/login"
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-primary hover:bg-navy text-white text-xs font-semibold tracking-wide transition-all shadow-md"
            >
              <span className="material-symbols-outlined text-[16px]">lock</span>
              Staff Login
            </Link>
          )}

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2 rounded-lg hover:bg-surface-container-high transition-colors"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            <span className="material-symbols-outlined text-on-surface text-[22px]">
              {mobileOpen ? 'close' : 'menu'}
            </span>
          </button>
        </div>
      </div>

      {/* Mobile Nav Dropdown */}
      {mobileOpen && (
        <div className="md:hidden bg-white border-t border-outline-variant px-4 py-3 flex flex-col gap-1 shadow-lg">
          <NavLink to="/" end className={mobileNavLinkClass} onClick={() => setMobileOpen(false)}>
            <span className="material-symbols-outlined text-[18px]">radar</span>
            Radar Hub
          </NavLink>
          <NavLink to="/trains" className={mobileNavLinkClass} onClick={() => setMobileOpen(false)}>
            <span className="material-symbols-outlined text-[18px]">grid_view</span>
            Browse Trains
          </NavLink>
          <NavLink to="/station-master" className={mobileNavLinkClass} onClick={() => setMobileOpen(false)}>
            <span className="material-symbols-outlined text-[18px]">meeting_room</span>
            Station Master
          </NavLink>
          <NavLink to="/control-room" className={mobileNavLinkClass} onClick={() => setMobileOpen(false)}>
            <span className="material-symbols-outlined text-[18px]">monitoring</span>
            Control Room
          </NavLink>
          <NavLink to="/admin/models" className={mobileNavLinkClass} onClick={() => setMobileOpen(false)}>
            <span className="material-symbols-outlined text-[18px]">analytics</span>
            Benchmarks
          </NavLink>
          {role === 'admin' && (
            <NavLink to="/admin/trains" className={mobileNavLinkClass} onClick={() => setMobileOpen(false)}>
              <span className="material-symbols-outlined text-[18px]">settings_input_component</span>
              Train Master
            </NavLink>
          )}
          {!isAuthenticated && (
            <Link
              to="/admin/login"
              className="mt-1 px-4 py-3 rounded-xl bg-primary text-white text-sm font-semibold flex items-center gap-2"
              onClick={() => setMobileOpen(false)}
            >
              <span className="material-symbols-outlined text-[18px]">lock</span>
              Staff / Admin Login
            </Link>
          )}
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="mt-1 px-4 py-3 rounded-xl bg-red-50 text-red-600 text-sm font-semibold flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-[18px]">logout</span>
              Log Out ({username || role})
            </button>
          )}
        </div>
      )}
    </header>
  )
}
