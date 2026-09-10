import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client.js'
import { useAuth } from '../../context/AuthContext.jsx'

export default function ControlRoomPage() {
  const { token, role } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filterRoute, setFilterRoute] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchOverview = () => {
    if (!token) return
    api.getControlRoomOverview(token)
      .then((res) => {
        setData(res)
        setError(null)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchOverview()
    if (!autoRefresh) return
    const timer = setInterval(fetchOverview, 10000) // Poll every 10s
    return () => clearInterval(timer)
  }, [token, autoRefresh])

  if (!token) {
    return (
      <div className="py-24 text-center">
        <p className="text-on-surface-variant mb-3">Operator or staff credentials required to access Control Room.</p>
        <Link to="/admin/login" className="px-4 py-2 rounded-lg bg-primary-container text-black font-display font-bold text-xs">
          Staff Portal Login
        </Link>
      </div>
    )
  }

  const trains = (data?.trains || []).filter((t) => !filterRoute || t.route_id === filterRoute)

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 py-8 flex flex-col gap-6">
      
      {/* Control Room Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-outline-variant/30 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="w-3 h-3 rounded-full bg-primary-container animate-pulse shadow-[0_0_10px_#33c2ff]"></span>
            <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-on-surface">
              Operations Control Room (COA Stand-In)
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
            Sectional train occupancy, dynamic arrival intervals, and congestion advisories across network corridors.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
              autoRefresh
                ? 'bg-primary-container/20 border-primary text-primary'
                : 'bg-surface-container-high border-outline-variant/40 text-on-surface-variant'
            }`}
          >
            <span className={`material-symbols-outlined text-[16px] ${autoRefresh ? 'animate-spin' : ''}`}>
              autorenew
            </span>
            {autoRefresh ? 'Auto Sync: 10s' : 'Auto Sync Paused'}
          </button>
          <button
            onClick={fetchOverview}
            className="p-2 rounded-lg bg-surface-container-high hover:bg-surface-container-highest border border-outline-variant/40 text-on-surface"
            title="Refresh now"
          >
            <span className="material-symbols-outlined text-[18px]">refresh</span>
          </button>
        </div>
      </div>

      {/* Network KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Active Trains */}
        <div className="glass-panel p-4 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-[10px] font-display uppercase font-bold text-outline">Active Tracked Trains</span>
            <div className="font-display font-bold text-2xl sm:text-3xl text-primary mt-0.5">
              {data?.total_active_trains || 0}
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-primary-container/15 text-primary flex items-center justify-center">
            <span className="material-symbols-outlined text-xl">train</span>
          </div>
        </div>

        {/* Network Punctuality */}
        <div className="glass-panel p-4 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-[10px] font-display uppercase font-bold text-outline">Network Punctuality</span>
            <div className="font-display font-bold text-2xl sm:text-3xl text-secondary mt-0.5">
              {data?.system_punctuality_rate || 0}%
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-secondary/15 text-secondary flex items-center justify-center">
            <span className="material-symbols-outlined text-xl">speed</span>
          </div>
        </div>

        {/* Average Delay */}
        <div className="glass-panel p-4 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-[10px] font-display uppercase font-bold text-outline">Average Network Delay</span>
            <div className="font-display font-bold text-2xl sm:text-3xl text-hazard-coral mt-0.5">
              +{data?.average_network_delay_min || 0} min
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-hazard-coral/15 text-hazard-coral flex items-center justify-center">
            <span className="material-symbols-outlined text-xl">alarm</span>
          </div>
        </div>
      </div>

      {/* Corridor Filter Strip */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-[10px] font-display font-bold text-outline uppercase tracking-wider shrink-0">
          Filter Corridor:
        </span>
        {['', 'R1', 'R2', 'R3', 'R4', 'R5'].map((r) => (
          <button
            key={r}
            onClick={() => setFilterRoute(r)}
            className={`px-3 py-1 rounded-full border text-xs font-semibold transition-all shrink-0 ${
              filterRoute === r
                ? 'bg-primary-container text-black border-primary font-bold shadow-[0_0_10px_rgba(51,194,255,0.4)]'
                : 'bg-surface-container-high/80 text-on-surface-variant border-outline-variant/40 hover:bg-surface-container-highest'
            }`}
          >
            {r ? `Corridor ${r}` : 'All Corridors'}
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-hazard-coral/20 border border-hazard-coral/40 text-hazard-coral text-xs">
          {error}
        </div>
      )}

      {/* Multi-Train Telemetry Matrix */}
      <div className="glass-panel rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs sm:text-sm">
            <thead>
              <tr className="border-b border-outline-variant/30 text-on-surface-variant text-[11px] font-display uppercase tracking-wider bg-surface-container-low/80">
                <th className="py-3 px-4">Train</th>
                <th className="py-3 px-4">Corridor</th>
                <th className="py-3 px-4">Current Stop</th>
                <th className="py-3 px-4">Current Delay</th>
                <th className="py-3 px-4">Next Station &amp; ML ETA (P50 / P90)</th>
                <th className="py-3 px-4">Advisories</th>
                <th className="py-3 px-4 text-right">Radar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/20">
              {loading && !data ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-on-surface-variant">
                    <span className="material-symbols-outlined animate-spin text-2xl text-primary mb-2">progress_activity</span>
                    <p>Polling live corridor feeds...</p>
                  </td>
                </tr>
              ) : trains.map((t) => {
                const isCritical = t.status === 'CRITICAL'
                const isDelayed = t.status === 'DELAYED'
                return (
                  <tr key={t.train_no} className="hover:bg-surface-container-high/40 transition-colors">
                    {/* Train info */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-display font-bold text-primary">{t.train_no}</span>
                        <span className="px-1.5 py-0.5 rounded bg-surface-container-highest font-display text-[9px] font-bold text-secondary">
                          P{t.priority}
                        </span>
                      </div>
                      <span className="text-xs font-semibold text-on-surface block truncate max-w-[180px]">
                        {t.train_name}
                      </span>
                    </td>

                    {/* Corridor */}
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded bg-surface-container-highest font-display text-xs font-bold text-on-surface">
                        {t.route_id}
                      </span>
                      <span className="text-[10px] text-outline block mt-0.5">
                        {t.origin} → {t.destination}
                      </span>
                    </td>

                    {/* Current Position */}
                    <td className="py-3 px-4 font-display font-bold text-on-surface">
                      {t.current_station}
                    </td>

                    {/* Delay */}
                    <td className="py-3 px-4">
                      <span className={`font-display font-bold tabular-nums ${isCritical ? 'text-hazard-coral' : isDelayed ? 'text-secondary' : 'text-primary'}`}>
                        +{t.current_delay_min} min
                      </span>
                      <span className={`block text-[9px] font-bold uppercase ${isCritical ? 'text-hazard-coral' : isDelayed ? 'text-secondary' : 'text-primary'}`}>
                        {t.status.replace('_', ' ')}
                      </span>
                    </td>

                    {/* Next ETA */}
                    <td className="py-3 px-4">
                      <div className="flex items-baseline gap-2">
                        <span className="font-display font-bold text-on-surface">{t.next_station}</span>
                        <span className="text-xs font-display text-primary font-bold">
                          +{t.next_eta_p50}m
                        </span>
                        <span className="text-[10px] font-display text-on-surface-variant">
                          (P90: +{t.next_eta_p90}m)
                        </span>
                      </div>
                    </td>

                    {/* Advisories */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {t.is_fog_prone && (
                          <span className="px-2 py-0.5 rounded bg-secondary/15 text-secondary border border-secondary/30 text-[10px] font-display font-bold flex items-center gap-1">
                            <span className="material-symbols-outlined text-[12px]">foggy</span>
                            Fog Zone
                          </span>
                        )}
                        {t.congestion_index > 0.4 && (
                          <span className="px-2 py-0.5 rounded bg-hazard-coral/15 text-hazard-coral border border-hazard-coral/30 text-[10px] font-display font-bold flex items-center gap-1">
                            <span className="material-symbols-outlined text-[12px]">traffic</span>
                            Congestion
                          </span>
                        )}
                        {!t.is_fog_prone && t.congestion_index <= 0.4 && (
                          <span className="text-[10px] text-outline">Nominal</span>
                        )}
                      </div>
                    </td>

                    {/* Radar Action */}
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/trains/${t.train_no}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-surface-container-high hover:bg-primary-container hover:text-black text-xs font-display font-bold text-primary transition-colors"
                      >
                        Track <span className="material-symbols-outlined text-[14px]">chevron_right</span>
                      </Link>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}
