import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../context/AuthContext'
import { 
  Building2, 
  FileCheck, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  Bell,
  ArrowRight,
  TrendingUp,
  Users,
  Calendar
} from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'

interface DashboardData {
  summary: {
    total_workspaces: number
    active_compliances: number
    pending_approvals: number
    overdue_items: number
    upcoming_deadlines: number
    pending_notices: number
  }
  compliance_status: Array<{ status: string; count: number }>
  staff_workload: Array<{
    user_id: number
    user_name: string
    assigned_items: number
    completed_items: number
    pending_items: number
  }>
  client_risks: Array<{
    client_id: number
    client_name: string
    risk_score: number
    overdue_count: number
    pending_approvals: number
  }>
  upcoming_deadlines: Array<{
    compliance_item_id: number
    compliance_name: string
    client_name: string
    due_date: string
    days_until_due: number
    status: string
  }>
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    try {
      const response = await api.get('/dashboard/partner')
      setData(response.data)
    } catch (error) {
      console.error('Failed to fetch dashboard:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!data) {
    return <div className="text-gray-500">Failed to load dashboard</div>
  }

  const statCards = [
    { label: 'Total Workspaces', value: data.summary.total_workspaces, icon: Building2, color: 'primary' },
    { label: 'Active Compliances', value: data.summary.active_compliances, icon: FileCheck, color: 'success' },
    { label: 'Pending Approvals', value: data.summary.pending_approvals, icon: Clock, color: 'warning' },
    { label: 'Overdue Items', value: data.summary.overdue_items, icon: AlertTriangle, color: 'danger' },
    { label: 'Upcoming Deadlines', value: data.summary.upcoming_deadlines, icon: Calendar, color: 'secondary' },
    { label: 'Pending Notices', value: data.summary.pending_notices, icon: Bell, color: 'primary' },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Overview of your compliance operations</p>
        </div>
        <div className="flex gap-3">
          <Link 
            to="/workspaces"
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2"
          >
            <Building2 className="w-4 h-4" />
            View Workspaces
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {statCards.map((stat, index) => (
          <div key={index} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-${stat.color}-100`}>
                <stat.icon className={`w-5 h-5 text-${stat.color}-600`} />
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
            <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upcoming Deadlines */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary-600" />
              Upcoming Deadlines
            </h2>
            <Link to="/compliance" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-gray-100">
            {data.upcoming_deadlines.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                No upcoming deadlines
              </div>
            ) : (
              data.upcoming_deadlines.map((item, index) => (
                <div key={index} className="p-4 flex items-center justify-between hover:bg-gray-50">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.compliance_name}</p>
                    <p className="text-sm text-gray-500">{item.client_name}</p>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-medium ${
                      item.days_until_due < 0 ? 'text-danger-600' :
                      item.days_until_due === 0 ? 'text-warning-600' :
                      'text-gray-600'
                    }`}>
                      {item.days_until_due < 0 ? 'Overdue' : 
                       item.days_until_due === 0 ? 'Due today' :
                       `${item.days_until_due} days`}
                    </p>
                    <p className="text-xs text-gray-400">
                      {format(new Date(item.due_date), 'MMM d')}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Client Risks */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-warning-500" />
              Client Risk Monitor
            </h2>
            <Link to="/clients" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-gray-100">
            {data.client_risks.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                No clients at risk
              </div>
            ) : (
              data.client_risks
                .filter(c => c.risk_score > 0)
                .slice(0, 5)
                .map((client, index) => (
                  <div key={index} className="p-4 flex items-center justify-between hover:bg-gray-50">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-warning-100 flex items-center justify-center">
                        <Users className="w-5 h-5 text-warning-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{client.client_name}</p>
                        <p className="text-sm text-gray-500">
                          {client.overdue_count} overdue, {client.pending_approvals} pending
                        </p>
                      </div>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                      client.risk_score >= 60 ? 'bg-danger-100 text-danger-700' :
                      client.risk_score >= 30 ? 'bg-warning-100 text-warning-700' :
                      'bg-success-100 text-success-700'
                    }`}>
                      {client.risk_score}%
                    </div>
                  </div>
                ))
            )}
          </div>
        </div>

        {/* Compliance Status Breakdown */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-success-600" />
              Compliance Status
            </h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {data.compliance_status.map((item, index) => {
                const total = data.compliance_status.reduce((sum, i) => sum + i.count, 0)
                const percentage = total > 0 ? (item.count / total) * 100 : 0
                return (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700 capitalize">{item.status.replace('_', ' ')}</span>
                      <span className="text-sm text-gray-500">{item.count}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          item.status === 'filed' ? 'bg-success-500' :
                          item.status === 'overdue' ? 'bg-danger-500' :
                          item.status === 'in_progress' ? 'bg-primary-500' :
                          'bg-gray-400'
                        }`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Staff Workload */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Users className="w-5 h-5 text-secondary-600" />
              Staff Workload
            </h2>
          </div>
          <div className="divide-y divide-gray-100">
            {data.staff_workload.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                No staff assigned
              </div>
            ) : (
              data.staff_workload.map((staff, index) => (
                <div key={index} className="p-4 flex items-center justify-between hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-secondary-100 flex items-center justify-center">
                      <span className="text-secondary-700 font-medium text-sm">
                        {staff.user_name.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{staff.user_name}</p>
                      <p className="text-sm text-gray-500">{staff.assigned_items} assigned</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-1 text-success-600">
                      <CheckCircle2 className="w-4 h-4" />
                      <span className="text-sm font-medium">{staff.completed_items}</span>
                    </div>
                    <p className="text-xs text-gray-400">completed</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}