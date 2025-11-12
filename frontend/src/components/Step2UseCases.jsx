import React, { useState } from 'react'
import axios from 'axios'
import { Loader2, CheckCircle, Settings, ArrowLeft, Info } from 'lucide-react'

function Step2UseCases({ sessionData, onComplete, onBack }) {
  const [useCases, setUseCases] = useState(
    sessionData.useCases.map(uc => ({ ...uc }))
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handlePromptCountChange = (id, newCount) => {
    setUseCases(prev =>
      prev.map(uc =>
        uc.id === id ? { ...uc, prompt_count: parseInt(newCount) || 1 } : uc
      )
    )
  }

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post('/api/step2-generate-prompts', {
        session_id: sessionData.sessionId,
        use_cases: useCases
      })

      onComplete(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate prompts')
    } finally {
      setLoading(false)
    }
  }

  const totalPrompts = useCases.reduce((sum, uc) => sum + (uc.prompt_count || 0), 0)

  return (
    <div className="space-y-6">
      {/* Metadata Summary Card */}
      <div className="glass-card rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-800">Organization Summary</h2>
          <CheckCircle className="w-6 h-6 text-green-600" />
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Organization</p>
            <p className="text-xl font-bold text-gray-800">
              {sessionData.metadataSummary.org_name || 'Connected'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {sessionData.metadataSummary.is_sandbox ? 'Sandbox' : 'Production'}
            </p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Custom Objects</p>
            <p className="text-xl font-bold text-gray-800">
              {sessionData.metadataSummary.custom_objects || 0}
            </p>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Total Flows</p>
            <p className="text-xl font-bold text-gray-800">
              {sessionData.metadataSummary.total_flows || 0}
            </p>
          </div>
        </div>
      </div>

      {/* Use Cases Configuration */}
      <div className="glass-card rounded-2xl p-8">
        <div className="mb-6">
          <div className="flex items-center space-x-2 mb-2">
            <Settings className="w-6 h-6 text-blue-600" />
            <h2 className="section-title">Configure Test Cases</h2>
          </div>
          <p className="text-gray-600">
            Adjust the number of test prompts for each use case
          </p>
        </div>

        <div className="space-y-4">
          {useCases.map((useCase, index) => (
            <div
              key={useCase.id}
              className="bg-gradient-to-r from-white to-blue-50/30 border border-blue-100 rounded-xl p-5 hover:shadow-md transition-all duration-200"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
                      {index + 1}
                    </span>
                    <h3 className="text-lg font-semibold text-gray-800">
                      {useCase.name}
                    </h3>
                  </div>
                  <p className="text-gray-600 text-sm ml-11">
                    {useCase.description}
                  </p>
                </div>

                <div className="ml-4 flex items-center space-x-3">
                  <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
                    Prompts:
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={useCase.prompt_count}
                    onChange={(e) => handlePromptCountChange(useCase.id, e.target.value)}
                    className="w-20 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center font-semibold"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="mt-6 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm mb-1">Total Test Prompts</p>
              <p className="text-4xl font-bold">{totalPrompts}</p>
            </div>
            <Info className="w-12 h-12 text-blue-200" />
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 font-medium">Error: {error}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-8 flex space-x-4">
          <button
            onClick={onBack}
            className="btn-secondary flex items-center"
            disabled={loading}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </button>

          <button
            onClick={handleGenerate}
            disabled={loading || totalPrompts === 0}
            className="btn-primary flex-1 flex items-center justify-center"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Generating {totalPrompts} prompts...
              </>
            ) : (
              `Generate ${totalPrompts} Test Prompts`
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Step2UseCases
