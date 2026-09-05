import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Splash } from './pages/Splash'
import { Login } from './pages/Login'
import { CampusBiteTeaser } from './pages/CampusBiteTeaser'
import { ProtectedRoute } from './components/ProtectedRoute'
import { ToastContainer } from './components/ToastContainer'
import { StudentLayout } from './layouts/StudentLayout'
import { Home } from './pages/student/Home'
import { Explore } from './pages/student/Explore'
import { FoodDetails } from './pages/student/FoodDetails'
import { Cart } from './pages/student/Cart'
import { Payment } from './pages/student/Payment'
import { TokenScreen } from './pages/student/TokenScreen'
import { Orders } from './pages/student/Orders'
import { OrderTracking } from './pages/student/OrderTracking'
import { Profile } from './pages/student/Profile'

const StaffDashboard = lazy(() => import('./pages/staff/StaffDashboard').then((m) => ({ default: m.StaffDashboard })))
const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard').then((m) => ({ default: m.AdminDashboard })))

function DashboardLoading() {
  return (
    <div className="min-h-screen grid place-items-center bg-slate-50 text-slate-400 text-sm font-semibold">
      Loading dashboard…
    </div>
  )
}

function App() {
  return (
    <>
      <ToastContainer />
      <Routes>
        <Route path="/" element={<Splash />} />
        <Route path="/login" element={<Login />} />
        <Route path="/campus-bite" element={<CampusBiteTeaser />} />

        <Route
          path="/app"
          element={
            <ProtectedRoute role="student">
              <StudentLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="home" replace />} />
          <Route path="home" element={<Home />} />
          <Route path="explore" element={<Explore />} />
          <Route path="food/:id" element={<FoodDetails />} />
          <Route path="cart" element={<Cart />} />
          <Route path="payment" element={<Payment />} />
          <Route path="token/:orderId" element={<TokenScreen />} />
          <Route path="orders" element={<Orders />} />
          <Route path="orders/:orderId" element={<OrderTracking />} />
          <Route path="profile" element={<Profile />} />
        </Route>

        <Route
          path="/staff"
          element={
            <ProtectedRoute role="staff">
              <Suspense fallback={<DashboardLoading />}>
                <StaffDashboard />
              </Suspense>
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin"
          element={
            <ProtectedRoute role="admin">
              <Suspense fallback={<DashboardLoading />}>
                <AdminDashboard />
              </Suspense>
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default App
