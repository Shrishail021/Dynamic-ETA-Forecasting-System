import React from 'react'
import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="w-full flex-1 flex items-center justify-center px-4 py-16">
      <div className="glass-panel p-8 rounded-2xl max-w-md text-center flex flex-col items-center gap-4">
        <div className="w-16 h-16 rounded-2xl bg-hazard-coral/15 text-hazard-coral flex items-center justify-center">
          <span className="material-symbols-outlined text-3xl">wrong_location</span>
        </div>
        <h1 className="font-display font-bold text-2xl text-on-surface">
          404 — Route Vector Not Found
        </h1>
        <p className="text-xs text-on-surface-variant">
          The requested checkpoint, corridor, or operational panel does not exist or has been relocated.
        </p>
        <Link
          to="/"
          className="mt-2 px-4 py-2 rounded-xl bg-primary-container text-black font-display font-bold text-xs shadow-md"
        >
          Return to Radar Hub
        </Link>
      </div>
    </div>
  )
}
