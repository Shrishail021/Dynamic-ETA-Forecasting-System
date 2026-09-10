import React from 'react'

export default function Footer() {
  return (
    <footer className="w-full mt-auto border-t border-outline-variant bg-white py-4 px-4 sm:px-8 text-center text-xs text-on-surface-variant">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
        
        {/* Left: Brand */}
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-primary"></span>
          <span className="font-semibold text-navy">RailPulse</span>
          <span className="text-outline-variant">•</span>
          <span>Dynamic ETA Forecasting Prototype</span>
        </div>

        {/* Centre: Data Source Legend */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-green-500"></span>
            <span className="text-[11px] font-semibold text-green-700">RailRadar / Live API</span>
            <span className="text-[10px] text-outline">— real telemetry feed</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-blue-400"></span>
            <span className="text-[11px] font-semibold text-primary">Simulated Demo</span>
            <span className="text-[10px] text-outline">— calibrated synthetic data</span>
          </div>
        </div>

        {/* Right: Disclaimer */}
        <div className="text-on-surface-variant font-medium max-w-xs text-right">
          <span className="text-secondary font-semibold">Disclaimer:</span> All simulated data is calibrated synthetic telemetry — not live Indian Railways operational data.
        </div>
      </div>
    </footer>
  )
}
