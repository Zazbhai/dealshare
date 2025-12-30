import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { AlertCircle, CheckCircle, XCircle, RefreshCw, Globe, Server, Wifi, WifiOff } from 'lucide-react'
import axios from 'axios'

function ConnectionDebugger() {
  const [status, setStatus] = useState('checking')
  const [details, setDetails] = useState(null)
  const [loading, setLoading] = useState(false)
  const [backendUrl, setBackendUrl] = useState(import.meta.env.VITE_BACKEND_URL || window.location.origin.replace(':3000', ':5000') || 'http://localhost:5000')

  const checkConnection = async () => {
    setLoading(true)
    setStatus('checking')
    setDetails(null)

    const checks = {
      frontend: {
        url: window.location.origin,
        status: 'unknown',
        error: null
      },
      backend: {
        url: backendUrl,
        status: 'unknown',
        error: null,
        response: null
      },
      api: {
        url: `${backendUrl}/api/health`,
        status: 'unknown',
        error: null,
        response: null
      },
      proxy: {
        url: '/api/health',
        status: 'unknown',
        error: null,
        response: null
      }
    }

    // Check Frontend
    try {
      checks.frontend.status = 'online'
    } catch (error) {
      checks.frontend.status = 'error'
      checks.frontend.error = error.message
    }

    // Check Backend directly
    try {
      const backendResponse = await axios.get(`${backendUrl}/api/health`, {
        timeout: 5000,
        validateStatus: () => true // Don't throw on any status
      })
      checks.backend.status = backendResponse.status === 200 ? 'online' : 'error'
      checks.backend.response = {
        status: backendResponse.status,
        data: backendResponse.data
      }
    } catch (error) {
      checks.backend.status = 'error'
      checks.backend.error = error.message || 'Connection refused'
      if (error.code === 'ECONNREFUSED') {
        checks.backend.error = 'Connection refused - Backend server is not running'
      } else if (error.code === 'ECONNABORTED') {
        checks.backend.error = 'Connection timeout - Backend server is not responding'
      } else if (error.code === 'ERR_NETWORK') {
        checks.backend.error = 'Network error - Cannot reach backend server'
      }
    }

    // Check API via proxy
    try {
      const proxyResponse = await axios.get('/api/health', {
        timeout: 5000,
        validateStatus: () => true
      })
      checks.proxy.status = proxyResponse.status === 200 ? 'online' : 'error'
      checks.proxy.response = {
        status: proxyResponse.status,
        data: proxyResponse.data
      }
    } catch (error) {
      checks.proxy.status = 'error'
      checks.proxy.error = error.message || 'Connection failed'
      if (error.code === 'ECONNABORTED') {
        checks.proxy.error = 'Timeout - Proxy not forwarding to backend'
      } else if (error.code === 'ERR_NETWORK') {
        checks.proxy.error = 'Network error - Check Vite proxy configuration'
      }
    }

    // Determine overall status
    if (checks.backend.status === 'online' && checks.proxy.status === 'online') {
      setStatus('connected')
    } else if (checks.backend.status === 'online' && checks.proxy.status === 'error') {
      setStatus('proxy_error')
    } else if (checks.backend.status === 'error' && checks.proxy.status === 'error') {
      setStatus('disconnected')
    } else {
      setStatus('partial')
    }

    setDetails(checks)
    setLoading(false)
  }

  useEffect(() => {
    checkConnection()
  }, [])

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online':
      case 'connected':
        return <CheckCircle className="w-5 h-5 text-green-400" />
      case 'error':
      case 'disconnected':
        return <XCircle className="w-5 h-5 text-red-400" />
      case 'checking':
        return <RefreshCw className="w-5 h-5 text-yellow-400 animate-spin" />
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-400" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'online':
      case 'connected':
        return 'bg-green-500/20 border-green-500/50 text-green-400'
      case 'error':
      case 'disconnected':
        return 'bg-red-500/20 border-red-500/50 text-red-400'
      case 'checking':
        return 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400'
      default:
        return 'bg-gray-500/20 border-gray-500/50 text-gray-400'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/20 shadow-2xl mb-4 sm:mb-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Wifi className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-bold">Connection Debugger</h2>
            <p className="text-xs sm:text-sm text-gray-400">Diagnose API connection issues</p>
          </div>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={checkConnection}
          disabled={loading}
          className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold disabled:opacity-50 text-sm sm:text-base"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Refresh</span>
        </motion.button>
      </div>

      {/* Backend URL Input */}
      <div className="mb-4">
        <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-2">
          <Server className="w-4 h-4" />
          Backend URL
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={backendUrl}
            onChange={(e) => setBackendUrl(e.target.value)}
            className="flex-1 px-3 py-2 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm"
            placeholder={import.meta.env.VITE_BACKEND_URL || window.location.origin.replace(':3000', ':5000') || 'http://localhost:5000'}
          />
          <button
            onClick={checkConnection}
            disabled={loading}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold disabled:opacity-50 text-sm"
          >
            Test
          </button>
        </div>
      </div>

      {/* Overall Status */}
      <div className={`mb-4 p-3 rounded-lg border flex items-center gap-3 ${getStatusColor(status)}`}>
        {getStatusIcon(status)}
        <div className="flex-1">
          <p className="font-semibold">
            {status === 'connected' && '✅ All connections working'}
            {status === 'disconnected' && '❌ Backend server is not running'}
            {status === 'proxy_error' && '⚠️ Backend running but proxy not working'}
            {status === 'partial' && '⚠️ Partial connection'}
            {status === 'checking' && '🔄 Checking connections...'}
          </p>
        </div>
      </div>

      {/* Connection Details */}
      {details && (
        <div className="space-y-3">
          {/* Frontend */}
          <div className="p-3 bg-black/40 rounded-lg border border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <Globe className="w-4 h-4 text-blue-400" />
              <span className="font-semibold text-sm">Frontend</span>
              {getStatusIcon(details.frontend.status)}
            </div>
            <p className="text-xs text-gray-400 break-all">{details.frontend.url}</p>
            {details.frontend.error && (
              <p className="text-xs text-red-400 mt-1">{details.frontend.error}</p>
            )}
          </div>

          {/* Backend Direct */}
          <div className="p-3 bg-black/40 rounded-lg border border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <Server className="w-4 h-4 text-purple-400" />
              <span className="font-semibold text-sm">Backend (Direct)</span>
              {getStatusIcon(details.backend.status)}
            </div>
            <p className="text-xs text-gray-400 break-all">{details.backend.url}</p>
            {details.backend.error && (
              <p className="text-xs text-red-400 mt-1">{details.backend.error}</p>
            )}
            {details.backend.response && (
              <div className="mt-2 text-xs">
                <p className="text-gray-400">Status: <span className="text-green-400">{details.backend.response.status}</span></p>
                {details.backend.response.data && (
                  <p className="text-gray-400 mt-1">
                    Database: <span className={details.backend.response.data.database === 'connected' ? 'text-green-400' : 'text-red-400'}>
                      {details.backend.response.data.database}
                    </span>
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Proxy */}
          <div className="p-3 bg-black/40 rounded-lg border border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <Wifi className="w-4 h-4 text-green-400" />
              <span className="font-semibold text-sm">Proxy (/api)</span>
              {getStatusIcon(details.proxy.status)}
            </div>
            <p className="text-xs text-gray-400 break-all">{details.proxy.url}</p>
            {details.proxy.error && (
              <p className="text-xs text-red-400 mt-1">{details.proxy.error}</p>
            )}
            {details.proxy.response && (
              <div className="mt-2 text-xs">
                <p className="text-gray-400">Status: <span className="text-green-400">{details.proxy.response.status}</span></p>
              </div>
            )}
          </div>

          {/* Troubleshooting Tips */}
          {status !== 'connected' && (
            <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <p className="text-sm font-semibold text-yellow-400 mb-2">💡 Troubleshooting Tips:</p>
              <ul className="text-xs text-yellow-300 space-y-1 list-disc list-inside">
                {status === 'disconnected' && (
                  <>
                    <li>Make sure the backend server is running: <code className="bg-black/40 px-1 rounded">python backend/server.py</code></li>
                    <li>Check if the backend is running on port 5000</li>
                    <li>Verify MongoDB is running: <code className="bg-black/40 px-1 rounded">net start MongoDB</code></li>
                  </>
                )}
                {status === 'proxy_error' && (
                  <>
                    <li>Backend is running but Vite proxy is not forwarding requests</li>
                    <li>Check <code className="bg-black/40 px-1 rounded">vite.config.js</code> proxy configuration</li>
                    <li>Restart the frontend dev server: <code className="bg-black/40 px-1 rounded">npm run dev</code></li>
                  </>
                )}
                <li>Check browser console (F12) for detailed error messages</li>
                <li>Verify CORS is enabled in backend (Flask-CORS)</li>
              </ul>
            </div>
          )}
        </div>
      )}
    </motion.div>
  )
}

export default ConnectionDebugger

