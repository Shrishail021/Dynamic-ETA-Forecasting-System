import React from 'react'

/**
 * Location-Aware Delay Root Cause Attribution Widget.
 * Explains WHY the train is delayed based on its physical section location (e.g. Dense Fog, TSR, Congestion).
 */
export default function DelayCauseAlert({ delayCause, currentLocation, currentDelay }) {
  if (!delayCause) return null

  const isFog = delayCause.primary_cause === 'DENSE_FOG'
  const isTSR = delayCause.primary_cause === 'TSR_RESTRICTION'
  const isCongestion = delayCause.primary_cause === 'LINE_CONGESTION'
  const isNominal = delayCause.primary_cause === 'ON_TIME_NOMINAL'

  if (isNominal && (!currentDelay || currentDelay <= 5)) {
    return (
      <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
            <span className="material-symbols-outlined text-xl">check_circle</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-display font-bold text-sm text-emerald-950">Normal Line Operations</span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold">ALL CLEAR</span>
            </div>
            <p className="text-xs text-emerald-800/80 mt-0.5">
              Track clear between stations. Operating at permissible line speed with normal signaling margins.
            </p>
          </div>
        </div>
      </div>
    )
  }

  const borderClass = isFog
    ? 'border-amber-300 bg-amber-50/70'
    : isTSR
    ? 'border-rose-300 bg-rose-50/70'
    : 'border-blue-300 bg-blue-50/70'

  const badgeClass = isFog
    ? 'bg-amber-100 text-amber-900 border-amber-300'
    : isTSR
    ? 'bg-rose-100 text-rose-900 border-rose-300'
    : 'bg-blue-100 text-blue-900 border-blue-300'

  const iconName = isFog ? 'foggy' : isTSR ? 'handyman' : 'traffic'

  return (
    <div className={`border-2 ${borderClass} rounded-2xl p-5 shadow-sm transition-all animate-fadeIn`}>
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className={`w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 ${
            isFog ? 'bg-amber-200/80 text-amber-900' : isTSR ? 'bg-rose-200/80 text-rose-900' : 'bg-blue-200/80 text-blue-900'
          }`}>
            <span className="material-symbols-outlined text-2xl">{iconName}</span>
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                Location-Based Delay Root Cause
              </span>
              <span className={`px-2 py-0.5 rounded-full border text-[10px] font-display font-bold uppercase ${badgeClass}`}>
                {isFog ? '🌫️ Weather Hazard' : isTSR ? '🚧 Caution Order' : '🛑 Track Saturation'}
              </span>
            </div>

            <h3 className="font-display font-bold text-base sm:text-lg text-navy mt-0.5">
              {delayCause.title || 'Delay Analysis'}
            </h3>

            <p className="text-xs text-slate-700 mt-1 max-w-2xl leading-relaxed">
              {delayCause.detailed_explanation}
            </p>

            {delayCause.safety_regulation && (
              <div className="flex items-center gap-1.5 mt-2 text-[11px] font-mono text-slate-600 bg-white/80 border border-slate-200 px-2.5 py-1 rounded-lg w-fit">
                <span className="material-symbols-outlined text-[13px] text-amber-600">verified</span>
                <span>{delayCause.safety_regulation}</span>
              </div>
            )}
          </div>
        </div>

        {/* Speed & Delay Impact Badges */}
        <div className="flex sm:flex-col items-end justify-between sm:justify-start gap-2 shrink-0 border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-200">
          <div className="flex flex-col items-end">
            <span className="text-[10px] uppercase font-bold text-slate-500">Speed Restricted To</span>
            <div className="flex items-baseline gap-1">
              <span className="font-display font-bold text-xl text-amber-900 tabular-nums">
                {delayCause.speed_restriction_kmph || 60}
              </span>
              <span className="text-[10px] text-slate-500">KM/H (Max)</span>
            </div>
            <span className="text-[10px] text-slate-500">
              Normal: {delayCause.nominal_speed_kmph || 130} km/h (-{delayCause.speed_drop_pct || 53}%)
            </span>
          </div>

          {delayCause.delay_contribution_min > 0 && (
            <div className="px-2.5 py-1 rounded-xl bg-white border border-amber-300 text-amber-900 text-xs font-display font-bold shadow-xs">
              Contributes +{delayCause.delay_contribution_min}m to ETA
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
