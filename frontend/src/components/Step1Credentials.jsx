import React, { useState } from 'react'
import axios from 'axios'
import { Loader2, Lock, FileText, Upload, AlertCircle } from 'lucide-react'

function Step1Credentials({ onComplete }) {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    securityToken: '',
    domain: 'test',
    anthropicApiKey: '',
    useCaseDescription: ''
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [uploadedFile, setUploadedFile] = useState(null)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleFileUpload = (e) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        const content = event.target.result
        setFormData(prev => ({
          ...prev,
          useCaseDescription: prev.useCaseDescription + '\n\n' + content
        }))
        setUploadedFile(file.name)
      }
      reader.readAsText(file)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post('/api/step1-extract', {
        credentials: {
          username: formData.username,
          password: formData.password,
          security_token: formData.securityToken,
          domain: formData.domain,
          anthropic_api_key: formData.anthropicApiKey
        },
        use_case_description: formData.useCaseDescription
      })

      onComplete(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to connect. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="glass-card rounded-2xl p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="section-title mb-2">Connect to Salesforce</h2>
        <p className="text-gray-600">
          Enter your Salesforce credentials and describe your testing use cases
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Salesforce Credentials Section */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2 mb-3">
            <Lock className="w-5 h-5 text-blue-600" />
            <h3 className="text-xl font-semibold text-gray-800">Salesforce Credentials</h3>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                className="input-field"
                placeholder="user@example.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className="input-field"
                placeholder="••••••••"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Security Token
              </label>
              <input
                type="password"
                name="securityToken"
                value={formData.securityToken}
                onChange={handleInputChange}
                className="input-field"
                placeholder="••••••••••••••••"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Environment
              </label>
              <select
                name="domain"
                value={formData.domain}
                onChange={handleInputChange}
                className="input-field"
              >
                <option value="test">Sandbox</option>
                <option value="login">Production</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Anthropic API Key
            </label>
            <input
              type="password"
              name="anthropicApiKey"
              value={formData.anthropicApiKey}
              onChange={handleInputChange}
              className="input-field"
              placeholder="sk-ant-......"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Get your API key from{' '}
              <a
                href="https://console.anthropic.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                console.anthropic.com
              </a>
            </p>
          </div>
        </div>

        {/* Use Case Description Section */}
        <div className="space-y-4 pt-6 border-t border-gray-200">
          <div className="flex items-center space-x-2 mb-3">
            <FileText className="w-5 h-5 text-blue-600" />
            <h3 className="text-xl font-semibold text-gray-800">Use Case Description</h3>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Describe your testing scenarios
            </label>
            <textarea
              name="useCaseDescription"
              value={formData.useCaseDescription}
              onChange={handleInputChange}
              className="input-field min-h-[150px]"
              placeholder="Example: We need to test insurance policy queries, commission calculations for agents, and opportunity tracking for the sales team..."
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Describe what you want to test in your Salesforce org
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Or upload a use case file (optional)
            </label>
            <div className="flex items-center space-x-3">
              <label className="btn-secondary cursor-pointer inline-flex items-center">
                <Upload className="w-4 h-4 mr-2" />
                Upload File
                <input
                  type="file"
                  accept=".txt,.md,.doc,.docx"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
              {uploadedFile && (
                <span className="text-sm text-green-600 font-medium">
                  ✓ {uploadedFile}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-800 font-medium">Connection Error</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="btn-primary w-full flex items-center justify-center"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Extracting metadata...
            </>
          ) : (
            'Connect & Extract Metadata'
          )}
        </button>
      </form>

      {/* Security Notice */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          🔒 <strong>Security:</strong> Your credentials are processed in-memory and never stored.
          All data is deleted after your session ends.
        </p>
      </div>
    </div>
  )
}

export default Step1Credentials
