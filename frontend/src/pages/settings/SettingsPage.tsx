import { useState } from 'react'
import { User, Bell, Shield, Building2, Database, Key, Save } from 'lucide-react'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile')
  const [settings, setSettings] = useState({
    firmName: 'Sharma & Associates',
    email: 'partner@sharmaassociates.com',
    phone: '+91 9876543210',
    gstin: '27AAACH1234C1ZB',
    notifications: { email: true, push: true, reminderDays: [5, 2, 0] },
    security: { mfaRequired: true, sessionTimeout: 30 },
  })

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'firm', label: 'Firm Details', icon: Building2 },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Manage your account and firm settings</p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="w-64 bg-white rounded-xl shadow-sm border p-4 h-fit">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                activeTab === tab.id ? 'bg-primary-50 text-primary-700' : 'hover:bg-gray-50'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 bg-white rounded-xl shadow-sm border p-6">
          {activeTab === 'profile' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold">Profile Settings</h2>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">First Name</label>
                  <input type="text" defaultValue="Rajesh" className="w-full px-4 py-2 border rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Last Name</label>
                  <input type="text" defaultValue="Sharma" className="w-full px-4 py-2 border rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                  <input type="email" defaultValue="partner@sharmaassociates.com" className="w-full px-4 py-2 border rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                  <input type="tel" defaultValue="+91 9876543210" className="w-full px-4 py-2 border rounded-lg" />
                </div>
              </div>
              <button className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2">
                <Save className="w-4 h-4" /> Save Changes
              </button>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold">Notification Preferences</h2>
              <div className="space-y-4">
                <label className="flex items-center gap-3">
                  <input type="checkbox" defaultChecked className="w-5 h-5 rounded" />
                  <span>Email notifications</span>
                </label>
                <label className="flex items-center gap-3">
                  <input type="checkbox" defaultChecked className="w-5 h-5 rounded" />
                  <span>Push notifications</span>
                </label>
                <label className="flex items-center gap-3">
                  <input type="checkbox" defaultChecked className="w-5 h-5 rounded" />
                  <span>Reminder notifications</span>
                </label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Reminder Days</label>
                <input type="text" defaultValue="5, 2, 0" className="w-full px-4 py-2 border rounded-lg" />
                <p className="text-sm text-gray-500 mt-1">Comma-separated days before deadline</p>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold">Security Settings</h2>
              <div className="space-y-4">
                <label className="flex items-center justify-between">
                  <span>Require MFA for all users</span>
                  <input type="checkbox" defaultChecked className="w-5 h-5 rounded" />
                </label>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Session Timeout (minutes)</label>
                  <input type="number" defaultValue="30" className="w-full px-4 py-2 border rounded-lg" />
                </div>
              </div>
              <button className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                Update Security Settings
              </button>
            </div>
          )}

          {activeTab === 'firm' && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold">Firm Details</h2>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Firm Name</label>
                  <input type="text" defaultValue="Sharma & Associates" className="w-full px-4 py-2 border rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">GSTIN</label>
                  <input type="text" defaultValue="27AAACH1234C1ZB" className="w-full px-4 py-2 border rounded-lg" />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
                  <textarea defaultValue="101, Trade Center, MG Road, Mumbai - 400001" className="w-full px-4 py-2 border rounded-lg" rows={3} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}