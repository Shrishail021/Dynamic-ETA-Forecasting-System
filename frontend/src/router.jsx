import { createBrowserRouter, Navigate } from 'react-router-dom'
import RootLayout from './components/layout/RootLayout.jsx'
import HomePage from './pages/public/HomePage.jsx'
import TrainSearchPage from './pages/public/TrainSearchPage.jsx'
import TrainLiveEtaPage from './pages/public/TrainLiveEtaPage.jsx'
import AdminLoginPage from './pages/admin/AdminLoginPage.jsx'
import TrainMasterPage from './pages/admin/TrainMasterPage.jsx'
import ControlRoomPage from './pages/staff/ControlRoomPage.jsx'
import ModelBenchmarkPage from './pages/admin/ModelBenchmarkPage.jsx'
import StationMasterPage from './pages/staff/StationMasterPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import { useAuth } from './context/AuthContext.jsx'

function RequireAdmin({ children }) {
  const { role, isAuthenticated } = useAuth()
  if (!isAuthenticated) {
    return <Navigate to="/admin/login" replace />
  }
  if (role !== 'admin') {
    return <Navigate to="/control-room" replace />
  }
  return children
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'trains', element: <TrainSearchPage /> },
      { path: 'trains/:trainNo', element: <TrainLiveEtaPage /> },
      { path: 'station-master', element: <StationMasterPage /> },
      { path: 'control-room', element: <ControlRoomPage /> },
      { path: 'admin/login', element: <AdminLoginPage /> },
      {
        path: 'admin/trains',
        element: (
          <RequireAdmin>
            <TrainMasterPage />
          </RequireAdmin>
        ),
      },
      { path: 'admin/models', element: <ModelBenchmarkPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
