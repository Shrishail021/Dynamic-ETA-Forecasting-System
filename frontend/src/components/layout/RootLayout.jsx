import React from 'react'
import { Outlet } from 'react-router-dom'
import NavBar from './NavBar.jsx'
import Footer from './Footer.jsx'

export default function RootLayout() {
  return (
    <div className="flex flex-col min-h-screen bg-surface text-on-surface relative">
      {/* Subtle ambient gradient mesh in background */}
      <div className="fixed inset-0 pointer-events-none opacity-20 z-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary-container/20 via-surface to-surface-lowest"></div>
      
      <NavBar />
      
      <main className="flex-1 w-full pt-16 z-10 flex flex-col">
        <Outlet />
      </main>

      <Footer />
    </div>
  )
}
