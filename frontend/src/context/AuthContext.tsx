import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import axios from 'axios'

// Types
interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  role: string
  phone?: string
  is_active: boolean
  last_login?: string
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string, firmId: number) => Promise<void>
  logout: () => void
  register: (data: any) => Promise<void>
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// API helper
const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: localStorage.getItem('token'),
    isLoading: true,
    isAuthenticated: false,
  })

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token')
      if (token) {
        try {
          const response = await api.get('/users/me')
          setState({
            user: response.data,
            token,
            isLoading: false,
            isAuthenticated: true,
          })
        } catch (error) {
          localStorage.removeItem('token')
          setState({
            user: null,
            token: null,
            isLoading: false,
            isAuthenticated: false,
          })
        }
      } else {
        setState(prev => ({ ...prev, isLoading: false }))
      }
    }
    checkAuth()
  }, [])

  const login = async (email: string, password: string, firmId: number) => {
    try {
      const response = await api.post('/users/login', { email, password }, {
        params: { firm_id: firmId }
      })
      const { access_token, user } = response.data
      
      localStorage.setItem('token', access_token)
      setState({
        user,
        token: access_token,
        isLoading: false,
        isAuthenticated: true,
      })
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed')
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setState({
      user: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,
    })
  }

  const register = async (data: any) => {
    try {
      const response = await api.post('/users/register', data)
      const { access_token, user } = response.data
      
      localStorage.setItem('token', access_token)
      setState({
        user,
        token: access_token,
        isLoading: false,
        isAuthenticated: true,
      })
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Registration failed')
    }
  }

  return (
    <AuthContext.Provider value={{ ...state, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}

// Custom hook
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Export API for use in components
export { api }