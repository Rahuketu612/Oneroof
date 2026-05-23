import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'

// Layouts
import DashboardLayout from './components/layouts/DashboardLayout'
import AuthLayout from './components/layouts/AuthLayout'

// Pages
import LoginPage from './pages/auth/LoginPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import WorkspacesPage from './pages/workspaces/WorkspacesPage'
import WorkspaceDetailPage from './pages/workspaces/WorkspaceDetailPage'
import CompliancePage from './pages/compliance/CompliancePage'
import DocumentsPage from './pages/documents/DocumentsPage'
import NoticesPage from './pages/notices/NoticesPage'
import ClientsPage from './pages/clients/ClientsPage'
import ApprovalsPage from './pages/approvals/ApprovalsPage'
import SettingsPage from './pages/settings/SettingsPage'
import ReportsPage from './pages/reports/ReportsPage'

// Protected route wrapper
function ProtectedRoute({ children, allowedRoles }: { children: React.ReactNode, allowedRoles?: string[] }) {
  const { user, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  if (!user) {
    return <Navigate to="/login" replace />
  }
  
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />
  }
  
  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Auth routes */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
          </Route>
          
          {/* Protected app routes */}
          <Route element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/workspaces" element={<WorkspacesPage />} />
            <Route path="/workspaces/:id" element={<WorkspaceDetailPage />} />
            <Route path="/compliance" element={<CompliancePage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/notices" element={<NoticesPage />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/approvals" element={<ApprovalsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Route>
          
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
        
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#22c55e',
                secondary: '#fff',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App