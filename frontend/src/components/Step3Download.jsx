import React, { useState } from 'react'
import axios from 'axios'
import { Download, FileJson, FileSpreadsheet, CheckCircle, RefreshCw, Sparkles, Eye } from 'lucide-react'

function Step3Download({ sessionData, onReset }) {
  const [selectedFormat, setSelectedFormat] = useState('json')
  const [downloading, setDownloading] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  const handleDownload = async () => {
    setDownloading(true)
    try {
      const response = await axios.get(
        `/api/download/${sessionData.sessionId}/${selectedFormat}`,
        { responseType: 'blob' }
      )

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      const extension = selectedFormat === 'json' ? 'json' : 'csv'
      link.setAttribute('download', `test_prompts_${Date.now()}.${extension}`)
      document.body.appendChild(link)
      link.click()
      link.remove()

      // Cleanup session after download
      await axios.delete(`/api/cleanup/${sessionData.sessionId}`)
    } catch (error) {
      console.error('Download failed:', error)
      alert('Failed to download file. Please try again.')
    } finally {
      setDownloading(false)
    }
  }

  const totalPrompts = sessionData.generatedPrompts?.length || 0

  // Group prompts by use case for preview
  const promptsByUseCase = sessionData.generatedPrompts?.reduce((acc, prompt) => {
    if (!acc[prompt.use_case]) {
      acc[prompt.use_case] = []
    }
    acc[prompt.use_case].push(prompt)
    return acc
  }, {})

  return (
    <div className="space-y-6">
      {/* Success Card */}
      <div className="glass-card rounded-2xl p-8 text-center">
        <div className="flex justify-center mb-4">
          <div className="bg-green-100 rounded-full p-4">
            <CheckCircle className="w-16 h-16 text-green-600" />
          </div>
        </div>

        <h2 className="section-title mb-3">Generation Complete!</h2>
        <p className="text-gray-600 text-lg mb-6">
          Successfully generated <span className="font-bold text-blue-600">{totalPrompts}</span> test prompts
        </p>

        {/* Stats Grid */}
        <div className="grid md:grid-cols-3 gap-4 max-w-2xl mx-auto mb-8">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4">
            <Sparkles className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-800">{totalPrompts}</p>
            <p className="text-sm text-gray-600">Test Prompts</p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4">
            <FileJson className="w-8 h-8 text-purple-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-800">
              {Object.keys(promptsByUseCase || {}).length}
            </p>
            <p className="text-sm text-gray-600">Use Cases</p>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4">
            <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-800">Ready</p>
            <p className="text-sm text-gray-600">To Download</p>
          </div>
        </div>
      </div>

      {/* Download Options */}
      <div className="glass-card rounded-2xl p-8">
        <h3 className="text-2xl font-bold text-gray-800 mb-6">Choose Download Format</h3>

        <div className="grid md:grid-cols-2 gap-4 mb-6">
          {/* JSON Option */}
          <button
            onClick={() => setSelectedFormat('json')}
            className={`p-6 rounded-xl border-2 transition-all duration-200 text-left ${
              selectedFormat === 'json'
                ? 'border-blue-600 bg-blue-50 shadow-lg'
                : 'border-gray-200 hover:border-blue-300 bg-white'
            }`}
          >
            <div className="flex items-center space-x-3 mb-3">
              <FileJson className={`w-8 h-8 ${selectedFormat === 'json' ? 'text-blue-600' : 'text-gray-400'}`} />
              <div>
                <h4 className="font-bold text-lg text-gray-800">JSON Format</h4>
                <p className="text-sm text-gray-600">Structured data with metadata</p>
              </div>
            </div>
            <ul className="text-sm text-gray-600 space-y-1 ml-11">
              <li>• Complete metadata included</li>
              <li>• Easy to parse programmatically</li>
              <li>• Best for automation</li>
            </ul>
          </button>

          {/* CSV Option */}
          <button
            onClick={() => setSelectedFormat('csv')}
            className={`p-6 rounded-xl border-2 transition-all duration-200 text-left ${
              selectedFormat === 'csv'
                ? 'border-blue-600 bg-blue-50 shadow-lg'
                : 'border-gray-200 hover:border-blue-300 bg-white'
            }`}
          >
            <div className="flex items-center space-x-3 mb-3">
              <FileSpreadsheet className={`w-8 h-8 ${selectedFormat === 'csv' ? 'text-blue-600' : 'text-gray-400'}`} />
              <div>
                <h4 className="font-bold text-lg text-gray-800">CSV Format</h4>
                <p className="text-sm text-gray-600">Spreadsheet-friendly format</p>
              </div>
            </div>
            <ul className="text-sm text-gray-600 space-y-1 ml-11">
              <li>• Open in Excel/Google Sheets</li>
              <li>• Easy to review and edit</li>
              <li>• Best for manual testing</li>
            </ul>
          </button>
        </div>

        {/* Preview Toggle */}
        <button
          onClick={() => setShowPreview(!showPreview)}
          className="btn-secondary w-full mb-6 flex items-center justify-center"
        >
          <Eye className="w-4 h-4 mr-2" />
          {showPreview ? 'Hide Preview' : 'Preview Results'}
        </button>

        {/* Preview Section */}
        {showPreview && (
          <div className="mb-6 max-h-96 overflow-y-auto bg-gray-50 rounded-lg p-4 border border-gray-200">
            {Object.entries(promptsByUseCase || {}).map(([useCase, prompts]) => (
              <div key={useCase} className="mb-4">
                <h4 className="font-semibold text-gray-800 mb-2">{useCase}</h4>
                <div className="space-y-2">
                  {prompts.slice(0, 3).map((prompt, idx) => (
                    <div key={idx} className="bg-white p-3 rounded border border-gray-200">
                      <p className="text-sm text-gray-700 mb-1">"{prompt.prompt}"</p>
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                          {prompt.difficulty}
                        </span>
                        {prompt.expected_object && (
                          <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                            {prompt.expected_object}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                  {prompts.length > 3 && (
                    <p className="text-sm text-gray-500 italic">
                      + {prompts.length - 3} more prompts...
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-4">
          <button
            onClick={onReset}
            className="btn-secondary flex items-center"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Start Over
          </button>

          <button
            onClick={handleDownload}
            disabled={downloading}
            className="btn-primary flex-1 flex items-center justify-center"
          >
            {downloading ? (
              <>
                <Download className="w-5 h-5 mr-2 animate-bounce" />
                Downloading...
              </>
            ) : (
              <>
                <Download className="w-5 h-5 mr-2" />
                Download {selectedFormat.toUpperCase()}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Info Card */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-6 text-white">
        <h4 className="font-semibold text-lg mb-2">What's Next?</h4>
        <ul className="space-y-2 text-blue-50">
          <li>• Use these prompts to test your Salesforce AI agents</li>
          <li>• Track which prompts succeed and which fail</li>
          <li>• Iterate and generate more prompts for edge cases</li>
          <li>• Your session data is automatically cleaned up after download</li>
        </ul>
      </div>
    </div>
  )
}

export default Step3Download
