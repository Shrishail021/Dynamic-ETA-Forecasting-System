import React, { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext.jsx'
import { api } from '../../api/client.js'

export default function TrainMasterPage() {
  const { token, role } = useAuth()
  const [trains, setTrains] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingTrainNo, setEditingTrainNo] = useState(null)
  const [form, setForm] = useState({
    train_no: '',
    train_name: '',
    route_id: 'R1',
    train_type: 'express',
    priority: 3,
    recovery_fraction: 0.06,
    days_of_week: [0, 1, 2, 3, 4, 5, 6],
    origin_departure_time: '10:00',
  })

  const loadTrains = () => {
    setLoading(true)
    api.adminListTrains(token)
      .then((data) => {
        setTrains(data)
        setError(null)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (token) loadTrains()
  }, [token])

  if (!token) {
    return (
      <div className="py-24 text-center">
        <p className="text-on-surface-variant mb-3">Authentication required to access Train Master.</p>
        <a href="/admin/login" className="px-4 py-2 rounded-lg bg-primary-container text-black font-display font-bold text-xs">
          Log In as Admin
        </a>
      </div>
    )
  }

  if (role !== 'admin') {
    return (
      <div className="py-24 text-center">
        <p className="text-hazard-coral font-bold mb-1">Access Restricted</p>
        <p className="text-on-surface-variant text-sm">Train Master requires administrator privileges.</p>
      </div>
    )
  }

  const openAddModal = () => {
    setEditingTrainNo(null)
    setForm({
      train_no: '',
      train_name: '',
      route_id: 'R1',
      train_type: 'express',
      priority: 3,
      recovery_fraction: 0.06,
      days_of_week: [0, 1, 2, 3, 4, 5, 6],
      origin_departure_time: '10:00',
    })
    setIsModalOpen(true)
  }

  const openEditModal = (t) => {
    setEditingTrainNo(t.train_no)
    setForm({
      train_no: t.train_no,
      train_name: t.train_name,
      route_id: t.route_id,
      train_type: t.train_type,
      priority: t.priority,
      recovery_fraction: t.recovery_fraction,
      days_of_week: t.days_of_week || [0, 1, 2, 3, 4, 5, 6],
      origin_departure_time: t.origin_departure_time,
    })
    setIsModalOpen(true)
  }

  const handleDelete = async (trainNo) => {
    if (!window.confirm(`Are you sure you want to delete train ${trainNo} and its schedules?`)) return
    try {
      await api.adminDeleteTrain(token, trainNo)
      setSuccessMsg(`Train ${trainNo} deleted successfully.`)
      setTimeout(() => setSuccessMsg(null), 4000)
      loadTrains()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      if (editingTrainNo) {
        await api.adminUpdateTrain(token, editingTrainNo, form)
        setSuccessMsg(`Train ${editingTrainNo} updated successfully in SQLite database.`)
      } else {
        await api.adminCreateTrain(token, form)
        setSuccessMsg(`Train ${form.train_no} created and schedule auto-generated in SQLite database.`)
      }
      setIsModalOpen(false)
      setTimeout(() => setSuccessMsg(null), 4000)
      loadTrains()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 py-8 flex flex-col gap-6">
      
      {/* Information Banner */}
      <div className="p-4 rounded-xl bg-primary-container/10 border border-primary/30 flex items-start gap-3">
        <span className="material-symbols-outlined text-primary text-2xl shrink-0 mt-0.5">database</span>
        <div>
          <h2 className="font-display font-bold text-sm text-primary uppercase tracking-wide">
            Persistent Train Master Database (SQLite)
          </h2>
          <p className="text-xs text-on-surface-variant mt-0.5">
            All additions, timetable edits, and deletions persist across server restarts. Adding a new train
            automatically derives its station schedule and running times along the chosen route corridor.
          </p>
        </div>
      </div>

      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-on-surface">
            Train Master Directory
          </h1>
          <p className="text-xs text-on-surface-variant mt-1">
            Manage rolling stock rosters, corridor assignments, and timetable recovery buffers.
          </p>
        </div>

        <button
          onClick={openAddModal}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary-container hover:bg-primary text-black font-display font-bold text-xs tracking-wide transition-all shadow-[0_0_15px_rgba(51,194,255,0.35)] shrink-0"
        >
          <span className="material-symbols-outlined text-lg">add_circle</span>
          Register New Train
        </button>
      </div>

      {/* Status Alerts */}
      {successMsg && (
        <div className="p-3 rounded-xl bg-primary-container/20 border border-primary/40 text-primary text-xs flex items-center gap-2">
          <span className="material-symbols-outlined text-base">check_circle</span>
          <span>{successMsg}</span>
        </div>
      )}
      {error && (
        <div className="p-3 rounded-xl bg-hazard-coral/20 border border-hazard-coral/40 text-hazard-coral text-xs flex items-center gap-2">
          <span className="material-symbols-outlined text-base">error</span>
          <span>{error}</span>
        </div>
      )}

      {/* Trains Data Table */}
      <div className="glass-panel rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs sm:text-sm">
            <thead>
              <tr className="border-b border-outline-variant/30 text-on-surface-variant text-[11px] font-display uppercase tracking-wider bg-surface-container-low/80">
                <th className="py-3 px-4">Train No</th>
                <th className="py-3 px-4">Train Name</th>
                <th className="py-3 px-4">Route</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Dep. Time</th>
                <th className="py-3 px-4">Recovery %</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/20">
              {loading ? (
                <tr>
                  <td colSpan="8" className="py-12 text-center text-on-surface-variant">
                    <span className="material-symbols-outlined animate-spin text-2xl text-primary mb-2">progress_activity</span>
                    <p>Loading master database records...</p>
                  </td>
                </tr>
              ) : trains.map((t) => (
                <tr key={t.train_no} className="hover:bg-surface-container-high/40 transition-colors">
                  <td className="py-3 px-4 font-display font-bold text-primary">
                    {t.train_no}
                  </td>
                  <td className="py-3 px-4 font-semibold text-on-surface">
                    {t.train_name}
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-surface-container-highest font-display text-xs font-bold text-on-surface">
                      {t.route_id}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-on-surface-variant text-xs capitalize">
                    {t.train_type.replace('_', ' ')}
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-display font-bold text-secondary">
                      Tier {t.priority}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-display tabular-nums text-on-surface">
                    {t.origin_departure_time}
                  </td>
                  <td className="py-3 px-4 font-display tabular-nums text-on-surface-variant">
                    {Math.round(t.recovery_fraction * 100)}%
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => openEditModal(t)}
                        className="p-1.5 rounded-lg hover:bg-surface-container-high text-on-surface-variant hover:text-primary transition-colors"
                        title="Edit train"
                      >
                        <span className="material-symbols-outlined text-[18px]">edit</span>
                      </button>
                      <button
                        onClick={() => handleDelete(t.train_no)}
                        className="p-1.5 rounded-lg hover:bg-surface-container-high text-on-surface-variant hover:text-hazard-coral transition-colors"
                        title="Delete train"
                      >
                        <span className="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add / Edit Train Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-lg glass-panel-elevated p-6 rounded-2xl flex flex-col gap-5 relative animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-outline-variant/30 pb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-xl">
                  {editingTrainNo ? 'edit_note' : 'add_circle'}
                </span>
                <h3 className="font-display font-bold text-lg text-on-surface">
                  {editingTrainNo ? `Edit Train ${editingTrainNo}` : 'Register New Train'}
                </h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 rounded-lg hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface"
              >
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-outline uppercase font-semibold">Train Number</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingTrainNo}
                    value={form.train_no}
                    onChange={(e) => setForm({ ...form, train_no: e.target.value })}
                    placeholder="e.g. 22436"
                    className="p-2 rounded-lg bg-surface-container-lowest border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary disabled:opacity-50"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-outline uppercase font-semibold">Origin Departure Time</label>
                  <input
                    type="text"
                    required
                    value={form.origin_departure_time}
                    onChange={(e) => setForm({ ...form, origin_departure_time: e.target.value })}
                    placeholder="10:00"
                    className="p-2 rounded-lg bg-surface-container-lowest border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-outline uppercase font-semibold">Train Name</label>
                <input
                  type="text"
                  required
                  value={form.train_name}
                  onChange={(e) => setForm({ ...form, train_name: e.target.value })}
                  placeholder="e.g. Vande Bharat Express"
                  className="p-2 rounded-lg bg-surface-container-lowest border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-outline uppercase font-semibold">Corridor Route</label>
                  <select
                    value={form.route_id}
                    onChange={(e) => setForm({ ...form, route_id: e.target.value })}
                    className="p-2 rounded-lg bg-surface-container-lowest border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary"
                  >
                    <option value="R1">R1 — Delhi to Mumbai</option>
                    <option value="R2">R2 — Delhi to Amritsar</option>
                    <option value="R3">R3 — Bengaluru to Chennai</option>
                    <option value="R4">R4 — Howrah to Delhi</option>
                    <option value="R5">R5 — Mysuru to Bengaluru</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-outline uppercase font-semibold">Train Type</label>
                  <select
                    value={form.train_type}
                    onChange={(e) => setForm({ ...form, train_type: e.target.value })}
                    className="p-2 rounded-lg bg-surface-container-lowest border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary"
                  >
                    <option value="rajdhani_shatabdi_vb">Premier (Rajdhani/Shatabdi/VB)</option>
                    <option value="superfast">Superfast Express</option>
                    <option value="express">Express</option>
                    <option value="passenger">Passenger Local</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-outline uppercase font-semibold">Priority Tier (1 Highest)</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={form.priority}
                    onChange={(e) => setForm({ ...form, priority: Number(e.target.value) })}
                    className="p-2 rounded-lg bg-surface-container-lowest border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-outline uppercase font-semibold">Recovery Buffer Fraction</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="0.25"
                    value={form.recovery_fraction}
                    onChange={(e) => setForm({ ...form, recovery_fraction: Number(e.target.value) })}
                    className="p-2 rounded-lg bg-surface-container-lowest border border-outline-variant/40 text-on-surface focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-outline-variant/30 mt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-surface-container-high hover:bg-surface-container-highest text-on-surface font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-primary-container hover:bg-primary text-black font-display font-bold"
                >
                  {editingTrainNo ? 'Save Changes' : 'Create & Generate Schedule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  )
}
