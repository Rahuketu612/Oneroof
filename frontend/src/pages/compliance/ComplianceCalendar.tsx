import { useState, useEffect } from 'react'
import { api } from '../../context/AuthContext'
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay } from 'date-fns'

interface CalendarItem {
  id: number
  name: string
  client: string
  compliance_type: string
  due_date: string
  due_day: number
  status: string
  priority: string
}

interface CalendarDay {
  date: Date
  items: CalendarItem[]
  isCurrentMonth: boolean
}

export default function ComplianceCalendar() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [calendarData, setCalendarData] = useState<CalendarItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedItem, setSelectedItem] = useState<CalendarItem | null>(null)

  useEffect(() => {
    fetchCalendarData()
  }, [currentDate])

  const fetchCalendarData = async () => {
    setIsLoading(true)
    try {
      const year = currentDate.getFullYear()
      const month = currentDate.getMonth() + 1
      const response = await api.get('/compliance/calendar', {
        params: { year, month }
      })
      setCalendarData(response.data.items || [])
    } catch (error) {
      console.error('Failed to fetch calendar:', error)
      // Use sample data for demo
      setCalendarData(generateSampleData())
    } finally {
      setIsLoading(false)
    }
  }

  const generateSampleData = (): CalendarItem[] => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth() + 1
    return [
      { id: 1, name: 'GSTR-1 Filing', client: 'Tech Solutions', compliance_type: 'gst', due_date: `${year}-${month.toString().padStart(2, '0')}-10`, due_day: 10, status: 'pending', priority: 'high' },
      { id: 2, name: 'GSTR-3B Filing', client: 'Tech Solutions', compliance_type: 'gst', due_date: `${year}-${month.toString().padStart(2, '0')}-15`, due_day: 15, status: 'in_progress', priority: 'high' },
      { id: 3, name: 'TDS Filing', client: 'Metro Logistics', compliance_type: 'tds', due_date: `${year}-${month.toString().padStart(2, '0')}-20`, due_day: 20, status: 'pending', priority: 'normal' },
    ]
  }

  const getMonthData = (): CalendarDay[] => {
    const start = startOfMonth(currentDate)
    const end = endOfMonth(currentDate)
    const days = eachDayOfInterval({ start, end })
    
    // Pad start of month
    const startDay = start.getDay()
    const paddedDays: CalendarDay[] = []
    
    // Add empty days for padding
    for (let i = 0; i < startDay; i++) {
      const prevDate = new Date(start)
      prevDate.setDate(prevDate.getDate() - (startDay - i))
      paddedDays.push({
        date: prevDate,
        items: [],
        isCurrentMonth: false
      })
    }
    
    // Add actual days
    days.forEach(day => {
      const dayItems = calendarData.filter(item => item.due_day === day.getDate())
      paddedDays.push({
        date: day,
        items: dayItems,
        isCurrentMonth: true
      })
    })
    
    return paddedDays
  }

  const calendarDays = getMonthData()

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate)
    if (direction === 'prev') {
      newDate.setMonth(newDate.getMonth() - 1)
    } else {
      newDate.setMonth(newDate.getMonth() + 1)
    }
    setCurrentDate(newDate)
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-danger-100 text-danger-700 border-danger-300'
      case 'high': return 'bg-warning-100 text-warning-700 border-warning-300'
      case 'normal': return 'bg-primary-100 text-primary-700 border-primary-300'
      case 'low': return 'bg-gray-100 text-gray-600 border-gray-300'
      default: return 'bg-gray-100 text-gray-600 border-gray-300'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'filed': return '✓'
      case 'completed': return '✓'
      case 'in_progress': return '●'
      case 'overdue': return '!'
      default: return '○'
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <CalendarIcon className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">
            Compliance Calendar
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigateMonth('prev')}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <span className="text-lg font-medium min-w-[150px] text-center">
            {format(currentDate, 'MMMM yyyy')}
          </span>
          <button
            onClick={() => navigateMonth('next')}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Days of week header */}
      <div className="grid grid-cols-7 gap-2 mb-2">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
            {day}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-2">
        {calendarDays.map((day, index) => (
          <div
            key={index}
            className={`
              min-h-[100px] p-2 rounded-lg border
              ${day.isCurrentMonth ? 'bg-white border-gray-200' : 'bg-gray-50 border-gray-100'}
              ${isSameDay(day.date, new Date()) ? 'ring-2 ring-primary-500' : ''}
            `}
          >
            <div className={`text-sm font-medium mb-1 ${
              day.isCurrentMonth ? 'text-gray-700' : 'text-gray-400'
            }`}>
              {format(day.date, 'd')}
            </div>
            <div className="space-y-1">
              {day.items.map(item => (
                <button
                  key={item.id}
                  onClick={() => setSelectedItem(item)}
                  className={`
                    w-full text-left text-xs p-1.5 rounded border
                    ${getPriorityColor(item.priority)}
                    truncate
                  `}
                >
                  <span className="mr-1">{getStatusIcon(item.status)}</span>
                  {item.name.split(' ')[0]}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Selected item modal */}
      {selectedItem && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">{selectedItem.name}</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-500">Client:</span>
                <span className="font-medium">{selectedItem.client}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Type:</span>
                <span className="capitalize">{selectedItem.compliance_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Due Date:</span>
                <span className="font-medium">{selectedItem.due_date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Status:</span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  selectedItem.status === 'filed' ? 'bg-success-100 text-success-700' :
                  selectedItem.status === 'overdue' ? 'bg-danger-100 text-danger-700' :
                  'bg-primary-100 text-primary-700'
                }`}>
                  {selectedItem.status.replace('_', ' ')}
                </span>
              </div>
            </div>
            <button
              onClick={() => setSelectedItem(null)}
              className="mt-6 w-full py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}