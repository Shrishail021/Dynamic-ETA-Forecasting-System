import React, { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client.js'

export default function TrainSearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [trains, setTrains] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const initialSearch = searchParams.get('search') || ''
  const initialRoute = searchParams.get('route') || ''
  const initialType = searchParams.get('type') || ''

  const [search, setSearch] = useState(initialSearch)
  const [routeFilter, setRouteFilter] = useState(initialRoute)
  const [typeFilter, setTypeFilter] = useState(initialType)

  // GPS Geolocation state
  const [gpsLoading, setGpsLoading] = useState(false)
  const [gpsStation, setGpsStation] = useState(null)
  const [gpsError, setGpsError] = useState(null)

  const handleGpsSearch = (lat, lon, cityName = '') => {
    setGpsLoading(true)
    setGpsError(null)
    api.getNearbyTrains(lat, lon)
      .then((res) => {
        setGpsStation(res)
        if (res.passing_trains) {
          setTrains(res.passing_trains)
        }
      })
      .catch((err) => {
        setGpsError(`Could not find nearest station for ${cityName || 'GPS'}: ${err.message}`)
      })
      .finally(() => setGpsLoading(false))
  }

  const handleUseBrowserGps = () => {
    if (!navigator.geolocation) {
      setGpsError('Geolocation is not supported by your browser.')
      return
    }
    setGpsLoading(true)
    setGpsError(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        handleGpsSearch(pos.coords.latitude, pos.coords.longitude)
      },
      (err) => {
        setGpsLoading(false)
        setGpsError(err.code === 1 ? 'Location permission denied. Use test cities below.' : err.message)
      },
      { timeout: 10000, enableHighAccuracy: true }
    )
  }

  useEffect(() => {
    setLoading(true)
    const params = {}
    if (routeFilter) params.route_id = routeFilter
    if (typeFilter) params.train_type = typeFilter
    if (search) params.search = search

    api.listTrains(params)
      .then((data) => {
        setTrains(data)
        setError(null)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [routeFilter, typeFilter, search])

  const handleClearFilters = () => {
    setSearch('')
    setRouteFilter('')
    setTypeFilter('')
    setSearchParams({})
  }

  const getTypeBadge = (type) => {
    switch (type) {
      case 'rajdhani_shatabdi_vb':
        return { label: 'Premier', bg: 'bg-primary/20 text-primary border-primary/30' }
      case 'superfast':
        return { label: 'Superfast', bg: 'bg-secondary/20 text-secondary border-secondary/30' }
      case 'express':
        return { label: 'Express', bg: 'bg-surface-container-highest text-on-surface-variant border-outline-variant/40' }
      case 'passenger':
        return { label: 'Passenger', bg: 'bg-outline/20 text-outline border-outline/30' }
      default:
        return { label: type, bg: 'bg-surface-variant text-on-surface' }
    }
  }

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 py-8 flex flex-col gap-6">
      
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-outline-variant pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-2xl">grid_view</span>
            <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-navy">
              Coaching Train Radar
            </h1>
          </div>
          <p className="text-sm text-on-surface-variant mt-1">
            Browse and track scheduled trains across key Northern and Southern transit corridors.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-display font-semibold text-outline uppercase tracking-wider">
            Total Results:
          </span>
          <span className="px-2.5 py-1 rounded-full bg-surface-container-high border border-primary/30 font-display font-bold text-xs text-primary">
            {trains.length} Trains
          </span>
        </div>
      </div>

      {/* Filter and Search Controls */}
      <div className="bg-white p-4 rounded-xl border border-outline-variant shadow-card flex flex-col md:flex-row items-center gap-3">
        {/* Search input */}
        <div className="relative flex-1 w-full">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[18px]">
            search
          </span>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search train no. or name..."
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-container-low border border-outline-variant text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary tracking-wide transition-colors"
          />
        </div>

        {/* Route Filter Dropdown */}
        <div className="w-full md:w-56">
          <select
            value={routeFilter}
            onChange={(e) => setRouteFilter(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-surface-container-low border border-outline-variant text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
          >
            <option value="">All Corridors / Routes</option>
            <option value="R1">R1 — NDLS to BCT (Delhi - Mumbai)</option>
            <option value="R2">R2 — NDLS to ASR (Delhi - Amritsar)</option>
            <option value="R3">R3 — SBC to MAS (Bengaluru - Chennai)</option>
            <option value="R4">R4 — HWH to NDLS (Howrah - Delhi)</option>
            <option value="R5">R5 — MYS to SBC (Mysuru - Bengaluru)</option>
          </select>
        </div>

        {/* Train Type Filter */}
        <div className="w-full md:w-52">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-surface-container-low border border-outline-variant text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
          >
            <option value="">All Train Types</option>
            <option value="rajdhani_shatabdi_vb">Premier (Rajdhani / Shatabdi)</option>
            <option value="superfast">Superfast Express</option>
            <option value="express">Mail / Express</option>
            <option value="passenger">Passenger Local</option>
          </select>
        </div>

        {/* Clear Filters Button */}
        {(search || routeFilter || typeFilter || gpsStation) && (
          <button
            onClick={() => {
              handleClearFilters()
              setGpsStation(null)
            }}
            className="px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-on-surface-variant hover:text-on-surface transition-colors shrink-0 border border-outline-variant"
          >
            Clear All
          </button>
        )}
      </div>

      {/* GPS Location Finder Bar */}
      <div className="bg-white p-4 rounded-xl border border-outline-variant shadow-card flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-lg">near_me</span>
          <span className="text-xs font-display font-semibold text-navy">Browse Station by Location:</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleUseBrowserGps}
            disabled={gpsLoading}
            className="px-3 py-1.5 rounded-lg bg-primary hover:bg-navy text-white font-display text-xs font-bold flex items-center gap-1.5 transition-all shadow-md disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-sm">
              {gpsLoading ? 'progress_activity' : 'my_location'}
            </span>
            <span>{gpsLoading ? 'Locating...' : 'Use My GPS'}</span>
          </button>
          <span className="text-[11px] text-outline">or test preset:</span>
          <button
            type="button"
            onClick={() => handleGpsSearch(28.6431, 77.2197, 'Delhi')}
            className="px-2.5 py-1 rounded border border-outline-variant bg-surface-container-low hover:bg-surface-container-high text-xs text-on-surface-variant hover:text-primary transition-colors"
          >
            Delhi (NDLS)
          </button>
          <button
            type="button"
            onClick={() => handleGpsSearch(18.9696, 72.8193, 'Mumbai')}
            className="px-2.5 py-1 rounded border border-outline-variant bg-surface-container-low hover:bg-surface-container-high text-xs text-on-surface-variant hover:text-primary transition-colors"
          >
            Mumbai (BCT)
          </button>
          <button
            type="button"
            onClick={() => handleGpsSearch(12.9781, 77.5696, 'Bengaluru')}
            className="px-2.5 py-1 rounded border border-outline-variant bg-surface-container-low hover:bg-surface-container-high text-xs text-on-surface-variant hover:text-primary transition-colors"
          >
            Bengaluru (SBC)
          </button>
        </div>
      </div>

      {gpsError && (
        <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center justify-between">
          <span>{gpsError}</span>
          <button onClick={() => setGpsError(null)} className="text-xs font-bold ml-2 hover:text-red-900">✕ Dismiss</button>
        </div>
      )}

      {gpsStation && (
        <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-fadeIn">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-lg bg-primary text-white font-display font-bold text-sm">
                {gpsStation.nearest_station.station_code}
              </span>
              <span className="font-display font-bold text-base text-navy">
                {gpsStation.nearest_station.station_name}
              </span>
              <span className="text-xs text-primary font-semibold bg-blue-100 px-2 py-0.5 rounded-full border border-blue-200">
                ~{gpsStation.distance_km} km
              </span>
            </div>
            <p className="text-xs text-on-surface-variant mt-1">
              Showing <span className="font-bold text-navy">{gpsStation.total_trains} trains</span> with stops at this station.
            </p>
          </div>
          <button
            onClick={() => { setGpsStation(null); handleClearFilters() }}
            className="px-3 py-1.5 rounded-lg bg-white border border-outline-variant text-xs text-on-surface hover:text-primary transition-colors shrink-0 font-semibold"
          >
            Reset to All Trains
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Train Cards Grid */}
      {loading ? (
        <div className="py-16 text-center text-on-surface-variant flex flex-col items-center gap-3">
          <span className="material-symbols-outlined text-3xl animate-spin text-primary">progress_activity</span>
          <span className="text-sm">Scanning corridor telemetry...</span>
        </div>
      ) : trains.length === 0 ? (
        <div className="bg-white p-12 rounded-2xl border border-outline-variant text-center flex flex-col items-center justify-center gap-3 shadow-card">
          <span className="material-symbols-outlined text-4xl text-outline">search_off</span>
          <h3 className="font-display font-bold text-lg text-navy">No Trains Match Filter</h3>
          <p className="text-xs text-on-surface-variant max-w-sm">
            Try adjusting your search query, route selection, or clear filters to view available coaching trains.
          </p>
          <button
            onClick={handleClearFilters}
            className="mt-2 px-4 py-2 rounded-lg bg-primary text-white font-display text-xs font-bold shadow-md hover:bg-navy transition-colors"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {trains.map((train) => {
            const badge = getTypeBadge(train.train_type)
            return (
              <Link
                key={train.train_no}
                to={`/trains/${train.train_no}`}
                className="group bg-white border border-outline-variant rounded-2xl p-5 shadow-card card-hover transition-all duration-200 flex flex-col justify-between"
              >
                <div>
                  {/* Top Bar: Train No + Type Badge */}
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-display font-bold text-lg text-primary tracking-tight">
                        {train.train_no}
                      </span>
                      <span className={`text-[10px] uppercase font-display font-bold px-2.5 py-0.5 rounded-full border ${badge.bg}`}>
                        {badge.label}
                      </span>
                    </div>

                    {/* Live Indicator */}
                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-green-50 border border-green-200 text-[10px] font-display font-bold text-green-700">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                      ACTIVE
                    </div>
                  </div>

                  {/* Train Title */}
                  <h2 className="font-semibold text-base text-navy leading-snug">
                    {train.train_name}
                  </h2>

                  {/* Route & Timetable Info */}
                  <div className="mt-3 flex items-center justify-between text-xs text-on-surface-variant bg-surface-container-low p-2.5 rounded-xl border border-outline-variant">
                    <div>
                      <span className="text-[10px] uppercase text-outline font-semibold block">Corridor</span>
                      <span className="font-display font-bold text-navy">{train.route_id}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase text-outline font-semibold block">Departure</span>
                      <span className="font-display font-bold text-navy">{train.origin_departure_time}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase text-outline font-semibold block">Priority</span>
                      <span className="font-display font-bold text-secondary">Tier {train.priority}</span>
                    </div>
                  </div>
                </div>

                {/* Footer Action */}
                <div className="flex items-center justify-between text-xs pt-4 mt-3 border-t border-outline-variant">
                  <span className="text-[11px] text-on-surface-variant">Runs: Daily</span>
                  <span className="flex items-center gap-1 text-primary font-display font-semibold group-hover:translate-x-1 transition-transform">
                    View Live ETA <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
                  </span>
                </div>
              </Link>
            )
          })}
        </div>
      )}

    </div>
  )
}
