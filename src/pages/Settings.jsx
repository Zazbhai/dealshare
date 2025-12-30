import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { updateSettings } from '../services/auth'
import { Key, Save, CheckCircle, XCircle } from 'lucide-react'

function Settings() {
  const { user, updateSettings: updateUserSettings } = useAuth()
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [formData, setFormData] = useState({
    api_key: ''
  })

  useEffect(() => {
    if (user) {
      setFormData({
        api_key: user.api_key || ''
      })
    }
  }, [user])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage({ type: '', text: '' })

    try {
      const result = await updateSettings({
        api_key: formData.api_key
      })

      if (result.success) {
        // Update user context
        await updateUserSettings({
          api_key: formData.api_key
        })
        setMessage({ type: 'success', text: 'Settings updated successfully!' })
      } else {
        setMessage({ type: 'error', text: result.error || 'Failed to update settings' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'An error occurred' })
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="pt-20 sm:pt-24 pb-8 sm:pb-12 px-4 sm:px-6">
      <div className="container mx-auto max-w-4xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 sm:mb-8"
        >
          <h1 className="text-3xl sm:text-4xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            API Settings
          </h1>
          <p className="text-gray-400 text-sm sm:text-base">Manage your API credentials</p>
        </motion.div>

        {/* Settings Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-purple-500/20 shadow-2xl"
        >
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

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* API Key */}
            <div>
              <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-2">
                <Key className="w-4 h-4" />
                API Key
              </label>
              <input
                type="text"
                value={formData.api_key}
                onChange={(e) => handleChange('api_key', e.target.value)}
                required
                className="w-full px-4 py-3 bg-black/40 border border-gray-600 rounded-lg focus:outline-none focus:border-purple-500 text-white placeholder-gray-500 text-sm sm:text-base"
                placeholder="Enter your API key"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto px-6 sm:px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                  />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  Save Settings
                </>
              )}
            </button>
          </form>
        </motion.div>
      </div>
    </div>
  )
}

export default Settings

