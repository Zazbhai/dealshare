import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Play, Square, TrendingUp, Zap, Activity, FileText, User, Home, MapPin, Bug } from 'lucide-react'
import { getBalance, getPrice, startAutomation, stopAutomation } from '../services/api'
import ConnectionDebugger from '../components/ConnectionDebugger'

function Dashboard() {
  const [balance, setBalance] = useState(null)
  const [price, setPrice] = useState(null)
  const [isRunning, setIsRunning] = useState(false)
  const [logs, setLogs] = useState([])
  const [formData, setFormData] = useState({
    name: '',
    houseFlatNo: '',
    landmark: ''
  })
  const logsEndRef = useRef(null)

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    // Auto-scroll logs to bottom
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const loadInitialData = async () => {
    try {
      const [balanceData, priceData] = await Promise.all([
        getBalance(),
        getPrice()
      ])
      if (balanceData.success) {
        setBalance(balanceData.balance)
      } else if (balanceData.error?.includes('API key')) {
        addLog('warning', '⚠️ API key not configured. Go to Settings to configure your API credentials.')
      }
      if (priceData.success) {
        setPrice(priceData.price)
      } else if (priceData.error?.includes('API key')) {
        // Already logged above
      }
    } catch (error) {
      console.error('Failed to load initial data:', error)
      addLog('error', 'Failed to load initial data')
    }
  }

  const addLog = (type, message) => {
    const timestamp = new Date().toLocaleTimeString()
    setLogs(prev => [...prev, { type, message, timestamp }])
  }

  const handleStart = async () => {
    // Validate form
    if (!formData.name.trim() || !formData.houseFlatNo.trim() || !formData.landmark.trim()) {
      addLog('error', 'Please fill in all fields (Name, House/Flat No., Landmark)')
      return
    }

    setIsRunning(true)
    addLog('info', '🚀 Starting automation...')
    addLog('info', `Name: ${formData.name}`)
    addLog('info', `House/Flat No.: ${formData.houseFlatNo}`)
    addLog('info', `Landmark: ${formData.landmark}`)

    try {
      const result = await startAutomation(formData)
      if (result.success) {
        addLog('success', '✅ Automation started successfully')
      } else {
        addLog('error', `❌ Failed to start: ${result.error || 'Unknown error'}`)
        setIsRunning(false)
      }
    } catch (error) {
      addLog('error', `❌ Error starting automation: ${error.message}`)
      setIsRunning(false)
    }
  }

  const handleStop = async () => {
    addLog('warning', '🛑 Stopping all workers and cancelling numbers...')
    setIsRunning(false)

    try {
      const result = await stopAutomation()
      if (result.success) {
        addLog('success', '✅ All workers stopped and numbers cancelled')
      } else {
        addLog('error', `❌ Failed to stop: ${result.error || 'Unknown error'}`)
      }
    } catch (error) {
      addLog('error', `❌ Error stopping automation: ${error.message}`)
    }
  }

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const [showDebugger, setShowDebugger] = useState(false)

  return (
    <div className="pt-20 sm:pt-24 pb-8 sm:pb-12 px-4 sm:px-6">
      <div className="container mx-auto max-w-6xl">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-6 sm:mb-8"
        >
          <div className="flex items-center justify-center gap-4 mb-2">
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent bg-[length:200%_auto] animate-gradient">
              Automation Dashboard
            </h1>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setShowDebugger(!showDebugger)}
              className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg border border-purple-500/20"
              title="Connection Debugger"
            >
              <Bug className="w-5 h-5 text-purple-400" />
            </motion.button>
          </div>
          <p className="text-sm sm:text-base text-gray-400">Manage your DealShare automation workflow</p>
        </motion.div>

        {/* Connection Debugger */}
        {showDebugger && <ConnectionDebugger />}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <StatCard
            icon={<TrendingUp />}
            label="Balance"
            value={balance !== null ? `₹${balance?.toFixed(2) || '0.00'}` : 'Loading...'}
            color="from-green-400 to-emerald-500"
          />
          <StatCard
            icon={<Zap />}
            label="Service Price"
            value={price ? `₹${price}` : 'Loading...'}
            color="from-yellow-400 to-orange-500"
          />
          <StatCard
            icon={<Activity />}
            label="Status"
            value={isRunning ? 'RUNNING' : 'IDLE'}
            color={isRunning ? 'from-red-400 to-pink-500' : 'from-blue-400 to-cyan-500'}
          />
        </div>

        {/* Logs Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/20 shadow-2xl mb-4 sm:mb-6"
        >
          <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
            <div className="p-2 sm:p-3 bg-purple-500/20 rounded-lg">
              <FileText className="w-5 h-5 sm:w-6 sm:h-6 text-purple-400" />
            </div>
            <h2 className="text-xl sm:text-2xl font-bold">Detailed Logs</h2>
          </div>

          <div className="bg-black/40 rounded-lg p-3 sm:p-4 h-48 sm:h-64 overflow-y-auto font-mono text-xs sm:text-sm">
            {logs.length === 0 ? (
              <div className="text-gray-500 text-center py-8">No logs yet. Start automation to see activity.</div>
            ) : (
              logs.map((log, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`mb-2 flex items-start gap-1 sm:gap-2 ${
                    log.type === 'error' ? 'text-red-400' :
                    log.type === 'success' ? 'text-green-400' :
                    log.type === 'warning' ? 'text-yellow-400' :
                    'text-gray-300'
                  }`}
                >
                  <span className="text-gray-500 text-xs min-w-[60px] sm:min-w-[80px] flex-shrink-0">{log.timestamp}</span>
                  <span className="break-words">{log.message}</span>
                </motion.div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>
        </motion.div>

        {/* Input Form Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-purple-900/50 to-pink-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/20 shadow-2xl mb-4 sm:mb-6"
        >
          <h2 className="text-xl sm:text-2xl font-bold mb-4 sm:mb-6">Order Details</h2>

          <div className="space-y-4">
            {/* Name Input */}
            <div>
              <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                <User className="w-4 h-4 flex-shrink-0" />
                Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder="Enter your name"
                disabled={isRunning}
                className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
              />
            </div>

            {/* House/Flat No. Input */}
            <div>
              <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                <Home className="w-4 h-4 flex-shrink-0" />
                House / Flat No.
              </label>
              <input
                type="text"
                value={formData.houseFlatNo}
                onChange={(e) => handleInputChange('houseFlatNo', e.target.value)}
                placeholder="Enter house/flat number"
                disabled={isRunning}
                className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
              />
            </div>

            {/* Landmark Input */}
            <div>
              <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                <MapPin className="w-4 h-4 flex-shrink-0" />
                Landmark
              </label>
              <input
                type="text"
                value={formData.landmark}
                onChange={(e) => handleInputChange('landmark', e.target.value)}
                placeholder="Enter landmark"
                disabled={isRunning}
                className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
              />
            </div>
          </div>
        </motion.div>

        {/* Start/Stop Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-center"
        >
          {!isRunning ? (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleStart}
              disabled={!formData.name.trim() || !formData.houseFlatNo.trim() || !formData.landmark.trim()}
              className="w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 rounded-lg font-bold text-base sm:text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3 shadow-xl"
            >
              <Play className="w-5 h-5 sm:w-6 sm:h-6" />
              <span>Start Automation</span>
            </motion.button>
          ) : (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleStop}
              className="w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700 rounded-lg font-bold text-base sm:text-lg transition-all flex items-center justify-center gap-2 sm:gap-3 shadow-xl"
            >
              <Square className="w-5 h-5 sm:w-6 sm:h-6" />
              <span>Stop All Workers</span>
            </motion.button>
          )}
        </motion.div>

        {/* Floating Particles Effect */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
          {[...Array(20)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 bg-purple-400/30 rounded-full"
              initial={{
                x: Math.random() * window.innerWidth,
                y: Math.random() * window.innerHeight,
              }}
              animate={{
                y: [null, -100],
                opacity: [0, 1, 0],
              }}
              transition={{
                duration: Math.random() * 3 + 2,
                repeat: Infinity,
                delay: Math.random() * 2,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, color }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.05, y: -5 }}
      className={`bg-gradient-to-br ${color} rounded-xl p-4 sm:p-6 backdrop-blur-sm border border-white/10 shadow-xl`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-white/80 text-xs sm:text-sm mb-1 truncate">{label}</p>
          <p className="text-xl sm:text-2xl font-bold text-white truncate">{value}</p>
        </div>
        <motion.div
          animate={{ rotate: [0, 10, -10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="flex-shrink-0 ml-2"
        >
          <div className="w-5 h-5 sm:w-6 sm:h-6">{icon}</div>
        </motion.div>
      </div>
    </motion.div>
  )
}

export default Dashboard
