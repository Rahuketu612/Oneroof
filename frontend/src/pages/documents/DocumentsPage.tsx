import { useState } from 'react'
import { FolderOpen, Search, Upload, FileText, Download } from 'lucide-react'

export default function DocumentsPage() {
  const [searchTerm, setSearchTerm] = useState('')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
          <p className="text-gray-500 mt-1">Version-controlled document vault</p>
        </div>
        <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2">
          <Upload className="w-4 h-4" />
          Upload Document
        </button>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12">
        <div className="text-center">
          <FolderOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Document Management</h3>
          <p className="text-gray-500 mb-6">
            Secure document vault with version control, encryption, and access tracking.
          </p>
          <div className="flex items-center justify-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <FileText className="w-4 h-4" />
              Version Control
            </span>
            <span className="flex items-center gap-1">
              <Download className="w-4 h-4" />
              Watermarking
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}