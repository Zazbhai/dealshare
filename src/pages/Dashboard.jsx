import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Play, Square, TrendingUp, Zap, Activity, FileText, User, Home, MapPin, Bug, Download, Eye, RefreshCw, AlertCircle, X, Edit2, Save, Link2, ChevronDown, Navigation2, ToggleLeft, ToggleRight } from 'lucide-react'
import { getBalance, getGlobalSettings, startAutomation, stopAutomation, getAutomationStatus, getOrdersReport, downloadOrdersReport, getLogsList, viewLogFile, downloadLogFile } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { updateSettings } from '../services/auth'
import ConnectionDebugger from '../components/ConnectionDebugger'

function Dashboard() {
  const { user, updateSettings: updateUserSettings } = useAuth()
  const [balance, setBalance] = useState(null)
  const [price, setPrice] = useState(null)
  const [isRunning, setIsRunning] = useState(false)
  const [logs, setLogs] = useState([])
  const [formData, setFormData] = useState({
    name: '',
    houseFlatNo: '',
    landmark: '',
    totalOrders: '1',
    maxParallelWindows: '1',
    retryOrders: false, // Toggle to retry failed orders once
    primaryProductUrl: '',
    secondaryProductUrl: '',
    thirdProductUrl: '',
    primaryProductQuantity: '1',
    secondaryProductQuantity: '1',
    thirdProductQuantity: '1',
    latitude: '26.994880',
    longitude: '75.774836',
    currentLocation: 'default',
    selectLocation: true, // Toggle for location selection step
    searchInput: 'chinu juice center', // Search query for location
    locationText: 'Chinu Juice Center, Jaswant Nagar, mod, Khatipura, Jaipur, Rajasthan, India' // Exact location text to select
  })
  const logsEndRef = useRef(null)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [orders, setOrders] = useState([])
  const [logFiles, setLogFiles] = useState([])
  const [selectedLogContent, setSelectedLogContent] = useState(null)
  const [selectedLogFilename, setSelectedLogFilename] = useState(null)
  const [showCompletionModal, setShowCompletionModal] = useState(false)
  const [showCapacityErrorModal, setShowCapacityErrorModal] = useState(false)
  const [showAllProductsFailedModal, setShowAllProductsFailedModal] = useState(false)
  const [completionStats, setCompletionStats] = useState({ success: 0, failure: 0 })
  const [realtimeStats, setRealtimeStats] = useState({ success: 0, failure: 0, total: 0 })
  const [isEditMode, setIsEditMode] = useState(false)
  const [hasStarted, setHasStarted] = useState(false) // Track if automation has actually started
  const [isProductLinksOpen, setIsProductLinksOpen] = useState(false) // Track product links dropdown state

  useEffect(() => {
    loadInitialData()
    loadAllDashboardSettings()
    // Check initial automation status to sync state
    checkInitialStatus()
  }, [user])

  const loadAllDashboardSettings = () => {
    if (user) {
      setFormData(prev => ({
        ...prev,
        // Order details
        name: user.name || prev.name || '',
        houseFlatNo: user.house_flat_no || prev.houseFlatNo || '',
        landmark: user.landmark || prev.landmark || '',
        // Automation settings
        totalOrders: user.total_orders?.toString() || prev.totalOrders || '1',
        maxParallelWindows: user.max_parallel_windows?.toString() || prev.maxParallelWindows || '1',
        retryOrders: user.retry_orders !== undefined ? user.retry_orders : prev.retryOrders || false,
        // Product URLs
        primaryProductUrl: user.primary_product_url || prev.primaryProductUrl || '',
        secondaryProductUrl: user.secondary_product_url || prev.secondaryProductUrl || '',
        thirdProductUrl: user.third_product_url || prev.thirdProductUrl || '',
        // Product Quantities
        primaryProductQuantity: user.primary_product_quantity?.toString() || prev.primaryProductQuantity || '1',
        secondaryProductQuantity: user.secondary_product_quantity?.toString() || prev.secondaryProductQuantity || '1',
        thirdProductQuantity: user.third_product_quantity?.toString() || prev.thirdProductQuantity || '1',
        // Location settings
        latitude: user.latitude || prev.latitude || '26.994880',
        longitude: user.longitude || prev.longitude || '75.774836',
        currentLocation: user.current_location || prev.currentLocation || 'default',
        selectLocation: user.select_location_enabled !== undefined ? user.select_location_enabled : prev.selectLocation !== undefined ? prev.selectLocation : true,
        searchInput: user.search_input || prev.searchInput || 'chinu juice center',
        locationText: user.location_text || prev.locationText || 'Chinu Juice Center, Jaswant Nagar, mod, Khatipura, Jaipur, Rajasthan, India'
      }))
    }
  }

  const checkInitialStatus = async () => {
    try {
      const status = await getAutomationStatus()
      if (status.success && status.is_running === true) {
        // Automation is already running - sync state
        setIsRunning(true)
        setHasStarted(true)
        setRealtimeStats({
          success: status.success || 0,
          failure: status.failure || 0,
          total: (status.success || 0) + (status.failure || 0)
        })
      }
    } catch (error) {
      // Silently handle - automation might not be running
    }
  }

  const handleToggleEditMode = async () => {
    if (isEditMode) {
      // Save all dashboard settings when exiting edit mode
      try {
        const settingsToSave = {
          // Order details
          name: formData.name,
          house_flat_no: formData.houseFlatNo,
          landmark: formData.landmark,
          // Automation settings
          total_orders: parseInt(formData.totalOrders) || 1,
          max_parallel_windows: parseInt(formData.maxParallelWindows) || 1,
          retry_orders: formData.retryOrders || false,
          // Product URLs
          primary_product_url: formData.primaryProductUrl,
          secondary_product_url: formData.secondaryProductUrl,
          third_product_url: formData.thirdProductUrl,
          // Product Quantities
          primary_product_quantity: parseInt(formData.primaryProductQuantity) || 1,
          secondary_product_quantity: parseInt(formData.secondaryProductQuantity) || 1,
          third_product_quantity: parseInt(formData.thirdProductQuantity) || 1,
          // Location settings
          latitude: formData.latitude,
          longitude: formData.longitude,
          current_location: formData.currentLocation,
          select_location_enabled: formData.selectLocation !== undefined ? formData.selectLocation : true,
          search_input: formData.searchInput,
          location_text: formData.locationText
        }
        
        const result = await updateSettings(settingsToSave)
        if (result.success) {
          await updateUserSettings(settingsToSave)
          addLog('success', '✅ All dashboard settings saved successfully')
        } else {
          addLog('error', `❌ Failed to save settings: ${result.error}`)
        }
      } catch (error) {
        addLog('error', `❌ Error saving settings: ${error.message}`)
      }
    }
    setIsEditMode(!isEditMode)
  }

  useEffect(() => {
    // Auto-scroll logs to bottom
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const loadInitialData = async () => {
    try {
      const [balanceData, settingsData] = await Promise.all([
        getBalance(),
        getGlobalSettings()
      ])
      if (balanceData.success) {
        setBalance(balanceData.balance)
      } else if (balanceData.error) {
        // Only show "not configured" if the error specifically says "not configured"
        // Don't show warning for "Invalid API key" - that means it's configured but wrong
        if (balanceData.error.includes('not configured') || balanceData.error.includes('not set')) {
          addLog('warning', '⚠️ API key not configured. Go to Settings to configure your API credentials.')
        } else if (balanceData.error.includes('Invalid API key')) {
          addLog('error', '⚠️ Invalid API key. Please check your API credentials in Settings.')
        } else {
          addLog('error', `⚠️ ${balanceData.error}`)
        }
      }
      if (settingsData.success) {
        setPrice(settingsData.price !== undefined ? settingsData.price : null)
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

    // Validate numeric inputs
    const totalOrders = parseInt(formData.totalOrders) || 1
    const maxParallel = parseInt(formData.maxParallelWindows) || 1


    if (totalOrders < 1) {
      addLog('error', 'Total orders must be at least 1')
      return
    }
    if (maxParallel < 1) {
      addLog('error', 'Max parallel windows must be at least 1')
      return
    }
    if (maxParallel > totalOrders) {
      addLog('warning', `Max parallel windows (${maxParallel}) is greater than total orders (${totalOrders}). Setting to ${totalOrders}`)
      setFormData(prev => ({ ...prev, maxParallelWindows: totalOrders.toString() }))
    }

    // Validate capacity
    if (price !== null && price > 0 && balance !== null && balance > 0) {
      const capacity = Math.floor(balance / price)
      if (totalOrders > capacity) {
        setShowCapacityErrorModal(true)
        addLog('error', `❌ Total orders (${totalOrders}) exceeds capacity (${capacity}). Please reduce the number of orders.`)
        return
      }
    }

    // Get product URLs - Primary is mandatory, others are optional
    let primaryUrl = formData.primaryProductUrl ? formData.primaryProductUrl.trim() : ''

    // Primary URL is mandatory
    if (!primaryUrl) {
      addLog('error', '❌ Primary Product URL is required. Please configure it.')
      return
    }

    if (price === null || price <= 0) {
      addLog('error', '❌ Service price is not set. Please contact admin to set the price.')
      return
    } else if (balance === null || balance <= 0) {
      addLog('error', '❌ Insufficient balance. Please check your account balance.')
      return
    }

    addLog('info', '🚀 Starting automation...')
    addLog('info', `Name: ${formData.name}`)
    addLog('info', `House/Flat No.: ${formData.houseFlatNo}`)
    addLog('info', `Landmark: ${formData.landmark}`)
    addLog('info', `Total Orders: ${totalOrders}`)
    addLog('info', `Max Parallel Windows: ${Math.min(maxParallel, totalOrders)}`)

    // Reset all state before starting
    setRealtimeStats({ success: 0, failure: 0, total: 0 })
    setCompletionStats({ success: 0, failure: 0 })
    setShowCompletionModal(false)
    setShowAllProductsFailedModal(false)
    setHasStarted(false)

    try {
      const result = await startAutomation(formData)

      if (result.success) {
        addLog('success', '✅ Automation started successfully')
        // Only set running state after backend confirms success
        setIsRunning(true)
        setHasStarted(true)
      } else {
        addLog('error', `❌ Failed to start: ${result.error || 'Unknown error'}`)
      }
    } catch (error) {
      addLog('error', `❌ Error starting automation: ${error.message}`)
    }
  }

  const handleStop = async () => {
    addLog('warning', '🛑 Stopping all workers and cancelling numbers...')

    try {
      const result = await stopAutomation()
      if (result.success) {
        addLog('success', '✅ All workers stopped and numbers cancelled')
        // Reset state after successful stop
        setIsRunning(false)
        setHasStarted(false)
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

  const loadOrdersReport = async () => {
    try {
      const result = await getOrdersReport()
      if (result.success) {
        setOrders(result.orders || [])
      } else {
        addLog('error', `Failed to load orders: ${result.error}`)
      }
    } catch (error) {
      addLog('error', `Error loading orders: ${error.message}`)
    }
  }

  const loadLogsList = async () => {
    try {
      const result = await getLogsList()
      if (result.success) {
        setLogFiles(result.logs || [])
      } else {
        addLog('error', `Failed to load logs: ${result.error}`)
      }
    } catch (error) {
      addLog('error', `Error loading logs: ${error.message}`)
    }
  }

  const handleViewLog = async (filename) => {
    try {
      const result = await viewLogFile(filename)
      if (result.success) {
        setSelectedLogContent(result.content)
        setSelectedLogFilename(filename)
      } else {
        addLog('error', `Failed to view log: ${result.error}`)
      }
    } catch (error) {
      addLog('error', `Error viewing log: ${error.message}`)
    }
  }

  const handleDownloadLog = async (filename) => {
    try {
      const result = await downloadLogFile(filename)
      if (result.success) {
        addLog('success', `Downloaded ${filename}`)
      } else {
        addLog('error', `Failed to download: ${result.error}`)
      }
    } catch (error) {
      addLog('error', `Error downloading log: ${error.message}`)
    }
  }

  const handleDownloadOrders = async () => {
    try {
      const result = await downloadOrdersReport()
      if (result.success) {
        addLog('success', 'Orders report downloaded')
      } else {
        addLog('error', `Failed to download: ${result.error}`)
      }
    } catch (error) {
      addLog('error', `Error downloading report: ${error.message}`)
    }
  }

  useEffect(() => {
    if (activeTab === 'reports') {
      loadOrdersReport()
    } else if (activeTab === 'logs') {
      loadLogsList()
    }
  }, [activeTab])

  // Poll automation status when running
  useEffect(() => {
    let intervalId = null

    // Only poll if we're actually running or have started
    if (!isRunning && !hasStarted) {
      return // Don't poll if we haven't started
    }

    const pollStatus = async () => {
      try {
        const status = await getAutomationStatus()

        if (status.success) {
          const successCount = status.success_count || 0
          const failureCount = status.failure_count || 0
          const totalCount = successCount + failureCount
          const backendIsRunning = status.is_running === true

          // Only update stats if we've actually started
          if (hasStarted) {
            setRealtimeStats({
              success: successCount,
              failure: failureCount,
              total: totalCount
            })
          }

          // Check for critical failure (all products failed)
          if (status.all_products_failed) {
            if (!showAllProductsFailedModal) {
              setShowAllProductsFailedModal(true)
              addLog('error', '🚨 ALL PRODUCTS FAILED - Stopped Automation')
            }
          }

          // Handle state transitions
          if (!backendIsRunning && isRunning && hasStarted) {
            // Automation completed - only show modal if we actually ran
            setIsRunning(false)
            setHasStarted(false)
            setCompletionStats({
              success: successCount,
              failure: failureCount
            })
            // Use setTimeout to ensure state updates before showing modal
            setTimeout(() => {
              setShowCompletionModal(true)
            }, 300)
            addLog('success', `✅ Automation completed! Success: ${successCount}, Failure: ${failureCount}`)
          } else if (backendIsRunning && !isRunning && hasStarted) {
            // Backend says running but frontend doesn't - sync state
            setIsRunning(true)
          } else if (!backendIsRunning && hasStarted && !isRunning) {
            // Backend stopped, make sure we're in sync
            setHasStarted(false)
          }
        }
      } catch (error) {
        // Silently handle errors - don't spam logs
      }
    }

    // Poll every 1 second when running
    if (isRunning) {
      intervalId = setInterval(pollStatus, 1000)
      // Also poll immediately
      pollStatus()
    } else if (hasStarted) {
      // If we started but aren't running, check once more to catch completion
      pollStatus()
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [isRunning, hasStarted])

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

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex gap-2 mb-6 border-b border-purple-500/20"
        >
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-4 py-2 font-semibold transition-colors ${activeTab === 'dashboard'
              ? 'text-purple-400 border-b-2 border-purple-400'
              : 'text-gray-400 hover:text-gray-300'
              }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab('reports')}
            className={`px-4 py-2 font-semibold transition-colors ${activeTab === 'reports'
              ? 'text-purple-400 border-b-2 border-purple-400'
              : 'text-gray-400 hover:text-gray-300'
              }`}
          >
            Reports
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`px-4 py-2 font-semibold transition-colors ${activeTab === 'logs'
              ? 'text-purple-400 border-b-2 border-purple-400'
              : 'text-gray-400 hover:text-gray-300'
              }`}
          >
            Logs
          </button>
        </motion.div>

        {/* Dashboard Tab Content */}
        {activeTab === 'dashboard' && (
          <>
            {/* Stats Cards */}
            <div className={`grid gap-4 sm:gap-6 mb-6 sm:mb-8 ${isRunning
              ? 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6'
              : 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3'
              }`}>
              <StatCard
                icon={<TrendingUp />}
                label="Balance"
                value={balance !== null ? `₹${balance?.toFixed(2) || '0.00'}` : 'Loading...'}
                color="from-green-400 to-emerald-500"
              />
              <StatCard
                icon={<Zap />}
                label="Service Price"
                value={price !== null ? `₹${price.toFixed(2)}` : 'Not Set'}
                color="from-yellow-400 to-orange-500"
              />
              {price !== null && price > 0 && balance !== null && balance > 0 && (
                <StatCard
                  icon={<TrendingUp />}
                  label="Capacity"
                  value={Math.floor(balance / price)}
                  color="from-blue-400 to-cyan-500"
                />
              )}
              <StatCard
                icon={<Activity />}
                label="Status"
                value={isRunning ? 'RUNNING' : 'IDLE'}
                color={isRunning ? 'from-red-400 to-pink-500' : 'from-blue-400 to-cyan-500'}
              />
              {isRunning && (
                <>
                  <motion.div
                    animate={{ scale: [1, 1.05, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <StatCard
                      icon={<TrendingUp />}
                      label="Success (Live)"
                      value={realtimeStats.success}
                      color="from-green-400 to-emerald-500"
                    />
                  </motion.div>
                  <motion.div
                    animate={{ scale: [1, 1.05, 1] }}
                    transition={{ duration: 2, repeat: Infinity, delay: 0.3 }}
                  >
                    <StatCard
                      icon={<Square />}
                      label="Failed (Live)"
                      value={realtimeStats.failure}
                      color="from-red-400 to-pink-500"
                    />
                  </motion.div>
                  <motion.div
                    animate={{ scale: [1, 1.05, 1] }}
                    transition={{ duration: 2, repeat: Infinity, delay: 0.6 }}
                  >
                    <StatCard
                      icon={<Zap />}
                      label="Total Processed"
                      value={realtimeStats.total}
                      color="from-blue-400 to-cyan-500"
                    />
                  </motion.div>
                </>
              )}
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
                      className={`mb-2 flex items-start gap-1 sm:gap-2 ${log.type === 'error' ? 'text-red-400' :
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
              <div className="flex items-center justify-between mb-4 sm:mb-6">
                <h2 className="text-xl sm:text-2xl font-bold">Order Details</h2>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleToggleEditMode}
                  disabled={isRunning}
                  className={`p-2 rounded-lg transition-all flex items-center gap-2 ${isEditMode
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-purple-600 hover:bg-purple-700 text-white'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                  title={isEditMode ? 'Save changes' : 'Edit order details'}
                >
                  {isEditMode ? (
                    <>
                      <Save className="w-4 h-4 sm:w-5 sm:h-5" />
                      <span className="text-xs sm:text-sm font-semibold hidden sm:inline">Save</span>
                    </>
                  ) : (
                    <>
                      <Edit2 className="w-4 h-4 sm:w-5 sm:h-5" />
                      <span className="text-xs sm:text-sm font-semibold hidden sm:inline">Edit</span>
                    </>
                  )}
                </motion.button>
              </div>

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
                    disabled={isRunning || !isEditMode}
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
                    disabled={isRunning || !isEditMode}
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
                    disabled={isRunning || !isEditMode}
                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                  />
                </div>

                {/* Total Orders Input */}
                <div>
                  <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                    <TrendingUp className="w-4 h-4 flex-shrink-0" />
                    Total Orders
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.totalOrders}
                    onChange={(e) => handleInputChange('totalOrders', e.target.value)}
                    placeholder="Number of orders to process"
                    disabled={isRunning}
                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                  />
                </div>

                {/* Max Parallel Windows Input */}
                <div>
                  <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                    <Zap className="w-4 h-4 flex-shrink-0" />
                    Max Parallel Windows
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.maxParallelWindows}
                    onChange={(e) => handleInputChange('maxParallelWindows', e.target.value)}
                    placeholder="Max windows to open simultaneously"
                    disabled={isRunning}
                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                  />
                  <p className="text-xs text-gray-500 mt-1">Maximum number of browser windows to open at the same time</p>
                </div>

                {/* Retry Orders Toggle */}
                <div className="col-span-1 sm:col-span-2">
                  <div className="p-4 bg-black/30 rounded-lg border border-purple-500/20">
                    <div className="flex items-center justify-between mb-2">
                      <label className="flex items-center gap-2 text-sm sm:text-base font-semibold text-gray-300">
                        <RefreshCw className="w-5 h-5 text-purple-400" />
                        Retry Orders
                      </label>
                      <button
                        onClick={() => handleInputChange('retryOrders', !formData.retryOrders)}
                        disabled={isRunning}
                        className={`relative inline-flex h-7 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${
                          formData.retryOrders ? 'bg-gradient-to-r from-purple-500 to-pink-500' : 'bg-gray-600'
                        }`}
                        type="button"
                      >
                        <span
                          className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
                            formData.retryOrders ? 'translate-x-8' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                    <p className="text-xs text-gray-400">
                      {formData.retryOrders
                        ? 'Failed orders will be retried once automatically'
                        : 'Failed orders will not be retried'}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Product Links Dropdown Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-br from-blue-900/50 to-purple-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl border border-blue-500/20 shadow-2xl mb-4 sm:mb-6 overflow-hidden"
            >
              {/* Dropdown Header */}
              <motion.button
                onClick={() => setIsProductLinksOpen(!isProductLinksOpen)}
                disabled={isRunning}
                className="w-full px-4 sm:px-6 py-4 sm:py-5 flex items-center justify-between bg-gradient-to-r from-blue-600/20 to-purple-600/20 hover:from-blue-600/30 hover:to-purple-600/30 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed group"
                whileHover={!isRunning ? { scale: 1.01 } : {}}
                whileTap={!isRunning ? { scale: 0.99 } : {}}
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-500/20 rounded-lg group-hover:bg-blue-500/30 transition-colors">
                    <Link2 className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                  </div>
                  <div className="text-left">
                    <h2 className="text-lg sm:text-xl font-bold text-white">Product Links</h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-0.5">Configure your product URLs</p>
                  </div>
                </div>
                <motion.div
                  animate={{ rotate: isProductLinksOpen ? 180 : 0 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                  className="p-2 bg-white/5 rounded-lg group-hover:bg-white/10 transition-colors"
                >
                  <ChevronDown className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                </motion.div>
              </motion.button>

              {/* Dropdown Content */}
              <motion.div
                initial={false}
                animate={{
                  height: isProductLinksOpen ? "auto" : 0,
                  opacity: isProductLinksOpen ? 1 : 0
                }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="overflow-hidden"
              >
                <div className="px-4 sm:px-6 pb-4 sm:pb-6 pt-2 space-y-4">
                  {/* Primary Product URL */}
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{
                      opacity: isProductLinksOpen ? 1 : 0,
                      x: isProductLinksOpen ? 0 : -20
                    }}
                    transition={{ duration: 0.3, delay: 0.1 }}
                  >
                    <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                      <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                      Primary Product URL <span className="text-red-400">*</span>
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={formData.primaryProductUrl}
                        onChange={(e) => handleInputChange('primaryProductUrl', e.target.value)}
                        placeholder="https://www.dealshare.in/pname/..."
                        disabled={isRunning || !isEditMode}
                        className="flex-1 px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base transition-all"
                      />
                      <input
                        type="number"
                        min="1"
                        value={formData.primaryProductQuantity}
                        onChange={(e) => handleInputChange('primaryProductQuantity', e.target.value)}
                        placeholder="Qty"
                        disabled={isRunning || !isEditMode}
                        className="w-20 px-3 py-2.5 sm:py-3 bg-black/40 border border-blue-500/50 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base transition-all text-center"
                      />
                    </div>
                  </motion.div>

                  {/* Secondary Product URL */}
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{
                      opacity: isProductLinksOpen ? 1 : 0,
                      x: isProductLinksOpen ? 0 : -20
                    }}
                    transition={{ duration: 0.3, delay: 0.15 }}
                  >
                    <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                      <div className="w-2 h-2 rounded-full bg-purple-400"></div>
                      Secondary Product URL <span className="text-gray-500 text-xs">(Optional)</span>
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={formData.secondaryProductUrl}
                        onChange={(e) => handleInputChange('secondaryProductUrl', e.target.value)}
                        placeholder="https://www.dealshare.in/pname/..."
                        disabled={isRunning || !isEditMode}
                        className="flex-1 px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base transition-all"
                      />
                      <input
                        type="number"
                        min="1"
                        value={formData.secondaryProductQuantity}
                        onChange={(e) => handleInputChange('secondaryProductQuantity', e.target.value)}
                        placeholder="Qty"
                        disabled={isRunning || !isEditMode}
                        className="w-20 px-3 py-2.5 sm:py-3 bg-black/40 border border-purple-500/50 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base transition-all text-center"
                      />
                    </div>
                  </motion.div>

                  {/* Third Product URL */}
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{
                      opacity: isProductLinksOpen ? 1 : 0,
                      x: isProductLinksOpen ? 0 : -20
                    }}
                    transition={{ duration: 0.3, delay: 0.2 }}
                  >
                    <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                      <div className="w-2 h-2 rounded-full bg-pink-400"></div>
                      Third Product URL <span className="text-gray-500 text-xs">(Optional)</span>
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={formData.thirdProductUrl}
                        onChange={(e) => handleInputChange('thirdProductUrl', e.target.value)}
                        placeholder="https://www.dealshare.in/pname/..."
                        disabled={isRunning || !isEditMode}
                        className="flex-1 px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-pink-500 focus:ring-2 focus:ring-pink-500/50 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base transition-all"
                      />
                      <input
                        type="number"
                        min="1"
                        value={formData.thirdProductQuantity}
                        onChange={(e) => handleInputChange('thirdProductQuantity', e.target.value)}
                        placeholder="Qty"
                        disabled={isRunning || !isEditMode}
                        className="w-20 px-3 py-2.5 sm:py-3 bg-black/40 border border-pink-500/50 rounded-lg focus:outline-none focus:border-pink-500 focus:ring-2 focus:ring-pink-500/50 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base transition-all text-center"
                      />
                    </div>
                  </motion.div>

                  {/* Info Text */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: isProductLinksOpen ? 1 : 0 }}
                    transition={{ duration: 0.3, delay: 0.25 }}
                    className="mt-4 pt-4 border-t border-gray-700/50"
                  >
                    <p className="text-xs text-gray-400 flex items-start gap-2">
                      <Zap className="w-3 h-3 mt-0.5 text-blue-400 flex-shrink-0" />
                      <span>Automation will try URLs in order: Primary → Secondary → Third. If all 3 fail, automation stops.</span>
                    </p>
                  </motion.div>
                </div>
              </motion.div>
            </motion.div>

            {/* Location Settings Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-br from-green-900/50 to-blue-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-green-500/20 shadow-2xl mb-4 sm:mb-6"
            >
              <div className="flex items-center justify-between mb-4 sm:mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-500/20 rounded-lg">
                    <MapPin className="w-5 h-5 sm:w-6 sm:h-6 text-green-400" />
                  </div>
                  <h2 className="text-xl sm:text-2xl font-bold">Location Settings</h2>
                </div>
              </div>

              <div className="space-y-4">
                {/* Select Location Toggle */}
                <div className="p-4 bg-black/30 rounded-lg border border-green-500/20">
                  <div className="flex items-center justify-between mb-3">
                    <label className="flex items-center gap-2 text-sm sm:text-base font-semibold text-gray-300">
                      <Navigation2 className="w-5 h-5 text-green-400" />
                      Select Location
                    </label>
                    <button
                      onClick={() => handleInputChange('selectLocation', !formData.selectLocation)}
                      disabled={isRunning}
                      className={`relative inline-flex h-7 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed ${formData.selectLocation ? 'bg-gradient-to-r from-green-500 to-emerald-500' : 'bg-gray-600'
                        }`}
                      type="button"
                    >
                      <span
                        className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${formData.selectLocation ? 'translate-x-8' : 'translate-x-1'
                          }`}
                      />
                    </button>
                  </div>
                  <p className="text-xs text-gray-400">
                    {formData.selectLocation
                      ? 'Location selection step will be executed during automation'
                      : 'Location selection step will be skipped'}
                  </p>
                </div>

                {/* Current Location Dropdown */}
                <div>
                  <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                    <Navigation2 className="w-4 h-4 flex-shrink-0" />
                    Current Location
                  </label>
                  <select
                    value={formData.currentLocation}
                    onChange={(e) => {
                      const value = e.target.value
                      handleInputChange('currentLocation', value)
                      if (value === 'default') {
                        handleInputChange('latitude', '26.994880')
                        handleInputChange('longitude', '75.774836')
                      }
                    }}
                    disabled={isRunning}
                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/50 text-white disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                  >
                    <option value="default" className="bg-gray-800">Default Location (26.994880, 75.774836)</option>
                    <option value="custom" className="bg-gray-800">Custom Location</option>
                  </select>
                </div>

                {/* Latitude and Longitude Inputs */}
                {formData.currentLocation === 'custom' && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="grid grid-cols-1 sm:grid-cols-2 gap-4"
                  >
                    <div>
                      <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                        Latitude
                      </label>
                      <input
                        type="number"
                        step="any"
                        value={formData.latitude}
                        onChange={(e) => handleInputChange('latitude', e.target.value)}
                        placeholder="26.994880"
                        disabled={isRunning}
                        className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/50 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                      />
                    </div>
                    <div>
                      <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                        Longitude
                      </label>
                      <input
                        type="number"
                        step="any"
                        value={formData.longitude}
                        onChange={(e) => handleInputChange('longitude', e.target.value)}
                        placeholder="75.774836"
                        disabled={isRunning}
                        className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/50 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                      />
                    </div>
                  </motion.div>
                )}

                {/* Search Input and Location Text - Only visible when Select Location toggle is ON */}
                {formData.selectLocation && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-4 mt-4 pt-4 border-t border-gray-700/50"
                  >
                    <div>
                      <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                        <Navigation2 className="w-4 h-4 flex-shrink-0 text-green-400" />
                        Search Input
                      </label>
                      <input
                        type="text"
                        value={formData.searchInput}
                        onChange={(e) => handleInputChange('searchInput', e.target.value)}
                        placeholder="chinu juice center"
                        disabled={isRunning}
                        className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-green-500/30 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/50 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                      />
                      <p className="text-xs text-gray-400 mt-1">Search query to find location in Google search</p>
                    </div>
                    <div>
                      <label className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                        <Navigation2 className="w-4 h-4 flex-shrink-0 text-green-400" />
                        Location Text
                      </label>
                      <input
                        type="text"
                        value={formData.locationText}
                        onChange={(e) => handleInputChange('locationText', e.target.value)}
                        placeholder="Chinu Juice Center, Jaswant Nagar, mod, Khatipura, Jaipur, Rajasthan, India"
                        disabled={isRunning}
                        className="w-full px-3 sm:px-4 py-2.5 sm:py-3 bg-black/40 border border-green-500/30 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/50 text-white placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
                      />
                      <p className="text-xs text-gray-400 mt-1">Exact location text that appears in search results to select</p>
                    </div>
                  </motion.div>
                )}
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
                  onClick={(e) => {
                    handleStart()
                  }}
                  disabled={!formData.name.trim() || !formData.houseFlatNo.trim() || !formData.landmark.trim() || !formData.totalOrders || !formData.maxParallelWindows || !formData.primaryProductUrl.trim()}
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

            {/* Completion Modal */}
            {showCompletionModal && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                onClick={() => setShowCompletionModal(false)}
              >
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  onClick={(e) => e.stopPropagation()}
                  className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-6 sm:p-8 border border-purple-500/20 shadow-2xl max-w-md w-full"
                >
                  <div className="text-center mb-6">
                    <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
                      <Activity className="w-8 h-8 text-white" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Automation Complete!</h2>
                    <p className="text-gray-400">All orders have been processed</p>
                  </div>

                  <div className="space-y-4 mb-6">
                    <div className="flex items-center justify-between p-4 bg-green-500/10 rounded-lg border border-green-500/20">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center">
                          <TrendingUp className="w-5 h-5 text-green-400" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-400">Successful Orders</p>
                          <p className="text-2xl font-bold text-green-400">{completionStats.success}</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-red-500/10 rounded-lg border border-red-500/20">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-red-500/20 rounded-full flex items-center justify-center">
                          <Square className="w-5 h-5 text-red-400" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-400">Failed Orders</p>
                          <p className="text-2xl font-bold text-red-400">{completionStats.failure}</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-500/20 rounded-full flex items-center justify-center">
                          <Activity className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-400">Total Orders</p>
                          <p className="text-2xl font-bold text-blue-400">{completionStats.success + completionStats.failure}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setShowCompletionModal(false)
                      loadOrdersReport() // Refresh reports
                    }}
                    className="w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-lg font-semibold transition-all"
                  >
                    Close
                  </button>
                </motion.div>
              </motion.div>
            )}

            {/* All Products Failed Modal */}
            {showAllProductsFailedModal && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                onClick={() => setShowAllProductsFailedModal(false)}
              >
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  onClick={(e) => e.stopPropagation()}
                  className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-6 sm:p-8 max-w-md w-full border border-red-500/30 shadow-2xl"
                >
                  <div className="text-center mb-6">
                    <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      <AlertCircle className="w-8 h-8 text-red-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">⚠️ All Products Out of Stock!</h2>
                    <p className="text-gray-400">All three product URLs failed. Automation stopped immediately.</p>
                  </div>

                  {/* Warning Banner */}
                  <div className="mb-6 p-4 bg-red-500/10 rounded-lg border border-red-500/30">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-semibold text-red-400 mb-1">All Products Failed</p>
                        <p className="text-xs text-gray-400">
                          Primary, Secondary, and Third product URLs are all out of stock. Please update your product URLs and try again.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4 mb-6">
                    <div className="flex items-center justify-between p-4 bg-green-500/10 rounded-lg border border-green-500/20">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center">
                          <TrendingUp className="w-5 h-5 text-green-400" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-400">Successful Orders</p>
                          <p className="text-2xl font-bold text-green-400">{completionStats.success}</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-red-500/10 rounded-lg border border-red-500/20">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-red-500/20 rounded-full flex items-center justify-center">
                          <Square className="w-5 h-5 text-red-400" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-400">Failed Orders</p>
                          <p className="text-2xl font-bold text-red-400">{completionStats.failure}</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-500/20 rounded-full flex items-center justify-center">
                          <Activity className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-400">Total Processed</p>
                          <p className="text-2xl font-bold text-blue-400">{completionStats.success + completionStats.failure}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setShowAllProductsFailedModal(false)
                      loadOrdersReport() // Refresh reports
                    }}
                    className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-lg font-semibold text-white transition-all"
                  >
                    Close
                  </button>
                </motion.div>
              </motion.div>
            )}

            {/* Capacity Error Modal */}
            {showCapacityErrorModal && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                onClick={() => setShowCapacityErrorModal(false)}
              >
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  onClick={(e) => e.stopPropagation()}
                  className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-6 sm:p-8 border border-red-500/20 shadow-2xl max-w-md w-full"
                >
                  <div className="text-center mb-6">
                    <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-red-500 to-pink-500 rounded-full flex items-center justify-center">
                      <AlertCircle className="w-8 h-8 text-white" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Insufficient Capacity</h2>
                    <p className="text-gray-400">Total orders exceed available capacity</p>
                  </div>

                  <div className="space-y-4 mb-6">
                    <div className="p-4 bg-red-500/10 rounded-lg border border-red-500/20">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-400">Total Orders:</span>
                          <span className="text-lg font-bold text-red-400">{parseInt(formData.totalOrders) || 1}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-400">Available Capacity:</span>
                          <span className="text-lg font-bold text-green-400">
                            {price !== null && price > 0 && balance !== null && balance > 0
                              ? Math.floor(balance / price)
                              : 'N/A'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between pt-2 border-t border-gray-700">
                          <span className="text-sm text-gray-400">Balance:</span>
                          <span className="text-sm font-semibold text-white">
                            {balance !== null ? `₹${balance.toFixed(2)}` : 'N/A'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-400">Price per Order:</span>
                          <span className="text-sm font-semibold text-white">
                            {price !== null ? `₹${price.toFixed(2)}` : 'N/A'}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                      <p className="text-sm text-yellow-400 text-center">
                        Please reduce the number of orders to {price !== null && price > 0 && balance !== null && balance > 0
                          ? Math.floor(balance / price)
                          : 'available capacity'} or less
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setShowCapacityErrorModal(false)
                    }}
                    className="w-full px-6 py-3 bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700 rounded-lg font-semibold text-white transition-all flex items-center justify-center gap-2"
                  >
                    <X className="w-5 h-5" />
                    Close
                  </button>
                </motion.div>
              </motion.div>
            )}

          </>
        )}

        {/* Reports Tab Content */}
        {activeTab === 'reports' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/20 shadow-2xl"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="p-2 sm:p-3 bg-purple-500/20 rounded-lg">
                  <FileText className="w-5 h-5 sm:w-6 sm:h-6 text-purple-400" />
                </div>
                <h2 className="text-xl sm:text-2xl font-bold">Orders Report</h2>
              </div>
              <button
                onClick={handleDownloadOrders}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
              >
                <Download className="w-4 h-4" />
                Download CSV
              </button>
            </div>

            {orders.length === 0 ? (
              <div className="text-gray-500 text-center py-8">No orders found. Start automation to generate reports.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-purple-500/20">
                      <th className="pb-2 text-sm font-semibold text-gray-300">Timestamp</th>
                      <th className="pb-2 text-sm font-semibold text-gray-300">Screenshot</th>
                      <th className="pb-2 text-sm font-semibold text-gray-300">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((order, index) => (
                      <tr key={index} className="border-b border-purple-500/10">
                        <td className="py-3 text-sm text-gray-400">{order.timestamp || '-'}</td>
                        <td className="py-3 text-sm">
                          {order.screenshot_url ? (
                            <a href={order.screenshot_url} target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:text-purple-300 underline">
                              View Screenshot
                            </a>
                          ) : (
                            <span className="text-gray-500">No screenshot</span>
                          )}
                        </td>
                        <td className="py-3 text-sm">
                          <span className={`px-2 py-1 rounded ${order.status === 'success' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                            }`}>
                            {order.status || '-'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </motion.div>
        )}

        {/* Logs Tab Content */}
        {activeTab === 'logs' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/20 shadow-2xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="p-2 sm:p-3 bg-purple-500/20 rounded-lg">
                    <FileText className="w-5 h-5 sm:w-6 sm:h-6 text-purple-400" />
                  </div>
                  <h2 className="text-xl sm:text-2xl font-bold">Log Files</h2>
                </div>
                <button
                  onClick={loadLogsList}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh
                </button>
              </div>

              {logFiles.length === 0 ? (
                <div className="text-gray-500 text-center py-8">No log files found.</div>
              ) : (
                <div className="space-y-2">
                  {logFiles.map((log, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-black/40 rounded-lg">
                      <div className="flex-1">
                        <div className="font-semibold text-white">{log.filename}</div>
                        <div className="text-xs text-gray-400">
                          {(log.size / 1024).toFixed(2)} KB • {new Date(log.modified).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleViewLog(log.filename)}
                          className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded transition-colors text-sm"
                        >
                          <Eye className="w-4 h-4" />
                          View
                        </button>
                        <button
                          onClick={() => handleDownloadLog(log.filename)}
                          className="flex items-center gap-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded transition-colors text-sm"
                        >
                          <Download className="w-4 h-4" />
                          Download
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Log Viewer Modal */}
            {selectedLogContent && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/20 shadow-2xl"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold">{selectedLogFilename}</h3>
                  <button
                    onClick={() => {
                      setSelectedLogContent(null)
                      setSelectedLogFilename(null)
                    }}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                  >
                    Close
                  </button>
                </div>
                <div className="bg-black/40 rounded-lg p-4 h-96 overflow-y-auto font-mono text-xs text-gray-300 whitespace-pre-wrap">
                  {selectedLogContent}
                </div>
              </motion.div>
            )}
          </motion.div>
        )}

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
