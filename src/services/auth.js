import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 minutes for long operations
})

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 errors (unauthorized) and timeout errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Only log out on 401 from authentication endpoints
    // The auth service is only used for auth endpoints, so we can log out on any 401
    if (error.response?.status === 401) {
      console.log('[AUTH] Authentication failed, logging out...')
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    // Handle timeout errors
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      error.timeout = true
      error.message = 'Request timeout - the server is taking too long to respond'
    }
    return Promise.reject(error)
  }
)

export const login = async (username, password) => {
  try {
    const response = await api.post('/auth/login', { username, password })
    return response.data
  } catch (error) {
    let errorMessage = error.response?.data?.error || error.message
    
    // Provide more detailed error messages
    if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error')) {
      errorMessage = 'Cannot connect to backend server. Make sure the server is running on http://localhost:5000'
    } else if (error.code === 'ECONNABORTED' || error.timeout) {
      errorMessage = 'Request timeout - the server is taking too long to respond'
    } else if (error.response?.status === 0) {
      errorMessage = 'Connection failed - check if backend server is running'
    }
    
    console.error('Login error:', {
      message: error.message,
      code: error.code,
      status: error.response?.status,
      url: error.config?.url,
      baseURL: error.config?.baseURL
    })
    
    return {
      success: false,
      error: errorMessage
    }
  }
}

export const getCurrentUser = async () => {
  try {
    const response = await api.get('/auth/me')
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message
    }
  }
}

export const updateSettings = async (settings) => {
  try {
    const response = await api.put('/auth/settings', settings)
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message
    }
  }
}

