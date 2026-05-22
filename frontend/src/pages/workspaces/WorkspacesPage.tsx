import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../context/AuthContext'
import { Building2, Plus, Search, Filter } from 'lucide-react'

interface Workspace {
  id: number
  client_id: number
  name: string
  is_active: boolean
  is_frozen: boolean
  created_at: string
}

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchWorkspaces()
  }, [])

  const fetchWorkspaces = async () => {
    try {
      const response = await api.get('/workspaces')
      setWorkspaces(response.data)
    } catch (error) {
      console.error('Failed to fetch workspaces:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredWorkspaces = workspaces.filter(w => 
    w.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

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
          <h1 className="text-2xl font-bold text-gray-900">Workspaces</h1>
          <p className="text-gray-500 mt-1">Manage client compliance workspaces</p>
        </div>
        <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Workspace
        </button>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search workspaces..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2">
          <Filter className="w-4 h-4" />
          Filters
        </button>
      </div>

      {/* Workspaces Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredWorkspaces.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500">
            <Building2 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No workspaces found</p>
            <button className="mt-4 text-primary-600 hover:text-primary-700">
              Create your first workspace
            </button>
          </div>
        ) : (
          filteredWorkspaces.map((workspace) => (
            <Link
              key={workspace.id}
              to={`/workspaces/${workspace.id}`}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:border-primary-200 hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-secondary-100 flex items-center justify-center">
                  <Building2 className="w-6 h-6 text-primary-600" />
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  workspace.is_frozen 
                    ? 'bg-danger-100 text-danger-700' 
                    : workspace.is_active 
                    ? 'bg-success-100 text-success-700' 
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {workspace.is_frozen ? 'Frozen' : workspace.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <h3 className="font-semibold text-gray-900 mt-4">{workspace.name}</h3>
              <p className="text-sm text-gray-500 mt-1">Workspace #{workspace.id}</p>
              <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between text-sm">
                <span className="text-gray-500">Created {new Date(workspace.created_at).toLocaleDateString()}</span>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}