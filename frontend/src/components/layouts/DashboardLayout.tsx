import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { 
  LayoutDashboard, 
  Building2, 
  FileCheck, 
  FolderOpen, 
  AlertCircle, 
  Users, 
  LogOut,
  ChevronDown,
  Settings,
  FileBarChart,
  CheckCircle,
  Bell
} from 'lucide-react'
import { useState } from 'react'
import NotificationBell from '../notifications/NotificationBell'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Workspaces', href: '/workspaces', icon: Building2 },
  { name: 'Compliance', href: '/compliance', icon: FileCheck },
  { name: 'Approvals', href: '/approvals', icon: CheckCircle },
  { name: 'Documents', href: '/documents', icon: FolderOpen },
  { name: 'Notices', href: '/notices', icon: AlertCircle },
  { name: 'Clients', href: '/clients', icon: Users },
  { name: 'Reports', href: '/reports', icon: FileBarChart },
]

export default function DashboardLayout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo and Nav */}
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <Link to="/dashboard" className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-secondary-600 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-sm">OR</span>
                  </div>
                  <span className="font-semibold text-gray-900 text-lg">OneRoof</span>
                </Link>
              </div>
              
              <div className="hidden sm:ml-8 sm:flex sm:space-x-1">
                {navigation.map((item) => {
                  const isActive = location.pathname.startsWith(item.href)
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`
                        inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors
                        ${isActive 
                          ? 'bg-primary-50 text-primary-700' 
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}
                      `}
                    >
                      <item.icon className="w-4 h-4 mr-2" />
                      {item.name}
                    </Link>
                  )
                })}
              </div>
            </div>

            {/* Right side */}
            <div className="flex items-center gap-3">
              {/* Notifications */}
              <NotificationBell />

              {/* Settings */}
              <Link to="/settings" className="p-2 text-gray-400 hover:text-gray-500">
                <Settings className="w-5 h-5" />
              </Link>

              {/* User Menu */}
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 p-2 text-gray-700 hover:bg-gray-50 rounded-md"
                >
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-primary-700 font-medium text-sm">
                      {user?.first_name?.[0]}{user?.last_name?.[0]}
                    </span>
                  </div>
                  <div className="hidden md:block text-left">
                    <p className="text-sm font-medium">{user?.first_name} {user?.last_name}</p>
                    <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
                  </div>
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                </button>

                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50">
                    <div className="px-4 py-2 border-b border-gray-100">
                      <p className="text-sm font-medium">{user?.email}</p>
                    </div>
                    <Link
                      to="/settings"
                      className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      <Settings className="w-4 h-4" />
                      Settings
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      <LogOut className="w-4 h-4" />
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}