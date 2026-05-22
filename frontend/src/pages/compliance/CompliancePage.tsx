import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../context/AuthContext'
import { FileCheck, Search, Filter, Plus, Clock, CheckCircle2, AlertTriangle } from 'lucide-react'
import { format } from 'date-fns'

interface ComplianceItem {
  id: number
  workspace_id: number
  name: string
  compliance_type: string
  period: string
  status: string
  priority: string
  due_date: string
  created_at: string
}

export default function CompliancePage() {
  const [items, setItems] = useState<ComplianceItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchComplianceItems()
  }, [filter])

  const fetchComplianceItems = async () => {
    try {
      const params: any = {}
      if (filter !== 'all') params.status = filter
      if (filter === 'overdue') {
        params.overdue = true
        delete params.status
      }
      const response = await api.get('/compliance/items', { params })
      setItems(response.data)
    } catch (error) {
      console.error('Failed to fetch compliance items:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredItems = items.filter(item => 
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const statusFilters = [
    { id: 'all', label: 'All' },
    { id: 'pending', label: 'Pending' },
    { id: 'in_progress', label: 'In Progress' },
    { id: 'filed', label: 'Filed' },
    { id: 'overdue', label: 'Overdue' },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Compliance</h1>
          <p className="text-gray-500 mt-1">Manage all compliance items and deadlines</p>
        </div>
        <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Compliance
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 bg-white rounded-lg p-1 border border-gray-200">
          {statusFilters.map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                filter === f.id
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search compliance..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      {/* Items List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="divide-y divide-gray-100">
          {filteredItems.length === 0 ? (
            <div className="p-12 text-center">
              <FileCheck className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500">No compliance items found</p>
            </div>
          ) : (
            filteredItems.map((item) => {
              const isOverdue = new Date(item.due_date) < new Date() && !['filed', 'completed'].includes(item.status)
              return (
                <div key={item.id} className="p-4 hover:bg-gray-50 flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    isOverdue ? 'bg-danger-100' : 'bg-primary-100'
                  }`}>
                    {isOverdue ? (
                      <AlertTriangle className="w-5 h-5 text-danger-600" />
                    ) : (
                      <FileCheck className="w-5 h-5 text-primary-600" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.name}</p>
                    <p className="text-sm text-gray-500 capitalize">
                      {item.compliance_type} • {item.period}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    item.status === 'filed' ? 'bg-success-100 text-success-700' :
                    item.status === 'overdue' || isOverdue ? 'bg-danger-100 text-danger-700' :
                    item.status === 'in_progress' ? 'bg-primary-100 text-primary-700' :
                    item.status === 'review' ? 'bg-secondary-100 text-secondary-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {isOverdue ? 'Overdue' : item.status.replace('_', ' ')}
                  </span>
                  <div className="text-right min-w-[100px]">
                    <p className={`text-sm font-medium ${isOverdue ? 'text-danger-600' : 'text-gray-600'}`}>
                      {format(new Date(item.due_date), 'MMM d, yyyy')}
                    </p>
                    <p className="text-xs text-gray-400">
                      {item.priority === 'urgent' ? 'Urgent' : item.priority}
                    </p>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}