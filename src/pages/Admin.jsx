import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { 
  Settings, 
  Activity, 
  DollarSign, 
  RefreshCw, 
  AlertCircle,
  CheckCircle,
  XCircle,
  BarChart3,
  Clock,
  Users,
  UserPlus,
  Edit,
  Trash2,
  Save,
  X
} from 'lucide-react'
import { getBalance } from '../services/api'
import { getAllUsers, createUser, deleteUser, getGlobalSettings, updateGlobalSettings } from '../services/admin'

function Admin() {
  const { isAdmin } = useAuth()
  const [balance, setBalance] = useState(null)
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [apiStatus, setApiStatus] = useState('unknown')
  const [users, setUsers] = useState([])
  const [usersLoading, setUsersLoading] = useState(false)
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    role: 'user',
    api_url: 'https://api.temporasms.com/stubs/handler_api.php',
    api_key: ''
  })
  const [globalSettings, setGlobalSettings] = useState({
    country_code: '22',
    operator: '1',
    service: 'pfk',
    price: 0.0
  })
  const [message, setMessage] = useState({ type: '', text: '' })

  useEffect(() => {
    if (isAdmin) {
      checkApiHealth()
      loadData()
      loadUsers()
      loadGlobalSettings()
      const interval = setInterval(loadData, 30000)
      return () => clearInterval(interval)
    }
  }, [isAdmin])

  const loadGlobalSettings = async () => {
    try {
      const result = await getGlobalSettings()
      if (result.success) {
        setGlobalSettings({
          country_code: result.settings.country_code || '22',
          operator: result.settings.operator || '1',
          service: result.settings.service || 'pfk',
          price: result.settings.price || 0.0
        })
      }
    } catch (error) {
      console.error('Failed to load global settings:', error)
    }
  }

  const handleUpdateGlobalSettings = async (e) => {
    e.preventDefault()
    setMessage({ type: '', text: '' })
    
    try {
      const result = await updateGlobalSettings(globalSettings)
      if (result.success) {
        setMessage({ type: 'success', text: 'Global settings updated successfully!' })
        loadData() // Reload data to reflect new settings
      } else {
        setMessage({ type: 'error', text: result.error || 'Failed to update global settings' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'An error occurred' })
    }
  }

  const checkApiHealth = async () => {
    try {
      const response = await fetch('/api/health')
      setApiStatus(response.ok ? 'online' : 'offline')
    } catch {
      setApiStatus('offline')
    }
  }

  const loadData = async () => {
    setLoading(true)
    try {
      const balanceData = await getBalance()
      
      if (balanceData.success) {
        setBalance(balanceData.balance)
      } else if (balanceData.error) {
        // Only show "not configured" if the error specifically says "not configured"
        // Don't show warning for "Invalid API key" - that means it's configured but wrong
        if (balanceData.error.includes('not configured') || balanceData.error.includes('not set')) {
          setMessage({ type: 'error', text: 'API key not configured. Please set your API key in Settings.' })
        } else if (balanceData.error.includes('Invalid API key')) {
          setMessage({ type: 'error', text: 'Invalid API key. Please check your API credentials in Settings.' })
        } else {
          setMessage({ type: 'error', text: balanceData.error })
        }
      }
      
      setLastUpdate(new Date())
      setApiStatus('online')
    } catch (error) {
      console.error('Failed to load data:', error)
      setApiStatus('offline')
    } finally {
      setLoading(false)
    }
  }

  const loadUsers = async () => {
    setUsersLoading(true)
    try {
      const result = await getAllUsers()
      if (result.success) {
        setUsers(result.users)
      }
    } catch (error) {
      console.error('Failed to load users:', error)
    } finally {
      setUsersLoading(false)
    }
  }

  const handleCreateUser = async (e) => {
    e.preventDefault()
    setMessage({ type: '', text: '' })
    
    try {
      const result = await createUser(newUser)
      if (result.success) {
        setMessage({ type: 'success', text: 'User created successfully!' })
        setShowCreateUser(false)
        setNewUser({ username: '', password: '', role: 'user', country_code: '22', operator: '1', service: 'pfk' })
        loadUsers()
      } else {
        setMessage({ type: 'error', text: result.error || 'Failed to create user' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'An error occurred' })
    }
  }


  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return
    
    try {
      const result = await deleteUser(userId)
      if (result.success) {
        setMessage({ type: 'success', text: 'User deleted successfully!' })
        loadUsers()
      } else {
        setMessage({ type: 'error', text: result.error || 'Failed to delete user' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'An error occurred' })
    }
  }

  if (!isAdmin) {
    return (
      <div className="pt-24 pb-12 px-6 text-center">
        <h1 className="text-2xl font-bold text-red-400">Access Denied</h1>
        <p className="text-gray-400 mt-2">Admin access required</p>
      </div>
    )
  }

  return (
    <div className="pt-20 sm:pt-24 pb-8 sm:pb-12 px-4 sm:px-6">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 sm:mb-8"
        >
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <div>
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Admin Panel
              </h1>
              <p className="text-sm sm:text-base text-gray-400">Monitor and manage your automation system</p>
            </div>
            <div className="flex items-center gap-2 sm:gap-4">
              <StatusBadge status={apiStatus} />
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={loadData}
                disabled={loading}
                className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold disabled:opacity-50 text-sm sm:text-base"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline">Refresh</span>
              </motion.button>
            </div>
          </div>
          {lastUpdate && (
            <p className="text-xs sm:text-sm text-gray-500 flex items-center gap-2">
              <Clock className="w-3 h-3 sm:w-4 sm:h-4" />
              Last updated: {lastUpdate.toLocaleTimeString()}
            </p>
          )}
        </motion.div>

        {/* Message */}
        {message.text && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`mb-4 p-3 rounded-lg flex items-center gap-2 ${
              message.type === 'success'
                ? 'bg-green-500/20 border border-green-500/50 text-green-400'
                : 'bg-red-500/20 border border-red-500/50 text-red-400'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              <XCircle className="w-5 h-5" />
            )}
            <span className="text-sm">{message.text}</span>
          </motion.div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <StatCard
            icon={<DollarSign />}
            label="Account Balance"
            value={balance !== null ? `₹${balance?.toFixed(2) || '0.00'}` : 'Loading...'}
            color="from-green-400 to-emerald-500"
            loading={loading}
          />
          <StatCard
            icon={<Activity />}
            label="API Status"
            value={apiStatus.toUpperCase()}
            color={apiStatus === 'online' ? 'from-blue-400 to-cyan-500' : 'from-red-400 to-pink-500'}
            loading={false}
          />
        </div>

        {/* Global Settings Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/20 shadow-2xl mb-4 sm:mb-6"
        >
          <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
            <div className="p-2 sm:p-3 bg-purple-500/20 rounded-lg">
              <Settings className="w-5 h-5 sm:w-6 sm:h-6 text-purple-400" />
            </div>
            <h2 className="text-xl sm:text-2xl font-bold">Global Settings</h2>
          </div>

          <form onSubmit={handleUpdateGlobalSettings} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
              <div>
                <label className="block text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                  Country Code
                </label>
                <input
                  type="text"
                  value={globalSettings.country_code}
                  onChange={(e) => setGlobalSettings({ ...globalSettings, country_code: e.target.value })}
                  className="w-full px-3 sm:px-4 py-2 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm sm:text-base"
                />
              </div>
              <div>
                <label className="block text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                  Operator
                </label>
                <input
                  type="text"
                  value={globalSettings.operator}
                  onChange={(e) => setGlobalSettings({ ...globalSettings, operator: e.target.value })}
                  className="w-full px-3 sm:px-4 py-2 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm sm:text-base"
                />
              </div>
              <div>
                <label className="block text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                  Service
                </label>
                <input
                  type="text"
                  value={globalSettings.service}
                  onChange={(e) => setGlobalSettings({ ...globalSettings, service: e.target.value })}
                  className="w-full px-3 sm:px-4 py-2 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm sm:text-base"
                />
              </div>
              <div>
                <label className="block text-xs sm:text-sm font-semibold text-gray-300 mb-2">
                  Price (₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={globalSettings.price}
                  onChange={(e) => setGlobalSettings({ ...globalSettings, price: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 sm:px-4 py-2 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm sm:text-base"
                  placeholder="0.00"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                className="px-4 sm:px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold text-sm sm:text-base flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Save Global Settings
              </button>
            </div>
          </form>
        </motion.div>

        {/* User Management Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/20 shadow-2xl mb-4 sm:mb-6"
        >
          <div className="flex items-center justify-between mb-4 sm:mb-6">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="p-2 sm:p-3 bg-blue-500/20 rounded-lg">
                <Users className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
              </div>
              <h2 className="text-xl sm:text-2xl font-bold">User Management</h2>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowCreateUser(!showCreateUser)}
              className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold text-sm sm:text-base"
            >
              <UserPlus className="w-4 h-4 sm:w-5 sm:h-5" />
              <span className="hidden sm:inline">Create User</span>
            </motion.button>
          </div>

          {/* Create User Form */}
          {showCreateUser && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mb-4 p-4 bg-black/40 rounded-lg border border-gray-700"
            >
              <form onSubmit={handleCreateUser} className="space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs sm:text-sm font-semibold text-gray-300 mb-1">Username</label>
                    <input
                      type="text"
                      value={newUser.username}
                      onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                      required
                      className="w-full px-3 py-2 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs sm:text-sm font-semibold text-gray-300 mb-1">Password</label>
                    <input
                      type="password"
                      value={newUser.password}
                      onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                      required
                      className="w-full px-3 py-2 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs sm:text-sm font-semibold text-gray-300 mb-1">Role</label>
                    <select
                      value={newUser.role}
                      onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                      className="w-full px-3 py-2 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm"
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs sm:text-sm font-semibold text-gray-300 mb-1">API URL</label>
                    <input
                      type="url"
                      value={newUser.api_url}
                      onChange={(e) => setNewUser({ ...newUser, api_url: e.target.value })}
                      className="w-full px-3 py-2 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm"
                      placeholder="https://api.temporasms.com/stubs/handler_api.php"
                    />
                  </div>
                  <div>
                    <label className="block text-xs sm:text-sm font-semibold text-gray-300 mb-1">API Key</label>
                    <input
                      type="text"
                      value={newUser.api_key}
                      onChange={(e) => setNewUser({ ...newUser, api_key: e.target.value })}
                      className="w-full px-3 py-2 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white text-sm"
                      placeholder="Optional"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    type="submit"
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold text-sm flex items-center gap-2"
                  >
                    <Save className="w-4 h-4" />
                    Create
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateUser(false)}
                    className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg font-semibold text-sm flex items-center gap-2"
                  >
                    <X className="w-4 h-4" />
                    Cancel
                  </button>
                </div>
              </form>
            </motion.div>
          )}

          {/* Users List */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 px-4 text-xs sm:text-sm text-gray-400 font-semibold">Username</th>
                  <th className="text-left py-3 px-4 text-xs sm:text-sm text-gray-400 font-semibold">Role</th>
                  <th className="text-left py-3 px-4 text-xs sm:text-sm text-gray-400 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {usersLoading ? (
                  <tr>
                    <td colSpan="3" className="py-8 text-center text-gray-400">
                      Loading users...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan="3" className="py-8 text-center text-gray-400">
                      No users found
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <UserRow
                      key={user._id}
                      user={user}
                      onDelete={handleDeleteUser}
                    />
                  ))
                )}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* System Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 sm:mt-6 bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/20 shadow-2xl"
        >
          <h3 className="text-lg sm:text-xl font-bold mb-3 sm:mb-4">System Information</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 text-xs sm:text-sm">
            <div>
              <span className="text-gray-400">API Endpoint:</span>
              <span className="ml-2 text-gray-300">http://localhost:5000</span>
            </div>
            <div>
              <span className="text-gray-400">Frontend:</span>
              <span className="ml-2 text-gray-300">http://localhost:3000</span>
            </div>
            <div>
              <span className="text-gray-400">Auto-refresh:</span>
              <span className="ml-2 text-gray-300">Every 30 seconds</span>
            </div>
            <div>
              <span className="text-gray-400">Status:</span>
              <span className={`ml-2 ${apiStatus === 'online' ? 'text-green-400' : 'text-red-400'}`}>
                {apiStatus === 'online' ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

function UserRow({ user, onDelete }) {
  return (
    <motion.tr
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
    >
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm sm:text-base">{user.username}</span>
          {user.role === 'admin' && (
            <span className="px-2 py-0.5 bg-purple-600/20 text-purple-400 text-xs rounded">Admin</span>
          )}
        </div>
      </td>
      <td className="py-3 px-4 text-sm sm:text-base text-gray-300 capitalize">{user.role}</td>
      <td className="py-3 px-4">
        <div className="flex gap-2">
          <button
            onClick={() => onDelete(user._id)}
            className="p-1.5 bg-red-600 hover:bg-red-700 rounded text-white"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </td>
    </motion.tr>
  )
}

function StatCard({ icon, label, value, color, loading }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.05, y: -5 }}
      className={`bg-gradient-to-br ${color} rounded-xl p-4 sm:p-6 backdrop-blur-sm border border-white/10 shadow-xl`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-white/80 text-xs sm:text-sm mb-1 truncate">{label}</p>
          {loading ? (
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="h-5 sm:h-6 w-20 sm:w-24 bg-white/20 rounded"
            />
          ) : (
            <p className="text-xl sm:text-2xl font-bold text-white truncate">{value}</p>
          )}
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

function StatusBadge({ status }) {
  const configs = {
    online: { 
      icon: CheckCircle, 
      bgClass: 'bg-green-500/20', 
      borderClass: 'border-green-500/50',
      textClass: 'text-green-400',
      text: 'Online' 
    },
    offline: { 
      icon: XCircle, 
      bgClass: 'bg-red-500/20', 
      borderClass: 'border-red-500/50',
      textClass: 'text-red-400',
      text: 'Offline' 
    },
    unknown: { 
      icon: AlertCircle, 
      bgClass: 'bg-yellow-500/20', 
      borderClass: 'border-yellow-500/50',
      textClass: 'text-yellow-400',
      text: 'Unknown' 
    }
  }
  
  const config = configs[status] || configs.unknown
  const Icon = config.icon
  
  return (
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 rounded-full ${config.bgClass} border ${config.borderClass}`}
    >
      <Icon className={`w-3 h-3 sm:w-4 sm:h-4 ${config.textClass}`} />
      <span className={`text-xs sm:text-sm font-semibold ${config.textClass}`}>{config.text}</span>
    </motion.div>
  )
}

export default Admin
