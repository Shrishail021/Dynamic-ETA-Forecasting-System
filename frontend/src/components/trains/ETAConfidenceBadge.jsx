import React from 'react'
import { formatDelayHuman } from '../../utils/timeUtils.js'

/**
 * Reusable visual confidence band for ETA predictions.
 * Displays P50 (Likely arrival delay) and P90 (Uncertainty upper bound).
 */
export default function ETAConfidenceBadge({ p50, p90, method = 'gbm_model' }) {
  const p50Val = Number(p50 || 0)
  const p90Val = Number(p90 || p50Val)

  // Status color logic based on P50 delay
  let statusColor = 'text-primary'
  let barGradient = 'from-primary/60 to-primary-container'
  let pillBg = 'bg-primary-container/10 border-primary-container/30'

  if (p50Val > 30) {
    statusColor = 'text-hazard-coral'
    barGradient = 'from-secondary to-hazard-coral'
    pillBg = 'bg-hazard-coral/10 border-hazard-coral/30'
  } else if (p50Val > 10) {
    statusColor = 'text-secondary'
    barGradient = 'from-primary to-secondary'
    pillBg = 'bg-secondary/10 border-secondary/30'
  }

  // Width calculation for visual confidence band (capped for clean display)
  const p50Width = Math.min(Math.max((p50Val / 60) * 100, 15), 75)
  const p90Width = Math.min(Math.max((p90Val / 60) * 100, p50Width + 10), 100)

  return (
    <div className={`flex flex-col gap-1.5 p-3 rounded-xl border ${pillBg} backdrop-blur-sm`}>
      <div className="flex items-center justify-between text-xs">
        <span className="text-on-surface-variant font-medium flex items-center gap-1">
          <span className="material-symbols-outlined text-[14px]">tune</span>
          Confidence Band
        </span>
        <span className="text-[10px] font-display text-on-surface-variant/80 uppercase">
          {method.includes('gbm') ? 'ML Quantile Regressor' : 'Baseline Extrapolation'}
        </span>
      </div>

      {/* Visual Gauge Bar */}
      <div className="w-full h-2.5 bg-surface-container-highest rounded-full overflow-hidden relative">
        {/* P90 extended uncertainty range */}
        <div
          className="absolute top-0 bottom-0 left-0 bg-primary/25 rounded-full"
          style={{ width: `${p90Width}%` }}
          title={`P90 upper bound: +${p90Val} min`}
        ></div>
        {/* P50 solid marker */}
        <div
          className={`absolute top-0 bottom-0 left-0 bg-gradient-to-r ${barGradient} rounded-full`}
          style={{ width: `${p50Width}%` }}
          title={`P50 likely arrival: +${p50Val} min`}
        ></div>
      </div>

      {/* Numerical Labels */}
      <div className="flex items-center justify-between text-xs mt-0.5">
        <div className="flex items-baseline gap-1">
          <span className="text-[10px] text-on-surface-variant uppercase font-semibold">Likely (P50):</span>
          <span className={`font-display font-bold ${statusColor}`}>
            {formatDelayHuman(p50Val)}
          </span>
          {p50Val >= 60 && (
            <span className="text-[10px] text-slate-400">({p50Val.toFixed(0)}m)</span>
          )}
        </div>
        <div className="flex items-baseline gap-1">
          <span className="text-[10px] text-on-surface-variant uppercase font-semibold">Upper Bound (P90):</span>
          <span className="font-display font-semibold text-on-surface">
            {formatDelayHuman(p90Val)}
          </span>
        </div>
      </div>
    </div>
  )
}
