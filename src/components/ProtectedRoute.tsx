import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useSessionStore } from '../store/useSessionStore'
import type { Role } from '../types'

export function ProtectedRoute({ role, children }: { role: Exclude<Role, null>; children: ReactNode }) {
  const current = useSessionStore((s) => s.role)
  if (current !== role) return <Navigate to="/login" replace />
  return <>{children}</>
}
