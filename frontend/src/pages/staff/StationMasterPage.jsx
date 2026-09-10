import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client.js'
import DelayCauseAlert from '../../components/trains/DelayCauseAlert.jsx'
import { formatClockTime, formatDelayHuman } from '../../utils/timeUtils.js'

export default function StationMasterPage() {
  const [selectedStation, setSelectedStation] = useState('AGC')
  const [stationsList, setStationsList] = useState([])
  const [stationData, setStationData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [simulatedSilence, setSimulatedSilence] = useState(false)
  const [platformOverrides, setPlatformOverrides] = useState({})

  // Load available stations
  useEffect(() => {
    api.getStationMasterStations()
      .then((data) => {
        setStationsList(data || [])
      })
      .catch((err) => console.error('Failed to load stations:', err))
  }, [])

  // Load station master overview for selected station
  const fetchStationOverview = (code) => {
    setLoading(true)
    api.getStationMasterOverview(code)
      .then((res) => {
        setStationData(res)
        setError(null)
      })
      .catch((err) => {
        setError(err.message)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchStationOverview(selectedStation)
    const timer = setInterval(() => fetchStationOverview(selectedStation), 12000)
    return () => clearInterval(timer)
  }, [selectedStation])

  const handlePlatformChange = (trainNo, newPf) => {
    setPlatformOverrides((prev) => ({ ...prev, [trainNo]: newPf }))
  }

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 py-8 flex flex-col gap-6">

      {/* Station Master Header */}
      <div className="bg-white border border-outline-variant rounded-2xl p-6 shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center font-bold">
            <span className="material-symbols-outlined text-3xl">meeting_room</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-display font-bold uppercase tracking-wider text-primary">
                Station Master Operating Panel
              </span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 font-display text-[10px] font-bold">
                LIVE INTERLOCKING
              </span>
            </div>
            <h1 className="font-display text-2xl sm:text-3xl font-bold text-navy mt-0.5">
              {stationData?.station_name || selectedStation} Junction ({selectedStation})
            </h1>
            <p className="text-xs text-on-surface-variant mt-0.5">
              Live train attribute monitoring, approach ETAs, platform assignment & environmental hazard advisories.
            </p>
          </div>
        </div>

        {/* Station Selector Dropdown */}
        <div className="flex items-center gap-3">
          <div className="flex flex-col">
            <label className="text-[10px] uppercase font-bold text-slate-500 mb-1">Select Station Post</label>
            <select
              value={selectedStation}
              onChange={(e) => setSelectedStation(e.target.value)}
              className="px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant text-navy font-display font-bold text-sm focus:outline-none focus:border-primary shadow-xs"
            >
              {stationsList.length > 0 ? (
                stationsList.map((s) => (
                  <option key={s.station_code} value={s.station_code}>
                    {s.station_name} ({s.station_code})
                  </option>
                ))
              ) : (
                <>
                  <option value="AGC">Agra Cantt (AGC)</option>
                  <option value="NDLS">New Delhi (NDLS)</option>
                  <option value="JHS">Jhansi Jn (JHS)</option>
                  <option value="BPL">Bhopal Jn (BPL)</option>
                  <option value="BAU">Bhusaval Jn (BAU)</option>
                  <option value="BCT">Mumbai Central (BCT)</option>
                </>
              )}
            </select>
          </div>

          <button
            onClick={() => fetchStationOverview(selectedStation)}
            className="p-2.5 rounded-xl border border-outline-variant hover:bg-slate-50 text-navy mt-5 self-end"
            title="Refresh Incoming Trains"
          >
            <span className="material-symbols-outlined text-lg">refresh</span>
          </button>
        </div>
      </div>

      {/* Fog & Weather Hazard Alert for the Station Section */}
      {stationData?.fog_alert_active && (
        <div className="bg-amber-50 border-2 border-amber-300 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm animate-fadeIn">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-200/80 text-amber-900 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-2xl">foggy</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display font-bold text-sm text-amber-950">
                  Dense Fog Advisory Active in {selectedStation} Division
                </span>
                <span className="px-2 py-0.5 rounded-full bg-amber-200 text-amber-900 border border-amber-400 font-display text-[10px] font-bold">
                  CRS RULE 3.61
                </span>
              </div>
              <p className="text-xs text-amber-900/90 mt-0.5">
                Visibility below 200m in approaching sections. Maximum line speed capped at <strong>60 km/h</strong>. Audio Fog-Pass signals active at outer caution boards.
              </p>
            </div>
          </div>
          <div className="text-xs text-amber-900 font-display font-bold bg-white/80 border border-amber-300 px-3 py-1.5 rounded-xl self-start sm:self-auto shrink-0">
            Speed Cap: 60 km/h (Normal 130 km/h)
          </div>
        </div>
      )}

      {/* Autonomous Broadcast Demo Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="material-symbols-outlined text-primary text-xl">satellite_alt</span>
          <div>
            <div className="font-display font-bold text-sm text-navy">
              Autonomous Dead-Reckoning Broadcast Enabled
            </div>
            <p className="text-xs text-slate-600 mt-0.5">
              If an intermediate train master fails to log a checkpoint, RailPulse automatically extrapolates physical train position and broadcasts continuous ETAs to this station monitor.
            </p>
          </div>
        </div>
        <Link
          to={`/trains/12951`}
          className="text-xs font-display font-bold text-primary hover:underline flex items-center gap-1 shrink-0"
        >
          View Train 12951 Telemetry <span className="material-symbols-outlined text-sm">arrow_forward</span>
        </Link>
      </div>

      {/* Approaching Trains List with Full Attributes */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-lg">departure_board</span>
            <h2 className="font-display font-semibold text-sm uppercase tracking-wider text-navy">
              Incoming Approaching Trains ({stationData?.trains?.length || 0})
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            Auto-refreshing every 12s
          </span>
        </div>

        {loading ? (
          <div className="py-20 text-center text-slate-500 flex flex-col items-center gap-2">
            <span className="material-symbols-outlined text-3xl animate-spin text-primary">progress_activity</span>
            <span className="text-xs font-display font-bold">Scanning Section Signal Blocks...</span>
          </div>
        ) : stationData?.trains?.length === 0 ? (
          <div className="bg-white border border-outline-variant rounded-2xl p-12 text-center text-slate-500">
            <span className="material-symbols-outlined text-4xl text-slate-300 mb-2">train</span>
            <p className="font-display font-bold text-sm text-navy">No Trains Approaching</p>
            <p className="text-xs mt-1">No scheduled arrivals found for {selectedStation} in the active timetable.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {stationData.trains.map((train) => {
              const pf = platformOverrides[train.train_no] || train.assigned_platform
              const isAutonomous = train.telemetry_source === 'AUTONOMOUS_DEAD_RECKONING'
              const delayCause = train.delay_cause || {}

              return (
                <div
                  key={train.train_no}
                  className="bg-white border border-outline-variant rounded-2xl p-6 shadow-card hover:shadow-md transition-all flex flex-col gap-4"
                >
                  {/* Top Train Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-navy text-white flex items-center justify-center font-display font-bold text-sm">
                        {train.train_no}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-display font-bold text-base text-navy">
                            {train.train_name}
                          </h3>
                          <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-800 border border-blue-200 text-[10px] font-display font-bold uppercase">
                            {train.train_type?.replace('_', ' ')}
                          </span>
                          <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[10px] font-bold">
                            Tier {train.priority} Priority
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
                          <span>Departs Origin: <strong>{train.origin_departure_time}</strong></span>
                          <span>•</span>
                          <span>Last Known Location: <strong className="text-navy">{train.current_location?.station_name}</strong></span>
                        </div>
                      </div>
                    </div>

                    {/* Telemetry Status Badge */}
                    <div className="flex items-center gap-2 self-start sm:self-auto">
                      {isAutonomous ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300 text-xs font-display font-bold">
                          <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
                          ⚡ AUTONOMOUS BROADCAST (Master Missed Checkpoint)
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 text-xs font-display font-bold">
                          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                          🟢 Station Master Confirmed Telemetry
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Core Attribute Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs bg-surface-container-low p-4 rounded-xl border border-outline-variant/60">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-500 block">Rake Specification</span>
                      <span className="font-display font-bold text-navy block mt-0.5">
                        {train.attributes?.rake_type}
                      </span>
                      <span className="text-[11px] text-slate-500">
                        {train.attributes?.coaches_count} Coaches • {train.attributes?.rake_length_meters}m Length
                      </span>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-500 block">Traction & Power</span>
                      <span className="font-display font-bold text-navy block mt-0.5">
                        {train.attributes?.traction_type}
                      </span>
                      <span className="text-[11px] text-slate-500">
                        Twin-Pipe Disc Braking
                      </span>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-500 block">Speed & Distance</span>
                      <div className="flex items-baseline gap-1 mt-0.5">
                        <span className="font-display font-bold text-base text-primary">
                          {train.current_location?.current_speed_kmph}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          / {train.current_location?.permissible_speed_kmph} km/h
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-500">
                        <strong>{train.current_location?.distance_to_station_km} km</strong> away
                      </span>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-500 block">Assigned Platform</span>
                      <div className="flex items-center gap-2 mt-1">
                        <select
                          value={pf}
                          onChange={(e) => handlePlatformChange(train.train_no, e.target.value)}
                          className="px-2.5 py-1 rounded-lg bg-white border border-outline-variant font-display font-bold text-navy text-xs focus:outline-none focus:border-primary"
                        >
                          <option value="PF-1">Platform 1</option>
                          <option value="PF-2">Platform 2</option>
                          <option value="PF-3">Platform 3</option>
                          <option value="PF-4">Platform 4</option>
                          <option value="Main Line 1">Main Line 1</option>
                        </select>
                        <span className="text-[10px] text-emerald-700 font-bold">● Routed</span>
                      </div>
                    </div>
                  </div>

                  {/* Approach ETA & Delay Cause Breakdown */}
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pt-1">
                    {/* Expected Arrival Clock & P90 Band */}
                    <div className="flex items-center gap-6">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-500 block">Scheduled Time</span>
                        <span className="font-display font-bold text-lg text-slate-700 tabular-nums">
                          {train.scheduled_arrival_time}
                        </span>
                      </div>

                      <div className="border-l border-slate-200 pl-6">
                        <span className="text-[10px] uppercase font-bold text-primary block">Expected Live ETA (ML)</span>
                        <div className="flex items-baseline gap-2">
                          <span className="font-display font-bold text-2xl text-navy tabular-nums">
                            {train.expected_live_eta}
                          </span>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-display font-bold ${
                            train.p50_delay_min > 20 ? 'bg-amber-100 text-amber-900' : 'bg-blue-50 text-blue-800'
                          }`}>
                            {formatDelayHuman(train.p50_delay_min)}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-400">
                          P90 Risk Ceiling: +{train.p90_delay_min}m
                        </span>
                      </div>
                    </div>

                    {/* Delay Cause Alert Snippet */}
                    {delayCause.title && (
                      <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 max-w-md">
                        <span className="material-symbols-outlined text-amber-700 text-xl shrink-0">
                          {delayCause.icon || 'foggy'}
                        </span>
                        <div>
                          <div className="font-display font-bold text-xs">{delayCause.title}</div>
                          <div className="text-[11px] text-amber-800/80 leading-tight mt-0.5">
                            {delayCause.safety_regulation || delayCause.detailed_explanation}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Navigation Link */}
                    <Link
                      to={`/trains/${train.train_no}`}
                      className="px-3.5 py-2 rounded-xl bg-navy hover:bg-navy-dark text-white font-display font-semibold text-xs transition-colors shrink-0 text-center flex items-center justify-center gap-1"
                    >
                      <span>Full Telemetry</span>
                      <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

    </div>
  )
}
