import { useState, useEffect, useParams } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../../context/AuthContext'
import { 
  Building2, FileCheck, FolderOpen, AlertCircle, 
  Users, Calendar, Clock, CheckCircle2, ArrowLeft
} from 'lucide-react'
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
  current_step: number
  workflow_steps: any[]
  created_at: string
}

interface DocumentRequest {
  id: number
  compliance_item_id: number
  title: string
  status: string
  due_date: string
}

export default function WorkspaceDetailPage() {
  const { id } = useParams()
  const [workspace, setWorkspace] = useState<any>(null)
  const [complianceItems, setComplianceItems] = useState<ComplianceItem[]>([])
  const [pendingRequests, setPendingRequests] = useState<DocumentRequest[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'compliance' | 'documents' | 'notices'>('compliance')

  useEffect(() => {
    if (id) {
      fetchWorkspaceDetails()
    }
  }, [id])

  const fetchWorkspaceDetails = async () => {
    try {
      const wsResponse = await api.get(`/workspaces/${id}`)
      setWorkspace(wsResponse.data)
      
      // Fetch compliance items for this workspace
      const compResponse = await api.get('/compliance/items', {
        params: { workspace_id: id }
      })
      setComplianceItems(compResponse.data)
      
      // Fetch pending document requests
      const reqResponse = await api.get('/compliance/requests', {
        params: { compliance_item_id: id }
      })
      setPendingRequests(reqResponse.data)
    } catch (error) {
      console.error('Failed to fetch workspace details:', error)
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

  const stats = {
    total: complianceItems.length,
    pending: complianceItems.filter(c => c.status === 'pending').length,
    inProgress: complianceItems.filter(c => c.status === 'in_progress').length,
    completed: complianceItems.filter(c => ['filed', 'completed'].includes(c.status)).length,
    overdue: complianceItems.filter(c => new Date(c.due_date) < new Date() && c.status !== 'filed').length,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/workspaces" className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft className="w-5 h-5 text-gray-500" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{workspace?.name || 'Workspace'}</h1>
          <p className="text-gray-500">Compliance management workspace</p>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          workspace?.is_frozen ? 'bg-danger-100 text-danger-700' : 'bg-success-100 text-success-700'
        }`}>
          {workspace?.is_frozen ? 'Frozen' : 'Active'}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: 'Total', value: stats.total, icon: FileCheck, color: 'primary' },
          { label: 'Pending', value: stats.pending, icon: Clock, color: 'warning' },
          { label: 'In Progress', value: stats.inProgress, icon: Calendar, color: 'secondary' },
          { label: 'Completed', value: stats.completed, icon: CheckCircle2, color: 'success' },
          { label: 'Overdue', value: stats.overdue, icon: AlertCircle, color: 'danger' },
        ].map((stat, index) => (
          <div key={index} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center bg-${stat.color}-100 mb-3`}>
              <stat.icon className={`w-4 h-4 text-${stat.color}-600`} />
            </div>
            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            <p className="text-sm text-gray-500">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-8">
          {[
            { id: 'compliance', label: 'Compliance', icon: FileCheck },
            { id: 'documents', label: 'Documents', icon: FolderOpen },
            { id: 'notices', label: 'Notices', icon: AlertCircle },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        {activeTab === 'compliance' && (
          <div className="divide-y divide-gray-100">
            {complianceItems.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <FileCheck className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No compliance items yet</p>
              </div>
            ) : (
              complianceItems.map((item) => (
                <div key={item.id} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.name}</p>
                    <p className="text-sm text-gray-500 capitalize">{item.compliance_type} • {item.period}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      item.status === 'filed' ? 'bg-success-100 text-success-700' :
                      item.status === 'overdue' ? 'bg-danger-100 text-danger-700' :
                      item.status === 'in_progress' ? 'bg-primary-100 text-primary-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {item.status.replace('_', ' ')}
                    </span>
                    <span className="text-sm text-gray-500">
                      Due {format(new Date(item.due_date), 'MMM d')}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="p-8 text-center text-gray-500">
            <FolderOpen className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Document management coming soon</p>
          </div>
        )}

        {activeTab === 'notices' && (
          <div className="p-8 text-center text-gray-500">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Notice management coming soon</p>
          </div>
        )}
      </div>
    </div>
  )
}