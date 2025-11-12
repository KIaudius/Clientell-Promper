import React, { useState } from 'react'
import Step1Credentials from './components/Step1Credentials'
import Step2UseCases from './components/Step2UseCases'
import Step3Download from './components/Step3Download'
import { Sparkles } from 'lucide-react'

function App() {
  const [currentStep, setCurrentStep] = useState(1)
  const [sessionData, setSessionData] = useState({
    sessionId: null,
    useCases: [],
    metadataSummary: {},
    generatedPrompts: []
  })

  const handleStep1Complete = (data) => {
    setSessionData(prev => ({
      ...prev,
      sessionId: data.session_id,
      useCases: data.use_cases,
      metadataSummary: data.metadata_summary
    }))
    setCurrentStep(2)
  }

  const handleStep2Complete = (data) => {
    setSessionData(prev => ({
      ...prev,
      generatedPrompts: data.prompts
    }))
    setCurrentStep(3)
  }

  const handleReset = () => {
    setCurrentStep(1)
    setSessionData({
      sessionId: null,
      useCases: [],
      metadataSummary: {},
      generatedPrompts: []
    })
  }

  return (
    <div className="min-h-screen py-12 px-4">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-12">
        <div className="text-center">
          <div className="flex items-center justify-center mb-4">
            <Sparkles className="w-12 h-12 text-blue-600 mr-3" />
            <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Salesforce Test Prompt Generator
            </h1>
          </div>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Generate intelligent, context-aware test prompts for your Salesforce organization
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center justify-center mt-8 space-x-4">
          {[1, 2, 3].map((step) => (
            <React.Fragment key={step}>
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all duration-300 ${
                    currentStep >= step
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                      : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {step}
                </div>
                <span className="text-xs mt-2 text-gray-600 font-medium">
                  {step === 1 && 'Connect'}
                  {step === 2 && 'Configure'}
                  {step === 3 && 'Download'}
                </span>
              </div>
              {step < 3 && (
                <div
                  className={`h-1 w-16 rounded transition-all duration-300 ${
                    currentStep > step ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        {currentStep === 1 && (
          <Step1Credentials onComplete={handleStep1Complete} />
        )}
        {currentStep === 2 && (
          <Step2UseCases
            sessionData={sessionData}
            onComplete={handleStep2Complete}
            onBack={() => setCurrentStep(1)}
          />
        )}
        {currentStep === 3 && (
          <Step3Download
            sessionData={sessionData}
            onReset={handleReset}
          />
        )}
      </div>

      {/* Footer */}
      <div className="max-w-7xl mx-auto mt-16 text-center text-gray-500 text-sm">
        <p>Powered by Claude AI & FastAPI</p>
        <p className="mt-1">Your credentials are never stored and are only used for this session</p>
      </div>
    </div>
  )
}

export default App
