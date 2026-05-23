import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../context/AuthContext'
import { motion } from 'framer-motion'
import { FileCheck, Search, Filter, Plus, Clock, CheckCircle2, AlertTriangle, Calendar, X } from 'lucide-react'
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

// Status colors and config
const statusConfig: Record<string, { bg: string, text: string, label: string }> = {
  pending: { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Pending' },
  in_progress: { bg: 'bg-blue-100', text: 'text-blue-600', label: 'In Progress' },
  review: { bg: 'bg-purple-100', text: 'text-purple-600', label: 'Review' },
  approved: { bg: 'bg-emerald-100', text: 'text-emerald-600', label: 'Approved' },
  filed: { bg: 'bg-emerald-100', text: 'text-emerald-600', label: 'Filed' },
}

// Compliance type icons and colors
const typeConfig: Record<string, { bg: string, text: string }> = {
  gst: { bg: 'bg-blue-100', text: 'text-blue-600' },
  tds: { bg: 'bg-purple-100', text: 'text-purple-600' },
  income_tax: { bg: 'bg-amber-100', text: 'text-amber-600' },
  roc: { bg: 'bg-pink-100', text: 'text-pink-600' },
}

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.05 } }
}

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0 }
}

export default function CompliancePage() {
  const [items, setItems] = useState<ComplianceItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('list')

  useEffect(() => {
    fetchComplianceItems()
  }, [filter])

  const fetchComplianceItems = async () => {
    setIsLoading(true)
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
      // Use sample data
      setItems(generateSampleData())
    } finally {
      setIsLoading(false)
    }
  }

  const generateSampleData = (): ComplianceItem[] => [
    { id: 1, workspace_id: 1, name: 'GSTR-3B Filing - May 2026', compliance_type: 'gst', period: 'May 2026', status: 'pending', priority: 'high', due_date: '2026-05-20', created_at: '2026-05-01' },
    { id: 2, workspace_id: 1, name: 'GSTR-1 Filing - May 2026', compliance_type: 'gst', period: 'May 2026', status: 'in_progress', priority: 'high', due_date: '2026-05-10', created_at: '2026-05-01' },
    { id: 3, workspace_id: 2, name: 'TDS Quarterly Return - Q1 2026', compliance_type: 'tds', period: 'Q1 2026', status: 'review', priority: 'normal', due_date: '2026-05-31', created_at: '2026-04-15' },
    { id: 4, workspace_id: 3, name: 'ITR Filing - AY 2025-26', compliance_type: 'income_tax', period: 'AY 2025-26', status: 'pending', priority: 'urgent', due_date: '2026-07-31', created_at: '2026-04-01' },
    { id: 5, workspace_id: 1, name: 'ROC Annual Return - FY 2025', compliance_type: 'roc', period: 'FY 2025', status: 'filed', priority: 'normal', due_date: '2026-04-30', created_at: '2026-03-15' },
    { id: 6, workspace_id: 2, name: 'GST Annual Return - FY 2025', compliance_type: 'gst', period: 'FY 2025', status: 'in_progress', priority: 'high', due_date: '2026-06-30', created_at: '2026-05-01' },
  ]

  const filteredItems = items.filter(item => 
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const statusFilters = [
    { id: 'all', label: 'All', count: items.length },
    { id: 'pending', label: 'Pending', count: items.filter(i => i.status === 'pending').length },
    { id: 'in_progress', label: 'In Progress', count: items.filter(i => i.status === 'in_progress').length },
    { id: 'review', label: 'Review', count: items.filter(i => i.status === 'review').length },
    { id: 'filed', label: 'Filed', count: items.filter(i => i.status === 'filed').length },
  ]

  const getDaysUntilDue = (dueDate: string) => {
    const due = new Date(dueDate)
    const today = new Date()
    return Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  }

  const getDueStatus = (item: ComplianceItem) => {
    const days = getDaysUntilDue(item.due_date)
    if (item.status === 'filed') return 'safe'
    if (days < 0) return 'overdue'
    if (days <= 3) return 'urgent'
    if (days <= 7) return 'soon'
    return 'normal'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading compliance items...</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div 
      className="space-y-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Compliance</h1>
          <p className="text-gray-500 mt-1">Manage all compliance items and deadlines</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 rounded text-sm ${viewMode === 'list' ? 'bg-white shadow-sm font-medium' : 'text-gray-600'}`}
            >
              List
            </button>
            <button
              onClick={() => setViewMode('kanban')}
              className={`px-3 py-1.5 rounded text-sm ${viewMode === 'kanban' ? 'bg-white shadow-sm font-medium' : 'text-gray-600'}`}
            >
              Kanban
            </button>
          </div>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 shadow-sm">
            <Plus className="w-4 h-4" />
            Add Compliance
          </button>
        </div>
      </motion.div>

      {/* Stats Bar */}
      <motion.div variants={itemVariants} className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <FileCheck className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{items.length}</p>
              <p className="text-sm text-gray-500">Total Items</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{items.filter(i => i.status === 'filed').length}</p>
              <p className="text-sm text-gray-500">Filed</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <Clock className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{items.filter(i => getDueStatus(i) === 'soon').length}</p>
              <p className="text-sm text-gray-500">Due Soon</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{items.filter(i => getDueStatus(i) === 'overdue').length}</p>
              <p className="text-sm text-gray-500">Overdue</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div variants={itemVariants} className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 bg-white rounded-xl p-1.5 border border-gray-200 shadow-sm">
          {statusFilters.map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                filter === f.id
                  ? 'bg-blue-50 text-blue-700 shadow-sm'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              {f.label}
              <span className={`px-1.5 py-0.5 rounded-full text-xs ${
                filter === f.id ? 'bg-blue-100' : 'bg-gray-100'
              }`}>
                {f.count}
              </span>
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name, type, or period..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
          />
          {searchTerm && (
            <button 
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          )}
        </div>
      </motion.div>

      {/* Items List */}
      <motion.div variants={itemVariants} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="divide-y divide-gray-50">
          {filteredItems.length === 0 ? (
            <div className="p-16 text-center">
              <FileCheck className="w-16 h-16 mx-auto mb-4 text-gray-200" />
              <p className="text-lg font-medium text-gray-500">No compliance items found</p>
              <p className="text-sm text-gray-400 mt-1">Try adjusting your filters or search term</p>
            </div>
          ) : (
            filteredItems.map((item) => {
              const status = statusConfig[item.status] || statusConfig.pending
              const typeStyle = typeConfig[item.compliance_type] || { bg: 'bg-gray-100', text: 'text-gray-600' }
              const dueStatus = getDueStatus(item)
              const daysUntil = getDaysUntilDue(item.due_date)
              
              return (
                <motion.div 
                  key={item.id}
                  className="p-5 hover:bg-gray-50 transition-colors cursor-pointer group"
                  whileHover={{ x: 2 }
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl ${typeStyle.bg} flex items-center justify-center`}>
                      <span className={`font-semibold text-sm ${typeStyle.text}`}>
                        {item.compliance_type.toUpperCase().slice(0, 3)}
                      </span>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                          {item.name}
                        </p>
                        {item.priority === 'urgent' && (
                          <span className="px-2 py-0.5 bg-red-100 text-red-600 text-xs rounded-full font-medium">Urgent</span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                        <span className="capitalize">{item.compliance_type}</span>
                        <span>•</span>
                        <span>{item.period}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-6">
                      {/* Status */}
                      <span className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize ${status.bg} ${status.text}`}>
                        {status.label}
                      </span>

                      {/* Due Date */}
                      <div className={`w-24 text-center py-2 rounded-xl ${
                        dueStatus === 'overdue' ? 'bg-red-50' :
                        dueStatus === 'urgent' ? 'bg-amber-50' :
                        dueStatus === 'soon' ? 'bg-yellow-50' :
                        'bg-gray-50'
                      }`}>
                        <p className={`text-sm font-semibold ${
                          dueStatus === 'overdue' ? 'text-red-600' :
                          dueStatus === 'urgent' ? 'text-amber-600' :
                          'text-gray-600'
                        }`}>
                          {daysUntil < 0 ? `${Math.abs(daysUntil)}d overdue` : 
                           daysUntil === 0 ? 'Today' : 
                           `${daysUntil}d left`}
                        </p>
                        <p className="text-xs text-gray-400">
                          {format(new Date(item.due_date), 'MMM d')}
                        </p>
                      </div>

                      {/* Actions */}
                      <button className="p-2 hover:bg-gray-100 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </motion.div>
              )
            })
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}