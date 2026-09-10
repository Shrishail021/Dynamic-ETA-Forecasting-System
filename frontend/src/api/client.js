/*
  Single API client for RailPulse frontend.
  All network requests are routed through this file.
*/

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

async function request(path, options = {}) {
  const token = options.token || localStorage.getItem('eta_token')
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}`, 'x-admin-token': token } : {}),
    ...(options.headers || {}),
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    let errorDetail = `Status ${res.status}`
    try {
      const errJson = await res.json()
      errorDetail = errJson.detail || JSON.stringify(errJson)
    } catch {
      errorDetail = await res.text()
    }
    throw new Error(errorDetail || `API ${path} failed with code ${res.status}`)
  }

  // If endpoint returns binary/blob
  if (options.asBlob) {
    return res.blob()
  }

  return res.json()
}

export const api = {
  // Public Trains
  listTrains: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/trains${qs ? `?${qs}` : ''}`)
  },
  getTrain: (trainNo) => request(`/trains/${trainNo}`),
  getNearbyTrains: (lat, lon) => request(`/trains/nearby?lat=${lat}&lon=${lon}`),
  ingestRailRadarFeed: (payload) =>
    request('/live/railradar-adapter', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Dynamic ETA Prediction
  predictEta: (payload, useModel = true) =>
    request(`/eta/predict?use_model=${useModel}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Authentication
  login: (username, password) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  getMe: (token) => request('/auth/me', { token }),

  // Control Room (Staff & Admin)
  getControlRoomOverview: (token) => request('/control-room/overview', { token }),

  // Admin Train Master CRUD
  adminListTrains: (token) => request('/admin/trains', { token }),
  adminCreateTrain: (token, payload) =>
    request('/admin/trains', {
      method: 'POST',
      token,
      body: JSON.stringify(payload),
    }),
  adminUpdateTrain: (token, trainNo, payload) =>
    request(`/admin/trains/${trainNo}`, {
      method: 'PUT',
      token,
      body: JSON.stringify(payload),
    }),
  adminDeleteTrain: (token, trainNo) =>
    request(`/admin/trains/${trainNo}`, {
      method: 'DELETE',
      token,
    }),

  // Telemetry & ML Model Metrics
  getTelemetryStats: (token) => request('/telemetry/stats', { token }),
  getModelMetrics: () => request('/telemetry/model-metrics'),
  downloadSqlExport: (token) => request('/telemetry/export.sql', { token, asBlob: true }),

  // Station Master & Autonomous Broadcast
  getStationMasterStations: () => request('/station-master/stations'),
  getStationMasterOverview: (stationCode) => request(`/station-master/station/${stationCode}`),
  getAutonomousBroadcast: (trainNo, params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/station-master/autonomous-broadcast/${trainNo}${qs ? `?${qs}` : ''}`)
  },

  // Live SSE Stream
  liveStreamUrl: (trainNo, date, { seed, speed } = {}) => {
    const qs = new URLSearchParams({
      date,
      ...(seed != null ? { seed } : {}),
      ...(speed != null ? { speed } : {}),
    })
    return `${BASE_URL}/live/${trainNo}/stream?${qs.toString()}`
  },
}
