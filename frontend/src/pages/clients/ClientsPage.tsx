import { useState, useEffect } from 'react'
import { api } from '../../context/AuthContext'
import { Users, Plus, Search, Building2, Mail, Phone } from 'lucide-react'

interface Client {
  id: number
  name: string
  email: string
  gstin?: string
  pan?: string
  entity_type: string
  compliance_types: Record<string, boolean>
  is_active: boolean
  created_at: string
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchClients()
  }, [])

  const fetchClients = async () => {
    try {
      const response = await api.get('/users/clients')
      setClients(response.data)
    } catch (error) {
      console.error('Failed to fetch clients:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredClients = clients.filter(client => 
    client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.email.toLowerCase().includes(searchTerm.toLowerCase())
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Clients</h1>
          <p className="text-gray-500 mt-1">Manage firm clients and their compliance</p>
        </div>
        <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Client
        </button>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search clients..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredClients.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500">
            <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No clients found</p>
          </div>
        ) : (
          filteredClients.map((client) => (
            <div key={client.id} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:border-primary-200 hover:shadow-md transition-all">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-secondary-100 flex items-center justify-center">
                  <Building2 className="w-6 h-6 text-primary-600" />
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  client.is_active ? 'bg-success-100 text-success-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {client.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <h3 className="font-semibold text-gray-900">{client.name}</h3>
              <p className="text-sm text-gray-500 capitalize mt-1">{client.entity_type.replace('_', ' ')}</p>
              
              <div className="mt-4 space-y-2">
                <p className="text-sm text-gray-600 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-gray-400" />
                  {client.email}
                </p>
                {client.gstin && (
                  <p className="text-sm text-gray-600 flex items-center gap-2">
                    <span className="text-gray-400 text-xs font-medium">GST</span>
                    {client.gstin}
                  </p>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-500">Compliance Types</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {Object.entries(client.compliance_types || {}).map(([type, enabled]) => (
                    enabled && (
                      <span key={type} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs capitalize">
                        {type}
                      </span>
                    )
                  ))}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}