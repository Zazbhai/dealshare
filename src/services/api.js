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
    // Only log out on 401 from authentication endpoints, not API endpoints
    // API endpoints (balance, price, etc.) can return 401 for invalid API keys
    // which should not log the user out
    if (error.response?.status === 401) {
      const url = error.config?.url || ''
      // Only log out if it's an auth-related endpoint
      if (url.includes('/auth/') || url.includes('/admin/')) {
        console.log('[AUTH] Authentication failed, logging out...')
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
      // For other endpoints (balance, price, etc.), just reject the promise
      // Don't log out - these are API key errors, not auth errors
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
    // Preserve the exact error message from the backend
    let errorMessage = error.response?.data?.error || error.message

    // Only provide default messages for network/connection errors
    if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error')) {
      errorMessage = `Cannot connect to backend server. Make sure the server is running on ${import.meta.env.VITE_BACKEND_URL || window.location.origin.replace(':3000', ':5000')}`
    } else if (error.code === 'ECONNABORTED' || error.timeout) {
      errorMessage = 'Request timeout - the server is taking too long to respond'
    } else if (error.response?.status === 0) {
      errorMessage = 'Connection failed - check if backend server is running'
    }
    // For 400 and 401, use the exact error message from backend
    // 400 = API key not configured
    // 401 = Invalid API key

    console.error('getBalance error:', {
      message: error.message,
      code: error.code,
      status: error.response?.status,
      error: error.response?.data
    })

    return {
      success: false,
      error: errorMessage,
      status: error.response?.status  // Include status code for frontend to distinguish
    }
  }
}

export const getGlobalSettings = async () => {
  try {
    const response = await api.get('/global-settings')
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message
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
    // Preserve the exact error message from the backend
    let errorMessage = error.response?.data?.error || error.message

    // Only provide default messages for network/connection errors
    if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error')) {
      errorMessage = `Cannot connect to backend server. Make sure the server is running on ${import.meta.env.VITE_BACKEND_URL || window.location.origin.replace(':3000', ':5000')}`
    } else if (error.code === 'ECONNABORTED' || error.timeout) {
      errorMessage = 'Request timeout - the server is taking too long to respond'
    }
    // For 400 and 401, use the exact error message from backend
    // 400 = API key not configured
    // 401 = Invalid API key

    console.error('getPrice error:', {
      message: error.message,
      code: error.code,
      status: error.response?.status,
      error: error.response?.data
    })

    return {
      success: false,
      error: errorMessage,
      status: error.response?.status  // Include status code for frontend to distinguish
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
  console.log('[DEBUG API] startAutomation called with formData:', formData)

  try {
    // Automation start might take time, use longer timeout
    const automationApi = axios.create({
      baseURL: '/api',
      timeout: 60000, // 1 minute for automation start
    })

    const token = localStorage.getItem('token')
    console.log('[DEBUG API] Token present:', !!token)

    if (token) {
      automationApi.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }

    const requestData = {
      name: formData.name,
      house_flat_no: formData.houseFlatNo,
      landmark: formData.landmark,
      total_orders: formData.totalOrders || '1',
      max_parallel_windows: formData.maxParallelWindows || '1',
      products: formData.products ? formData.products.map(p => ({
        url: p.url ? p.url.trim() : '',
        quantity: parseInt(p.quantity) || 1
      })) : [],
      order_all: formData.orderAll !== undefined ? formData.orderAll : false,
      retry_orders: formData.retryOrders !== undefined ? formData.retryOrders : false,
      latitude: formData.latitude || '26.994880',
      longitude: formData.longitude || '75.774836',
      select_location: formData.selectLocation !== undefined ? formData.selectLocation : true,
      search_input: formData.searchInput || 'chinu juice center',
      location_text: formData.locationText || 'Chinu Juice Center, Jaswant Nagar, mod, Khatipura, Jaipur, Rajasthan, India'
    }

    console.log('[DEBUG API] Making POST request to /api/automation/start')
    console.log('[DEBUG API] Request data:', requestData)

    const response = await automationApi.post('/automation/start', requestData)

    console.log('[DEBUG API] Response received:', {
      status: response.status,
      data: response.data
    })

    return response.data
  } catch (error) {
    console.error('[DEBUG API] Error in startAutomation:', error)
    console.error('[DEBUG API] Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      statusText: error.response?.statusText
    })

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

export const getAutomationStatus = async () => {
  try {
    const response = await api.get('/automation/status')
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.message
    }
  }
}

// Reports API
export const getOrdersReport = async () => {
  try {
    const response = await api.get('/orders/report')
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.message
    }
  }
}

export const downloadOrdersReport = async () => {
  try {
    const response = await api.get('/orders/download', {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'my_orders.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error.message
    }
  }
}

// Logs API
export const getLogsList = async () => {
  try {
    const response = await api.get('/logs/list')
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.message
    }
  }
}



export const viewFailedLog = async (filename) => {
  try {
    const response = await api.get('/logs/failed', {
      params: { filename }
    })
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.message
    }
  }
}


export const viewScreenshot = async (filename) => {
  try {
    const response = await api.get('/screenshots/view', {
      params: { filename },
      responseType: 'blob'
    })
    return { success: true, blob: response.data }
  } catch (error) {
    return { success: false, error: error.message }
  }
}

export const viewLogFile = async (filename) => {
  try {
    const response = await api.get(`/logs/view/${filename}`)
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.message
    }
  }
}

export const downloadLogFile = async (filename) => {
  try {
    const response = await api.get(`/logs/download/${filename}`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error.message
    }
  }
}

