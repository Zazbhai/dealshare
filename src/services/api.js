import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 minutes for OTP polling
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
    if (error.response?.status === 401) {
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

export const getBalance = async () => {
  try {
    const response = await api.get('/balance')
    return response.data
  } catch (error) {
    let errorMessage = error.response?.data?.error || error.message
    
    // Provide more detailed error messages
    if (error.response?.status === 400) {
      errorMessage = error.response?.data?.error || 'API key not configured. Please set your API key in Settings.'
    } else if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error')) {
      errorMessage = 'Cannot connect to backend server. Make sure the server is running on http://localhost:5000'
    } else if (error.code === 'ECONNABORTED' || error.timeout) {
      errorMessage = 'Request timeout - the server is taking too long to respond'
    } else if (error.response?.status === 0) {
      errorMessage = 'Connection failed - check if backend server is running'
    }
    
    console.error('getBalance error:', {
      message: error.message,
      code: error.code,
      status: error.response?.status,
      error: error.response?.data
    })
    
    return {
      success: false,
      error: errorMessage
    }
  }
}

export const getPrice = async (country = '22', operator = '1', service = 'pfk') => {
  try {
    const response = await api.get('/price', {
      params: { country, operator, service }
    })
    return response.data
  } catch (error) {
    let errorMessage = error.response?.data?.error || error.message
    
    if (error.response?.status === 400) {
      errorMessage = error.response?.data?.error || 'API key not configured. Please set your API key in Settings.'
    } else if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error')) {
      errorMessage = 'Cannot connect to backend server. Make sure the server is running on http://localhost:5000'
    } else if (error.code === 'ECONNABORTED' || error.timeout) {
      errorMessage = 'Request timeout - the server is taking too long to respond'
    }
    
    console.error('getPrice error:', {
      message: error.message,
      code: error.code,
      status: error.response?.status,
      error: error.response?.data
    })
    
    return {
      success: false,
      error: errorMessage
    }
  }
}

export const getPrices = async (country = '22', operator = '1') => {
  try {
    const response = await api.get('/prices', {
      params: { country, operator }
    })
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.message
    }
  }
}

export const getNumber = async (service = 'pfk', country = '22', operator = '1') => {
  try {
    const response = await api.post('/number', {
      service,
      country,
      operator
    })
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.message
    }
  }
}

export const getOTP = async (requestId, timeout = 120.0, pollInterval = 2.0) => {
  try {
    // Create a separate axios instance with longer timeout for OTP polling
    const otpApi = axios.create({
      baseURL: '/api',
      timeout: 150000, // 2.5 minutes for OTP polling (backend polls for 2 minutes)
    })
    
    // Add token to OTP request
    const token = localStorage.getItem('token')
    if (token) {
      otpApi.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
    
    const response = await otpApi.post('/otp', {
      request_id: requestId,
      timeout,
      poll_interval: pollInterval
    })
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message || 'Request timeout'
    }
  }
}

export const cancelNumber = async (requestId) => {
  try {
    const response = await api.post('/cancel', {
      request_id: requestId
    })
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.message
    }
  }
}

export const startAutomation = async (formData) => {
  try {
    // Automation start might take time, use longer timeout
    const automationApi = axios.create({
      baseURL: '/api',
      timeout: 60000, // 1 minute for automation start
    })
    
    const token = localStorage.getItem('token')
    if (token) {
      automationApi.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
    
    const response = await automationApi.post('/automation/start', {
      name: formData.name,
      house_flat_no: formData.houseFlatNo,
      landmark: formData.landmark
    })
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message || 'Request timeout'
    }
  }
}

export const stopAutomation = async () => {
  try {
    const response = await api.post('/automation/stop')
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.message
    }
  }
}

