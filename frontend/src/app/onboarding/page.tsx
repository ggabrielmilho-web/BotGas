'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import CompanyInfoStep from '@/components/onboarding/CompanyInfoStep'
import WhatsAppSetupStep from '@/components/onboarding/WhatsAppSetupStep'
import ProductsSetupStep from '@/components/onboarding/ProductsSetupStep'
import DeliverySetupStep from '@/components/onboarding/DeliverySetupStep'
import PaymentSetupStep from '@/components/onboarding/PaymentSetupStep'

const STEPS = [
  { id: 1, title: 'Dados da Empresa', description: 'Informações básicas' },
  { id: 2, title: 'WhatsApp', description: 'Conectar WhatsApp' },
  { id: 3, title: 'Produtos', description: 'Cadastrar produtos' },
  { id: 4, title: 'Entrega', description: 'Configurar áreas de entrega' },
  { id: 5, title: 'Pagamento', description: 'Formas de pagamento' },
]

export default function OnboardingPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [completedSteps, setCompletedSteps] = useState<number[]>([])

  const handleNext = () => {
    if (!completedSteps.includes(currentStep)) {
      setCompletedSteps([...completedSteps, currentStep])
    }

    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1)
    } else {
      // Onboarding completo, redirecionar para dashboard
      router.push('/dashboard')
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSkip = () => {
    handleNext()
  }

  const handleStepComplete = () => {
    if (!completedSteps.includes(currentStep)) {
      setCompletedSteps([...completedSteps, currentStep])
    }
  }

  const currentStepData = STEPS.find(s => s.id === currentStep)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Bem-vindo ao GasBot!
          </h1>
          <p className="text-lg text-gray-600">
            Vamos configurar seu atendimento automatizado em 5 passos simples
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center">
                  <div
                    className={`
                      w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold
                      transition-all duration-300
                      ${
                        completedSteps.includes(step.id)
                          ? 'bg-green-500 text-white'
                          : step.id === currentStep
                          ? 'bg-blue-600 text-white ring-4 ring-blue-200'
                          : 'bg-gray-200 text-gray-500'
                      }
                    `}
                  >
                    {completedSteps.includes(step.id) ? '✓' : step.id}
                  </div>
                  <span className="text-xs text-gray-600 mt-2 text-center hidden sm:block">
                    {step.title}
                  </span>
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={`
                      flex-1 h-1 mx-2 transition-all duration-300
                      ${
                        completedSteps.includes(step.id)
                          ? 'bg-green-500'
                          : 'bg-gray-200'
                      }
                    `}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content Card */}
        <Card className="shadow-xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl">{currentStepData?.title}</CardTitle>
                <CardDescription className="text-base mt-1">
                  {currentStepData?.description}
                </CardDescription>
              </div>
              <span className="text-sm text-gray-500">
                Passo {currentStep} de {STEPS.length}
              </span>
            </div>
          </CardHeader>

          <CardContent>
            {/* Render current step component */}
            {currentStep === 1 && (
              <CompanyInfoStep onComplete={handleStepComplete} />
            )}
            {currentStep === 2 && (
              <WhatsAppSetupStep onComplete={handleStepComplete} />
            )}
            {currentStep === 3 && (
              <ProductsSetupStep onComplete={handleStepComplete} />
            )}
            {currentStep === 4 && (
              <DeliverySetupStep onComplete={handleStepComplete} />
            )}
            {currentStep === 5 && (
              <PaymentSetupStep onComplete={handleStepComplete} />
            )}

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t">
              <Button
                variant="outline"
                onClick={handleBack}
                disabled={currentStep === 1}
              >
                Voltar
              </Button>

              <div className="flex gap-2">
                {currentStep < STEPS.length && (
                  <Button variant="ghost" onClick={handleSkip}>
                    Pular
                  </Button>
                )}

                <Button onClick={handleNext}>
                  {currentStep === STEPS.length ? 'Finalizar' : 'Próximo'}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Help Text */}
        <div className="text-center mt-6 text-sm text-gray-600">
          <p>
            Precisa de ajuda?{' '}
            <a href="#" className="text-blue-600 hover:underline">
              Acesse nossa central de suporte
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
