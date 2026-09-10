import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../api/client.js'

export default function HomePage() {
  const [trains, setTrains] = useState([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [gpsLoading, setGpsLoading] = useState(false)
  const [gpsError, setGpsError] = useState(null)
  const [nearbyData, setNearbyData] = useState(null)
  const navigate = useNavigate()

  const fetchNearbyTrains = (lat, lon, cityName = '') => {
    setGpsLoading(true)
    setGpsError(null)
    api.getNearbyTrains(lat, lon)
      .then((res) => setNearbyData(res))
      .catch((err) => setGpsError(`Unable to locate nearest station for ${cityName || 'location'}: ${err.message}`))
      .finally(() => setGpsLoading(false))
  }

  const handleGetGpsLocation = () => {
    if (!navigator.geolocation) { setGpsError('Geolocation is not supported by your browser.'); return }
    setGpsLoading(true)
    setGpsError(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => fetchNearbyTrains(pos.coords.latitude, pos.coords.longitude),
      (err) => {
        setGpsLoading(false)
        setGpsError(err.code === 1
          ? 'Location permission denied. Use a test city button below!'
          : `GPS error: ${err.message}`)
      },
      { timeout: 10000, enableHighAccuracy: true }
    )
  }

  useEffect(() => {
    api.listTrains()
      .then((data) => setTrains(data))
      .catch((err) => console.error('Failed to load trains:', err))
      .finally(() => setLoading(false))
  }, [])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    if (query.trim()) navigate(`/trains?search=${encodeURIComponent(query.trim())}`)
    else navigate('/trains')
  }

  const handleChipClick = (q) => {
    if (/^\d{5}$/.test(q)) navigate(`/trains/${q}`)
    else navigate(`/trains?search=${encodeURIComponent(q)}`)
  }

  const typeBadge = (type) => {
    switch (type) {
      case 'rajdhani_shatabdi_vb': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'superfast':            return 'bg-indigo-100 text-indigo-800 border-indigo-200'
      case 'express':              return 'bg-sky-100 text-sky-800 border-sky-200'
      case 'passenger':            return 'bg-slate-100 text-slate-600 border-slate-200'
      default:                     return 'bg-gray-100 text-gray-600 border-gray-200'
    }
  }

  return (
    <div className="w-full min-h-[calc(100vh-4rem)] bg-background flex flex-col items-center">
      
      {/* ── Hero Banner ── */}
      <div className="w-full bg-gradient-to-br from-navy via-navy-light to-primary-container pt-20 pb-16 px-4 sm:px-6 text-white">
        <div className="max-w-5xl mx-auto flex flex-col items-center text-center gap-5">

          {/* Status pill */}
          <div className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/15 border border-white/25 backdrop-blur-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-300 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-400"></span>
            </span>
            <span className="font-display text-[11px] font-bold text-white/90 tracking-widest uppercase">
              RADAR ACTIVE · TELEMETRY ENGINE ONLINE
            </span>
          </div>

          <h1 className="font-display text-3xl sm:text-5xl font-bold tracking-tight leading-tight">
            Precision Transit Radar &amp;<br className="hidden sm:block" /> Dynamic ETA Forecasting
          </h1>
          <p className="max-w-2xl text-sm sm:text-base text-blue-100 font-normal">
            Next-generation Indian Railways prototype replacing static arithmetic with quantile machine learning,
            cascading delay propagation, and live telemetry simulation.
          </p>

          {/* Search Bar */}
          <div className="w-full max-w-2xl mt-2">
            <form onSubmit={handleSearchSubmit}>
              <div className="flex items-center w-full bg-white rounded-2xl px-4 py-3.5 shadow-xl border border-white/40">
                <span className="material-symbols-outlined text-primary text-2xl mr-3">search</span>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search train number (12302), name (Rajdhani), or station (NDLS)..."
                  className="w-full bg-transparent font-sans text-sm sm:text-base text-navy placeholder:text-slate-400 focus:outline-none tracking-wide"
                />
                <button
                  type="submit"
                  className="ml-2 px-5 py-2 rounded-xl bg-primary hover:bg-navy text-white font-display text-xs font-bold tracking-wide transition-all shadow-md"
                >
                  Track
                </button>
              </div>
            </form>

            {/* Hot Query Chips */}
            <div className="flex items-center gap-2 mt-3 overflow-x-auto pb-1 text-xs">
              <span className="text-[11px] font-display font-bold text-blue-200 uppercase tracking-wider shrink-0">
                Quick:
              </span>
              {[
                { label: '12302 Rajdhani', val: '12302', icon: 'bolt' },
                { label: '12951 Mumbai Raj.', val: '12951', icon: 'speed' },
                { label: '12007 Shatabdi', val: '12007', icon: 'fast_forward' },
                { label: 'NDLS Corridor', val: 'NDLS', icon: 'location_on' },
                { label: 'HWH Hub', val: 'HWH', icon: 'hub' },
              ].map((chip) => (
                <button
                  key={chip.val}
                  onClick={() => handleChipClick(chip.val)}
                  className="shrink-0 flex items-center gap-1 px-3 py-1 rounded-full bg-white/15 hover:bg-white/25 border border-white/20 text-white text-xs font-medium transition-all hover:scale-105"
                >
                  <span className="material-symbols-outlined text-[13px]">{chip.icon}</span>
                  {chip.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Content area ── */}
      <div className="w-full max-w-5xl px-4 sm:px-6 py-8 flex flex-col gap-8">

        {/* GPS Location Finder */}
        <div className="bg-white rounded-2xl border border-outline-variant shadow-card p-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="material-symbols-outlined text-primary text-xl">near_me</span>
                <span className="font-display font-bold text-base text-navy">Browse by Your GPS Location</span>
              </div>
              <p className="text-xs text-on-surface-variant">
                Find all trains passing through the nearest station to you.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={handleGetGpsLocation}
                disabled={gpsLoading}
                className="px-4 py-2 rounded-xl bg-primary hover:bg-navy text-white text-xs font-display font-bold flex items-center gap-1.5 transition-all shadow-md disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-sm">
                  {gpsLoading ? 'progress_activity' : 'my_location'}
                </span>
                {gpsLoading ? 'Detecting...' : 'Use My GPS'}
              </button>
              <span className="text-[11px] text-outline">or test:</span>
              {[
                { label: 'Delhi', lat: 28.6431, lon: 77.2197 },
                { label: 'Mumbai', lat: 18.9696, lon: 72.8193 },
                { label: 'Bengaluru', lat: 12.9781, lon: 77.5696 },
              ].map((city) => (
                <button
                  key={city.label}
                  type="button"
                  onClick={() => fetchNearbyTrains(city.lat, city.lon, city.label)}
                  className="px-3 py-1.5 rounded-lg bg-surface-container-high border border-outline-variant text-xs text-on-surface-variant hover:text-primary hover:border-primary transition-colors font-medium"
                >
                  {city.label}
                </button>
              ))}
            </div>
          </div>

          {gpsError && (
            <div className="mt-3 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs flex items-center justify-between">
              <span>{gpsError}</span>
              <button onClick={() => setGpsError(null)} className="font-bold ml-2 hover:text-red-900">✕</button>
            </div>
          )}

          {nearbyData && (
            <div className="mt-4 p-4 rounded-xl bg-blue-50 border border-blue-200 flex flex-col gap-3 animate-fadeIn">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-lg bg-primary text-white font-display font-bold text-sm">
                    {nearbyData.nearest_station.station_code}
                  </span>
                  <span className="font-display font-bold text-navy text-base">
                    {nearbyData.nearest_station.station_name}
                  </span>
                  <span className="text-xs text-primary font-semibold bg-blue-100 px-2 py-0.5 rounded-full border border-blue-200">
                    ~{nearbyData.distance_km} km
                  </span>
                </div>
                <button onClick={() => setNearbyData(null)} className="text-slate-400 hover:text-slate-600 text-sm font-bold">✕</button>
              </div>
              <p className="text-xs text-on-surface-variant">
                <span className="font-bold text-navy">{nearbyData.total_trains} trains</span> with stops at this station:
              </p>
              <div className="flex flex-wrap gap-2">
                {nearbyData.passing_trains.map((pt) => (
                  <Link
                    key={pt.train_no}
                    to={`/trains/${pt.train_no}`}
                    className="px-3 py-1.5 rounded-lg bg-white hover:bg-primary hover:text-white border border-blue-200 text-xs font-medium flex items-center gap-1.5 transition-all shadow-sm text-navy"
                  >
                    <span className="font-bold text-primary group-hover:text-white">{pt.train_no}</span>
                    <span className="opacity-70">{pt.train_name}</span>
                    <span className="material-symbols-outlined text-[13px]">arrow_forward</span>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Tracked Corridors Grid */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-xl">train</span>
              <h2 className="font-display font-bold text-lg text-navy">Tracked Train Corridors</h2>
            </div>
            <Link to="/trains" className="text-xs text-primary hover:text-navy hover:underline flex items-center gap-1 font-semibold transition-colors">
              View All ({trains.length})
              <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {loading ? (
              <div className="col-span-3 py-10 text-center text-on-surface-variant flex flex-col items-center gap-2">
                <span className="material-symbols-outlined text-3xl animate-spin text-primary">progress_activity</span>
                <span className="text-sm">Loading corridors...</span>
              </div>
            ) : (
              trains.slice(0, 6).map((t) => (
                <Link
                  key={t.train_no}
                  to={`/trains/${t.train_no}`}
                  className="group bg-white hover:shadow-card-hover border border-outline-variant rounded-xl p-4 transition-all duration-200 flex flex-col justify-between card-hover"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-display font-bold text-base text-primary">{t.train_no}</span>
                        <span className={`text-[10px] uppercase font-display font-bold px-2 py-0.5 rounded-full border ${typeBadge(t.train_type)}`}>
                          {t.train_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <h3 className="text-sm font-semibold text-navy truncate max-w-[190px]">{t.train_name}</h3>
                    </div>
                    <span className="relative flex h-2.5 w-2.5 mt-1">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs text-on-surface-variant pt-2 border-t border-outline-variant mt-1">
                    <span className="font-display font-semibold text-outline">Route {t.route_id}</span>
                    <span className="flex items-center gap-0.5 text-primary group-hover:gap-1 transition-all font-semibold">
                      Track Live
                      <span className="material-symbols-outlined text-[14px]">chevron_right</span>
                    </span>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* How It Works */}
        <div className="bg-white rounded-2xl border border-outline-variant shadow-card p-6">
          <h3 className="font-display font-bold text-center text-sm uppercase tracking-wider text-on-surface-variant mb-6">
            How Dynamic Forecasting Outperforms Static Timetables
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { icon: 'gps_fixed', color: 'bg-blue-50 text-primary', title: '1. Live Section Telemetry', desc: 'Captures GPS position pings and sectional speed anomalies to infer delays and choke points in real time.' },
              { icon: 'neurology', color: 'bg-amber-50 text-secondary', title: '2. Autoregressive ML Models', desc: 'Section-level Gradient Boosted Quantile Regressors predict next-stop running times, chaining cascades forward.' },
              { icon: 'query_stats', color: 'bg-red-50 text-hazard-coral', title: '3. P50 / P90 Uncertainty Bands', desc: 'Delivers realistic arrival intervals ("Likely arrival" to "Could be as late as") rather than single fragile points.' },
            ].map((step) => (
              <div key={step.title} className="flex flex-col items-center text-center p-4 rounded-xl bg-surface-container-low border border-outline-variant">
                <div className={`w-12 h-12 rounded-xl ${step.color} flex items-center justify-center mb-3 shadow-sm`}>
                  <span className="material-symbols-outlined text-2xl">{step.icon}</span>
                </div>
                <h4 className="font-display font-bold text-sm text-navy mb-1">{step.title}</h4>
                <p className="text-xs text-on-surface-variant leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Links Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pb-4">
          {[
            { to: '/trains', icon: 'grid_view', label: 'Browse All Trains', color: 'text-primary' },
            { to: '/control-room', icon: 'monitoring', label: 'Control Room', color: 'text-secondary' },
            { to: '/admin/models', icon: 'analytics', label: 'ML Benchmarks', color: 'text-tertiary' },
            { to: '/admin/login', icon: 'lock', label: 'Staff Login', color: 'text-on-surface-variant' },
          ].map((lnk) => (
            <Link
              key={lnk.to}
              to={lnk.to}
              className="flex flex-col items-center gap-2 p-4 bg-white border border-outline-variant rounded-xl hover:shadow-card-hover card-hover text-center transition-all"
            >
              <span className={`material-symbols-outlined text-2xl ${lnk.color}`}>{lnk.icon}</span>
              <span className="text-xs font-display font-semibold text-navy leading-tight">{lnk.label}</span>
            </Link>
          ))}
        </div>

      </div>
    </div>
  )
}
