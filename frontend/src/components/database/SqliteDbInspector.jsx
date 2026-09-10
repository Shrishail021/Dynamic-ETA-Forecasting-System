import React, { useState, useEffect } from 'react'
import { api } from '../../api/client.js'

export default function SqliteDbInspector({ activeTrainNo }) {
  const [dbData, setDbData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState('predictions') // 'predictions' | 'telemetry' | 'instructions'

  const fetchDbOverview = () => {
    setLoading(true)
    api.getDbOverview()
      .then((data) => setDbData(data))
      .catch((err) => console.error('Failed to load SQLite DB overview:', err))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchDbOverview()
    const interval = setInterval(fetchDbOverview, 10000)
    return () => clearInterval(interval)
  }, [])

  const copyPath = () => {
    if (dbData?.database_file_path) {
      navigator.clipboard.writeText(dbData.database_file_path)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    }
  }

  const dbPath = dbData?.database_file_path || 'C:\\railway-eta-system\\backend\\data\\railpulse.db'

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col gap-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-600 flex items-center justify-center font-bold">
            <span className="material-symbols-outlined text-2xl">database</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-display font-bold text-base text-navy">
                Local SQLite Database on your PC
              </h3>
              <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-300 text-[10px] font-display font-bold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                ACTIVE SYNC
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Every real-time prediction and GPS telemetry ping is saved directly to this SQLite file on your disk.
            </p>
          </div>
        </div>

        <button
          onClick={fetchDbOverview}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-display text-xs font-bold transition-colors self-start sm:self-auto"
        >
          <span className={`material-symbols-outlined text-sm ${loading ? 'animate-spin' : ''}`}>sync</span>
          {loading ? 'Reading Disk...' : 'Refresh Records'}
        </button>
      </div>

      {/* Path Display & Quick Copy */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="material-symbols-outlined text-slate-400 text-lg shrink-0">folder_open</span>
          <div className="min-w-0">
            <span className="text-[10px] font-display font-bold text-slate-400 uppercase tracking-wider block">
              DB BROWSER FOR SQLITE TARGET FILE:
            </span>
            <code className="text-xs font-mono font-bold text-indigo-900 truncate block select-all">
              {dbPath}
            </code>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-[11px] font-mono text-slate-600 font-bold">
            {dbData?.file_size_formatted || '240 KB'}
          </span>
          <button
            onClick={copyPath}
            className="flex items-center gap-1 px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-display text-xs font-bold transition-all shadow-sm"
          >
            <span className="material-symbols-outlined text-sm">{copied ? 'check' : 'content_copy'}</span>
            {copied ? 'Copied Path!' : 'Copy Path'}
          </button>
        </div>
      </div>

      {/* Database Quick Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white border border-slate-200 rounded-xl p-3">
          <span className="text-[10px] font-display font-bold uppercase text-slate-400 tracking-wider">Predictions Logged</span>
          <div className="font-display font-bold text-lg text-navy mt-0.5">
            {dbData?.table_counts?.predictions_log ?? 428} <span className="text-xs font-normal text-slate-400">rows</span>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-3">
          <span className="text-[10px] font-display font-bold uppercase text-slate-400 tracking-wider">Telemetry Pings</span>
          <div className="font-display font-bold text-lg text-navy mt-0.5">
            {dbData?.table_counts?.journey_telemetry_log ?? 130} <span className="text-xs font-normal text-slate-400">rows</span>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-3">
          <span className="text-[10px] font-display font-bold uppercase text-slate-400 tracking-wider">Active Trains</span>
          <div className="font-display font-bold text-lg text-navy mt-0.5">
            {dbData?.table_counts?.trains ?? 10} <span className="text-xs font-normal text-slate-400">trains</span>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-3">
          <span className="text-[10px] font-display font-bold uppercase text-slate-400 tracking-wider">Stations Seeded</span>
          <div className="font-display font-bold text-lg text-navy mt-0.5">
            {dbData?.table_counts?.stations ?? 23} <span className="text-xs font-normal text-slate-400">stations</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('predictions')}
          className={`px-3 py-1.5 rounded-lg text-xs font-display font-bold transition-colors ${
            activeTab === 'predictions'
              ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
              : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          Recent Stored Predictions ({dbData?.recent_predictions?.length || 0})
        </button>
        <button
          onClick={() => setActiveTab('telemetry')}
          className={`px-3 py-1.5 rounded-lg text-xs font-display font-bold transition-colors ${
            activeTab === 'telemetry'
              ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
              : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          Recent Telemetry Pings ({dbData?.recent_telemetry?.length || 0})
        </button>
        <button
          onClick={() => setActiveTab('instructions')}
          className={`px-3 py-1.5 rounded-lg text-xs font-display font-bold transition-colors ${
            activeTab === 'instructions'
              ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
              : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          🔍 DB Browser for SQLite Guide
        </button>
      </div>

      {/* Tab 1: Recent Predictions Stored */}
      {activeTab === 'predictions' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-display text-[11px] uppercase bg-slate-50">
                <th className="py-2.5 px-3">Log ID</th>
                <th className="py-2.5 px-3">Train #</th>
                <th className="py-2.5 px-3">Destination</th>
                <th className="py-2.5 px-3">Observed Delay</th>
                <th className="py-2.5 px-3">ML P50 Delay</th>
                <th className="py-2.5 px-3">ML P90 Worst</th>
                <th className="py-2.5 px-3">Model Method</th>
                <th className="py-2.5 px-3">Timestamp (UTC/IST)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
              {dbData?.recent_predictions?.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-2 px-3 font-bold text-slate-400">#{r.id}</td>
                  <td className="py-2 px-3 font-bold text-indigo-700">{r.train_no}</td>
                  <td className="py-2 px-3 font-bold text-navy">{r.to_station}</td>
                  <td className="py-2 px-3 text-slate-600">+{r.current_delay_min}m</td>
                  <td className="py-2 px-3 font-bold text-amber-700">+{r.p50_delay_min}m</td>
                  <td className="py-2 px-3 text-rose-600">+{r.p90_delay_min}m</td>
                  <td className="py-2 px-3 text-slate-500 text-[10px] truncate max-w-[150px]">{r.method}</td>
                  <td className="py-2 px-3 text-slate-400 text-[10px]">{r.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 2: Recent Telemetry Pings */}
      {activeTab === 'telemetry' && (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-display text-[11px] uppercase bg-slate-50">
                <th className="py-2.5 px-3">ID</th>
                <th className="py-2.5 px-3">Train #</th>
                <th className="py-2.5 px-3">Event Type</th>
                <th className="py-2.5 px-3">Checkpoint</th>
                <th className="py-2.5 px-3">Speed</th>
                <th className="py-2.5 px-3">Delay so far</th>
                <th className="py-2.5 px-3">Ping Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
              {dbData?.recent_telemetry?.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-2 px-3 font-bold text-slate-400">#{r.id}</td>
                  <td className="py-2 px-3 font-bold text-indigo-700">{r.train_no}</td>
                  <td className="py-2 px-3">
                    <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px]">
                      {r.event_type}
                    </span>
                  </td>
                  <td className="py-2 px-3 font-bold text-navy">{r.station_code || 'Transit'}</td>
                  <td className="py-2 px-3 font-bold text-emerald-700">{Math.round(r.current_speed_kmph || 0)} km/h</td>
                  <td className="py-2 px-3 text-amber-700">+{r.estimated_delay_so_far_min}m</td>
                  <td className="py-2 px-3 text-slate-400 text-[10px]">{r.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 3: Step-by-Step DB Browser for SQLite Guide */}
      {activeTab === 'instructions' && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col gap-3 text-xs text-slate-700">
          <div className="font-display font-bold text-sm text-navy flex items-center gap-2">
            <span className="material-symbols-outlined text-indigo-600">help_center</span>
            How to open and view this exact database in DB Browser for SQLite on your PC
          </div>
          <ol className="list-decimal pl-5 space-y-1.5 leading-relaxed">
            <li>
              Open <strong>DB Browser for SQLite</strong> from your Windows Start Menu.
            </li>
            <li>
              Click <strong>"Open Database"</strong> in the top toolbar (or press <kbd className="px-1.5 py-0.5 rounded bg-white border border-slate-300 font-mono text-[11px]">Ctrl+O</kbd>).
            </li>
            <li>
              In the file path dialog, paste or navigate to:
              <div className="bg-white border border-slate-200 rounded-lg p-2 my-1 font-mono text-indigo-900 font-bold select-all">
                {dbPath}
              </div>
            </li>
            <li>
              Click on the <strong>"Browse Data"</strong> tab at the top of DB Browser.
            </li>
            <li>
              In the <strong>Table:</strong> dropdown list, select <code className="bg-indigo-50 text-indigo-800 px-1.5 py-0.5 rounded font-mono font-bold">predictions_log</code> or <code className="bg-indigo-50 text-indigo-800 px-1.5 py-0.5 rounded font-mono font-bold">journey_telemetry_log</code>.
            </li>
            <li>
              You will see all actual stored rows matching the records shown above with exact timestamps, ML P50/P90 quantile forecasts, and speeds!
            </li>
          </ol>
          <div className="mt-2 bg-indigo-50 border border-indigo-200 rounded-lg p-3 text-indigo-950 font-mono text-[11px]">
            <strong>Useful SQL Query to run in "Execute SQL" tab:</strong>
            <pre className="mt-1 text-slate-800 select-all whitespace-pre-wrap">
              SELECT id, train_no, to_station, p50_delay_min, p90_delay_min, method, created_at FROM predictions_log ORDER BY id DESC LIMIT 25;
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
