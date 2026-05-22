import { Outlet } from 'react-router-dom'

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-secondary-600 rounded-2xl mb-4">
            <span className="text-white font-bold text-2xl">OR</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">OneRoof</h1>
          <p className="text-gray-600 mt-2">Compliance Collaboration Operating System</p>
        </div>
        
        <Outlet />
      </div>
    </div>
  )
}