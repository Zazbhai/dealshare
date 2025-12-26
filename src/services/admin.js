import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const getAllUsers = async () => {
  try {
    const response = await api.get('/admin/users')
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message
    }
  }
}

export const createUser = async (userData) => {
  try {
    const response = await api.post('/admin/users', userData)
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message
    }
  }
}

export const updateUserSettings = async (userId, settings) => {
  try {
    const response = await api.put(`/admin/users/${userId}/settings`, settings)
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message
    }
  }
}

export const deleteUser = async (userId) => {
  try {
    const response = await api.delete(`/admin/users/${userId}`)
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message
    }
  }
}

export const getGlobalSettings = async () => {
  try {
    const response = await api.get('/admin/global-settings')
    return response.data
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message
    }
  }
}

export const updateGlobalSettings = async (settings) => {
  try {
    const response = await api.put('/admin/global-settings', settings)
    return response.data
  } catch (error) {
    console.error('updateGlobalSettings error:', {
      message: error.message,
      status: error.response?.status,
      error: error.response?.data
    })
    return {
      success: false,
      error: error.response?.data?.error || error.message || 'Failed to update global settings'
    }
  }
}

