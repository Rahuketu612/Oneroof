import { useState } from 'react'
import { Check, X, Clock, Filter } from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'

interface Approval {
  id: number
  compliance_item_id: number
  approval_type: string
  status: string
  compliance_name?: string
  client_name?: string
  created_at: string
  approved_at?: string
  comments?: string
  ip_address?: string
}

export default function ApprovalsPage() {
  const [filter, setFilter] = useState<'pending' | 'approved' | 'rejected' | 'all'>('pending')
  const [approvals] = useState<Approval[]>([
    { id: 1, compliance_item_id: 1, approval_type: 'client_approval', status: 'pending', compliance_name: 'GSTR-3B Filing - May 2026', client_name: 'Tech Solutions', created_at: new Date().toISOString() },
    { id: 2, compliance_item_id: 2, approval_type: 'manager_approval', status: 'pending', compliance_name: 'GSTR-1 Filing - May 2026', client_name: 'Green Earth', created_at: new Date().toISOString() },
    { id: 3, compliance_item_id: 3, approval_type: 'client_approval', status: 'approved', compliance_name: 'TDS Q1 2026', client_name: 'Metro Logistics', created_at: new Date().toISOString(), approved_at: new Date().toISOString() },
  ])

  const pending = approvals.filter(a => a.status === 'pending').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Approvals</h1>
          <p className="text-gray-500 mt-1">{pending > 0 ? `${pending} pending` : 'All caught up'}</p>
        </div>
        <div className="flex gap-2 bg-white rounded-lg p-1 border">
          {(['pending', 'approved', 'rejected', 'all'] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)} className={`px-4 py-2 rounded text-sm ${filter === f ? 'bg-primary-100 text-primary-700' : 'text-gray-600'}`}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        {approvals.filter(a => filter === 'all' || a.status === filter).map((approval) => (
          <div key={approval.id} className="p-6 border-b last:border-0 hover:bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${approval.status === 'pending' ? 'bg-warning-100' : approval.status === 'approved' ? 'bg-success-100' : 'bg-danger-100'}`}>
                  {approval.status === 'pending' ? <Clock className="w-6 h-6 text-warning-600" /> : approval.status === 'approved' ? <Check className="w-6 h-6 text-success-600" /> : <X className="w-6 h-6 text-danger-600" />}
                </div>
                <div>
                  <h3 className="font-semibold">{approval.compliance_name}</h3>
                  <p className="text-sm text-gray-500">{approval.client_name} • {approval.approval_type.replace('_', ' ')}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className={`px-2 py-1 rounded-full text-xs ${approval.status === 'approved' ? 'bg-success-100 text-success-700' : approval.status === 'rejected' ? 'bg-danger-100 text-danger-700' : 'bg-warning-100 text-warning-700'}`}>
                  {approval.status}
                </span>
                {approval.status === 'pending' && (
                  <div className="flex gap-2">
                    <button className="px-4 py-2 bg-success-600 text-white rounded-lg hover:bg-success-700">Approve</button>
                    <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">Reject</button>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}