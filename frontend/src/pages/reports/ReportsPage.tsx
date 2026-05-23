import { useState } from 'react'
import { FileText, Download, Calendar, TrendingUp, Users, AlertTriangle } from 'lucide-react'
import { format } from 'date-fns'

interface Report {
  id: string
  name: string
  description: string
  type: 'compliance' | 'client' | 'financial' | 'audit'
  lastGenerated: string
}

const reports: Report[] = [
  { id: '1', name: 'Monthly Compliance Summary', description: 'Overview of all compliance items for the month', type: 'compliance', lastGenerated: new Date().toISOString() },
  { id: '2', name: 'Client Risk Report', description: 'Risk assessment for all clients', type: 'client', lastGenerated: new Date().toISOString() },
  { id: '3', name: 'Staff Performance Report', description: 'Task completion and workload analysis', type: 'compliance', lastGenerated: new Date().toISOString() },
  { id: '4', name: 'Audit Trail Export', description: 'Complete activity log for compliance period', type: 'audit', lastGenerated: new Date().toISOString() },
  { id: '5', name: 'Overdue Items Report', description: 'List of all overdue compliance items', type: 'compliance', lastGenerated: new Date().toISOString() },
  { id: '6', name: 'Filing Status Report', description: 'Status of all filed and pending returns', type: 'financial', lastGenerated: new Date().toISOString() },
]

export default function ReportsPage() {
  const [selectedReport, setSelectedReport] = useState<string | null>(null)
  const [dateRange, setDateRange] = useState({ from: new Date().toISOString(), to: new Date().toISOString() })

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'compliance': return <FileText className="w-5 h-5" />
      case 'client': return <Users className="w-5 h-5" />
      case 'financial': return <TrendingUp className="w-5 h-5" />
      case 'audit': return <AlertTriangle className="w-5 h-5" />
      default: return <FileText className="w-5 h-5" />
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'compliance': return 'bg-primary-100 text-primary-600'
      case 'client': return 'bg-secondary-100 text-secondary-600'
      case 'financial': return 'bg-success-100 text-success-600'
      case 'audit': return 'bg-warning-100 text-warning-600'
      default: return 'bg-gray-100 text-gray-600'
    }
  }

  const handleDownload = (reportId: string) => {
    // In production, this would trigger API call to generate and download report
    console.log('Downloading report:', reportId)
    alert('Report download started!')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <p className="text-gray-500 mt-1">Generate and download compliance reports</p>
        </div>
      </div>

      {/* Date Range Filter */}
      <div className="bg-white rounded-xl shadow-sm border p-4 flex items-center gap-4">
        <Calendar className="w-5 h-5 text-gray-400" />
        <div className="flex items-center gap-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">From</label>
            <input
              type="date"
              value={format(new Date(dateRange.from), 'yyyy-MM-dd')}
              onChange={(e) => setDateRange({ ...dateRange, from: e.target.value })}
              className="px-3 py-2 border rounded-lg text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">To</label>
            <input
              type="date"
              value={format(new Date(dateRange.to), 'yyyy-MM-dd')}
              onChange={(e) => setDateRange({ ...dateRange, to: e.target.value })}
              className="px-3 py-2 border rounded-lg text-sm"
            />
          </div>
        </div>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reports.map((report) => (
          <div
            key={report.id}
            className="bg-white rounded-xl shadow-sm border p-6 hover:border-primary-200 hover:shadow-md transition-all cursor-pointer"
            onClick={() => setSelectedReport(report.id)}
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${getTypeColor(report.type)}`}>
                {getTypeIcon(report.type)}
              </div>
              <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs capitalize">
                {report.type}
              </span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">{report.name}</h3>
            <p className="text-sm text-gray-500 mb-4">{report.description}</p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">
                Last: {format(new Date(report.lastGenerated), 'dd MMM yyyy')}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleDownload(report.id)
                }}
                className="flex items-center gap-1 text-primary-600 hover:text-primary-700 text-sm font-medium"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Stats */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4">Quick Statistics</h2>
        <div className="grid grid-cols-4 gap-6">
          <div className="text-center">
            <p className="text-3xl font-bold text-primary-600">24</p>
            <p className="text-sm text-gray-500 mt-1">Total Filings</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold text-success-600">18</p>
            <p className="text-sm text-gray-500 mt-1">Completed</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold text-warning-600">4</p>
            <p className="text-sm text-gray-500 mt-1">Pending</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold text-danger-600">2</p>
            <p className="text-sm text-gray-500 mt-1">Overdue</p>
          </div>
        </div>
      </div>
    </div>
  )
}