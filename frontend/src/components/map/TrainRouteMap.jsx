import React, { useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'

// Component to dynamically fit map view to the current train's route
function AutoFitRoute({ positions }) {
  const map = useMap()
  useEffect(() => {
    if (positions && positions.length > 1) {
      const bounds = L.latLngBounds(positions)
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 8 })
    } else if (positions && positions.length === 1) {
      map.setView(positions[0], 6)
    }
  }, [positions, map])
  return null
}

// Custom Leaflet Icons — Light Theme
function createStationIcon(isCurrent, isPast) {
  const bg    = isCurrent ? '#1559a8' : isPast ? '#2e7fdf' : '#c6d8eb'
  const border = isCurrent ? '#ffffff' : isPast ? '#ffffff' : '#7a96b4'
  const size  = isCurrent ? 14 : 10

  return L.divIcon({
    className: 'custom-station-icon',
    html: `<div style="
      width: ${size}px;
      height: ${size}px;
      background-color: ${bg};
      border: 2px solid ${border};
      border-radius: 50%;
      box-shadow: ${isCurrent ? '0 0 10px rgba(21,89,168,0.7)' : 'none'};
    "></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })
}

function createTrainPuckIcon() {
  return L.divIcon({
    className: 'custom-train-icon',
    html: `<div style="
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
    ">
      <div style="
        position: absolute;
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background-color: rgba(21, 89, 168, 0.25);
        animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
      "></div>
      <div style="
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background-color: #1559a8;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(21,89,168,0.6);
        font-size: 13px;
        font-weight: bold;
      ">🚂</div>
    </div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  })
}

import { formatClockTime, formatHalt } from '../../utils/timeUtils.js'

export default function TrainRouteMap({
  schedule = [],
  currentSeq = 1,
  trainName = '',
  trainNo = '',
  originDepTime = '10:00',
}) {
  // Filter stations that have valid coordinates
  const validStops = useMemo(() => {
    return schedule.filter(
      (s) => s.latitude != null && s.longitude != null && !isNaN(s.latitude) && !isNaN(s.longitude)
    )
  }, [schedule])

  const routePolyline = useMemo(() => {
    return validStops.map((s) => [Number(s.latitude), Number(s.longitude)])
  }, [validStops])

  // Current train position marker coordinates
  const trainCoord = useMemo(() => {
    if (!validStops.length) return [28.6431, 77.2197]
    const currentStop = validStops.find((s) => s.seq === currentSeq)
    if (currentStop) return [Number(currentStop.latitude), Number(currentStop.longitude)]

    // Interpolate between stops if possible
    const prevStop = validStops.filter((s) => s.seq <= currentSeq).pop()
    const nextStop = validStops.filter((s) => s.seq > currentSeq).shift()
    if (prevStop && nextStop) {
      return [
        (Number(prevStop.latitude) + Number(nextStop.latitude)) / 2,
        (Number(prevStop.longitude) + Number(nextStop.longitude)) / 2,
      ]
    }
    return [Number(validStops[0].latitude), Number(validStops[0].longitude)]
  }, [validStops, currentSeq])

  const initialCenter = routePolyline.length > 0 ? routePolyline[0] : [28.6431, 77.2197]

  return (
    <div className="w-full h-80 sm:h-96 rounded-2xl overflow-hidden relative z-0 border border-outline-variant shadow-card">
      <MapContainer
        center={initialCenter}
        zoom={6}
        scrollWheelZoom={false}
        className="w-full h-full"
        style={{ background: '#f0f5fb' }}
      >
        {/*
          OpenStreetMap tiles — completely FREE, no API key required.
          Clear, crisp light tiles that match the app's light theme.
        */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        {/* Route Polyline */}
        {routePolyline.length > 1 && (
          <>
            {/* Wide glow shadow */}
            <Polyline
              positions={routePolyline}
              pathOptions={{
                color: '#1559a8',
                weight: 8,
                opacity: 0.18,
                lineCap: 'round',
                lineJoin: 'round',
              }}
            />
            {/* Sharp railway line */}
            <Polyline
              positions={routePolyline}
              pathOptions={{
                color: '#1559a8',
                weight: 3,
                opacity: 0.85,
                dashArray: '10, 7',
              }}
            />
          </>
        )}

        {/* Station Markers */}
        {validStops.map((stop) => {
          const isCurrent = stop.seq === currentSeq
          const isPast = stop.seq < currentSeq
          return (
            <Marker
              key={stop.seq}
              position={[Number(stop.latitude), Number(stop.longitude)]}
              icon={createStationIcon(isCurrent, isPast)}
            >
              <Popup>
                <div className="p-1 text-xs font-sans text-gray-900 leading-snug">
                  <div className="font-bold text-sm text-blue-700">
                    {stop.station_name || stop.station_code} ({stop.station_code})
                  </div>
                  <div className="text-[11px] text-gray-500 mt-0.5">Stop #{stop.seq}</div>
                  <div className="mt-1 pt-1 border-t border-gray-200 flex flex-col gap-0.5">
                    <div>Sched Arr: <strong>{formatClockTime(originDepTime, stop.scheduled_arrival_min)}</strong></div>
                    <div>Sched Dep: <strong>{formatClockTime(originDepTime, stop.scheduled_departure_min)}</strong></div>
                    <div className="text-[11px] text-gray-600">Dist: <strong>{stop.distance_from_origin_km} km</strong> • Halt: <strong>{formatHalt(stop.halt_min)}</strong></div>
                  </div>
                  {isCurrent && (
                    <div className="mt-1 text-[10px] font-bold text-blue-600">● Train currently here</div>
                  )}
                </div>
              </Popup>
            </Marker>
          )
        })}

        {/* Active Train Marker */}
        {trainCoord && (
          <Marker position={trainCoord} icon={createTrainPuckIcon()}>
            <Popup>
              <div className="p-1 text-xs font-sans text-gray-900">
                <div className="font-bold text-sm text-blue-700">Train {trainNo}</div>
                <div className="text-[11px] text-gray-600">{trainName}</div>
                <div className="text-[10px] text-blue-600 font-bold mt-1">● Estimated Position</div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Auto-fit map to the route */}
        <AutoFitRoute positions={routePolyline} />
      </MapContainer>
    </div>
  )
}
