import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../context/AuthContext'
import { motion } from 'framer-motion'
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
  Calendar,
  DollarSign,
  FileText,
  RefreshCw
} from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'
import { 
  AreaChart, 
  Area, 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  BarChart, 
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts'

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

// Chart colors
const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
}

// Stat Card Component
function StatCard({ label, value, icon: Icon, color, trend }: { 
  label: string
  value: number
  icon: any
  color: string
  trend?: string
}) {
  const colorMap: Record<string, string> = {
    primary: { bg: 'bg-blue-50', text: 'text-blue-600', ring: 'ring-blue-100' },
    success: { bg: 'bg-emerald-50', text: 'text-emerald-600', ring: 'ring-emerald-100' },
    warning: { bg: 'bg-amber-50', text: 'text-amber-600', ring: 'ring-amber-100' },
    danger: { bg: 'bg-red-50', text: 'text-red-600', ring: 'ring-red-100' },
    secondary: { bg: 'bg-purple-50', text: 'text-purple-600', ring: 'ring-purple-100' },
  }
  
  const styles = colorMap[color] || colorMap.primary
  
  return (
    <motion.div
      variants={itemVariants}
      whileHover={{ y: -4, boxShadow: '0 10px 40px -10px rgba(0,0,0,0.1)' }}
      className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:border-gray-200 transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between">
        <div className={`w-14 h-14 rounded-2xl ${styles.bg} flex items-center justify-center ring-4 ${styles.ring} group-hover:scale-110 transition-transform`}>
          <Icon className={`w-6 h-6 ${styles.text}`} />
        </div>
        {trend && (
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${
            trend.startsWith('+') ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
          }`}>
            {trend}
          </span>
        )}
      </div>
      <div className="mt-4">
        <p className="text-3xl font-bold text-gray-900">{value.toLocaleString()}</p>
        <p className="text-sm text-gray-500 mt-1">{label}</p>
      </div>
    </motion.div>
  )
}

// Mini Chart Component
function MiniAreaChart({ data, color }: { data: number[], color: string }) {
  const chartData = data.map((value, i) => ({ value, index: i }))
  return (
    <ResponsiveContainer width="100%" height={40}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
            <stop offset="95%" stopColor={color} stopOpacity={0}/>
          </linearGradient>
        </defs>
        <Area 
          type="monotone" 
          dataKey="value" 
          stroke={color} 
          strokeWidth={2}
          fill={`url(#gradient-${color})`}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year'>('month')

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    setIsLoading(true)
    try {
      const response = await api.get('/dashboard/partner')
      setData(response.data)
    } catch (error) {
      console.error('Failed to fetch dashboard:', error)
      // Use sample data for demo
      setData(generateSampleData())
    } finally {
      setIsLoading(false)
    }
  }

  const generateSampleData = (): DashboardData => ({
    summary: {
      total_workspaces: 24,
      active_compliances: 156,
      pending_approvals: 8,
      overdue_items: 3,
      upcoming_deadlines: 12,
      pending_notices: 5,
    },
    compliance_status: [
      { status: 'filed', count: 89 },
      { status: 'in_progress', count: 42 },
      { status: 'pending', count: 18 },
      { status: 'overdue', count: 7 },
    ],
    staff_workload: [
      { user_id: 1, user_name: 'Priya Patel', assigned_items: 15, completed_items: 12, pending_items: 3 },
      { user_id: 2, user_name: 'Amit Singh', assigned_items: 18, completed_items: 15, pending_items: 3 },
      { user_id: 3, user_name: 'Neha Sharma', assigned_items: 12, completed_items: 10, pending_items: 2 },
    ],
    client_risks: [
      { client_id: 1, client_name: 'Tech Solutions Pvt Ltd', risk_score: 75, overdue_count: 2, pending_approvals: 1 },
      { client_id: 2, client_name: 'Green Earth Enterprises', risk_score: 45, overdue_count: 1, pending_approvals: 0 },
      { client_id: 3, client_name: 'Metro Logistics LLP', risk_score: 20, overdue_count: 0, pending_approvals: 2 },
    ],
    upcoming_deadlines: [
      { compliance_item_id: 1, compliance_name: 'GSTR-3B Filing - May 2026', client_name: 'Tech Solutions', due_date: '2026-05-20', days_until_due: 3, status: 'pending' },
      { compliance_item_id: 2, compliance_name: 'TDS Quarterly Return', client_name: 'Metro Logistics', due_date: '2026-05-31', days_until_due: 14, status: 'pending' },
      { compliance_item_id: 3, compliance_name: 'GSTR-1 Filing - May 2026', client_name: 'Green Earth', due_date: '2026-05-10', days_until_due: -2, status: 'overdue' },
    ],
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-10 h-10 mx-auto animate-spin text-primary-600 mb-4" />
          <p className="text-gray-500">Loading dashboard...</p>
        </div>
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

  // Prepare chart data
  const pieData = data.compliance_status.map(item => ({
    name: item.status.replace('_', ' '),
    value: item.count,
  }))

  const totalCompliances = data.compliance_status.reduce((sum, i) => sum + i.count, 0)

  return (
    <motion.div 
      className="space-y-8"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Welcome back! Here's your compliance overview.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex bg-gray-100 rounded-lg p-1">
            {(['week', 'month', 'year'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  timeRange === range
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {range.charAt(0).toUpperCase() + range.slice(1)}
              </button>
            ))}
          </div>
          <button 
            onClick={fetchDashboard}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RefreshCw className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {statCards.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Chart - Compliance Overview */}
        <motion.div variants={itemVariants} className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Compliance Overview</h2>
              <p className="text-sm text-gray-500 mt-1">Status distribution across all workspaces</p>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
              <span className="text-gray-500">Filed</span>
              <span className="w-3 h-3 rounded-full bg-blue-500 ml-2"></span>
              <span className="text-gray-500">In Progress</span>
              <span className="w-3 h-3 rounded-full bg-amber-500 ml-2"></span>
              <span className="text-gray-500">Pending</span>
            </div>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={[
                { name: 'Jan', filed: 65, progress: 28, pending: 12 },
                { name: 'Feb', filed: 72, progress: 35, pending: 15 },
                { name: 'Mar', filed: 78, progress: 32, pending: 10 },
                { name: 'Apr', filed: 85, progress: 38, pending: 8 },
                { name: 'May', filed: 89, progress: 42, pending: 18 },
              ]}>
                <defs>
                  <linearGradient id="colorFiled" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorProgress" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorPending" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#F59E0B" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}
                />
                <Legend />
                <Area type="monotone" dataKey="filed" stroke="#10B981" strokeWidth={2} fillOpacity={1} fill="url(#colorFiled)" name="Filed" />
                <Area type="monotone" dataKey="progress" stroke="#3B82F6" strokeWidth={2} fillOpacity={1} fill="url(#colorProgress)" name="In Progress" />
                <Area type="monotone" dataKey="pending" stroke="#F59E0B" strokeWidth={2} fillOpacity={1} fill="url(#colorPending)" name="Pending" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Compliance Pie Chart */}
        <motion.div variants={itemVariants} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Status Split</h2>
              <p className="text-sm text-gray-500 mt-1">Current period breakdown</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-4 mt-4">
            {pieData.map((item, index) => (
              <div key={index} className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></span>
                <span className="text-sm text-gray-600 capitalize">{item.name}</span>
                <span className="text-sm font-semibold text-gray-900">{item.value}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upcoming Deadlines */}
        <motion.div variants={itemVariants} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                <Clock className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Upcoming Deadlines</h2>
                <p className="text-sm text-gray-500">{data.upcoming_deadlines.length} items due this month</p>
              </div>
            </div>
            <Link to="/compliance" className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-gray-50">
            {data.upcoming_deadlines.length === 0 ? (
              <div className="p-12 text-center">
                <CheckCircle2 className="w-16 h-16 mx-auto text-emerald-300 mb-4" />
                <p className="text-gray-500">All caught up!</p>
              </div>
            ) : (
              data.upcoming_deadlines.map((item, index) => (
                <div key={index} className="p-4 flex items-center gap-4 hover:bg-gray-50 transition-colors cursor-pointer group">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    item.days_until_due < 0 ? 'bg-red-100' :
                    item.days_until_due <= 3 ? 'bg-amber-100' :
                    'bg-blue-100'
                  }`}>
                    <FileText className={`w-5 h-5 ${
                      item.days_until_due < 0 ? 'text-red-600' :
                      item.days_until_due <= 3 ? 'text-amber-600' :
                      'text-blue-600'
                    }`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate group-hover:text-blue-600 transition-colors">{item.compliance_name}</p>
                    <p className="text-sm text-gray-500">{item.client_name}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className={`text-sm font-semibold ${
                      item.days_until_due < 0 ? 'text-red-600' :
                      item.days_until_due === 0 ? 'text-amber-600' :
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
        </motion.div>

        {/* Client Risk Monitor */}
        <motion.div variants={itemVariants} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Client Risk Monitor</h2>
                <p className="text-sm text-gray-500">{data.client_risks.filter(c => c.risk_score > 30).length} clients need attention</p>
              </div>
            </div>
            <Link to="/clients" className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="p-6">
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.client_risks} layout="vertical">
                  <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} domain={[0, 100]} />
                  <YAxis type="category" dataKey="client_name" axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} width={120} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}
                    formatter={(value: number) => [`${value}%`, 'Risk Score']}
                  />
                  <Bar dataKey="risk_score" radius={[0, 8, 8, 0]}>
                    {data.client_risks.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.risk_score >= 60 ? '#EF4444' : entry.risk_score >= 30 ? '#F59E0B' : '#10B981'} 
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Staff Performance */}
      <motion.div variants={itemVariants} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
              <Users className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Staff Performance</h2>
              <p className="text-sm text-gray-500">Workload distribution across team</p>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {data.staff_workload.map((staff, index) => {
            const completionRate = staff.assigned_items > 0 
              ? Math.round((staff.completed_items / staff.assigned_items) * 100) 
              : 0
            return (
              <div key={index} className="bg-gray-50 rounded-xl p-5 hover:bg-gray-100 transition-colors">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
                    <span className="text-white font-semibold text-sm">
                      {staff.user_name.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{staff.user_name}</p>
                    <p className="text-sm text-gray-500">{staff.assigned_items} tasks assigned</p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Completion Rate</span>
                      <span className="font-semibold text-purple-600">{completionRate}%</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <motion.div 
                        className="h-full bg-gradient-to-r from-purple-500 to-purple-600 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${completionRate}%` }}
                        transition={{ duration: 1, delay: index * 0.2 }}
                      />
                    </div>
                  </div>
                  <div className="flex justify-between text-sm">
                    <div>
                      <span className="text-gray-500">Completed</span>
                      <p className="font-semibold text-emerald-600">{staff.completed_items}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Pending</span>
                      <p className="font-semibold text-amber-600">{staff.pending_items}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">In Progress</span>
                      <p className="font-semibold text-blue-600">{staff.assigned_items - staff.completed_items - staff.pending_items}</p>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </motion.div>
    </motion.div>
  )
}