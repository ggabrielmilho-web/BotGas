'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { whatsappApi } from '@/lib/api'
import Image from 'next/image'

interface WhatsAppSetupStepProps {
  onComplete: () => void
}

export default function WhatsAppSetupStep({ onComplete }: WhatsAppSetupStepProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [qrCode, setQrCode] = useState('')
  const [connected, setConnected] = useState(false)
  const [checkingStatus, setCheckingStatus] = useState(false)

  useEffect(() => {
    checkStatus()
  }, [])

  const checkStatus = async () => {
    setCheckingStatus(true)
    try {
      const status = await whatsappApi.getStatus()
      setConnected(status.connected)
      if (status.connected) {
        onComplete()
      }
    } catch (err) {
      console.error('Erro ao verificar status:', err)
    } finally {
      setCheckingStatus(false)
    }
  }

  const generateQRCode = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await whatsappApi.getQRCode()
      setQrCode(response.qr_code)

      // Poll status a cada 3 segundos
      const interval = setInterval(async () => {
        try {
          const status = await whatsappApi.getStatus()
          if (status.connected) {
            setConnected(true)
            clearInterval(interval)
            onComplete()
          }
        } catch (err) {
          console.error('Erro ao verificar status:', err)
        }
      }, 3000)

      // Limpar interval após 2 minutos
      setTimeout(() => clearInterval(interval), 120000)
    } catch (err: any) {
      setError(err.message || 'Erro ao gerar QR Code')
    } finally {
      setLoading(false)
    }
  }

  if (connected) {
    return (
      <div className="text-center py-8">
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-10 h-10 text-green-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <h3 className="text-2xl font-semibold text-gray-900 mb-2">
          WhatsApp Conectado!
        </h3>
        <p className="text-gray-600 mb-6">
          Seu WhatsApp está conectado e pronto para receber mensagens.
        </p>
        <Button onClick={() => window.location.reload()}>
          Reconectar
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
        <h4 className="font-medium text-yellow-900 mb-2">Atenção!</h4>
        <ul className="text-sm text-yellow-800 space-y-1">
          <li>• Use um número exclusivo para o bot (não use seu WhatsApp pessoal)</li>
          <li>• O número ficará conectado 24/7 ao sistema</li>
          <li>• Recomendamos um chip separado ou WhatsApp Business</li>
        </ul>
      </div>

      {!qrCode && (
        <div className="text-center py-8">
          <div className="w-32 h-32 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-16 h-16 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Conectar WhatsApp
          </h3>
          <p className="text-gray-600 mb-6">
            Clique no botão abaixo para gerar o QR Code e conectar seu WhatsApp
          </p>
          <Button
            onClick={generateQRCode}
            disabled={loading || checkingStatus}
            size="lg"
          >
            {loading ? 'Gerando QR Code...' : checkingStatus ? 'Verificando...' : 'Gerar QR Code'}
          </Button>
        </div>
      )}

      {qrCode && (
        <div className="space-y-4">
          <div className="bg-white border-2 border-gray-200 rounded-lg p-6 text-center">
            <h3 className="text-lg font-semibold mb-4">
              Escaneie o QR Code com seu WhatsApp
            </h3>
            <div className="flex justify-center mb-4">
              {qrCode.startsWith('data:image') ? (
                <img
                  src={qrCode}
                  alt="QR Code WhatsApp"
                  className="w-64 h-64"
                />
              ) : (
                <div className="w-64 h-64 bg-gray-100 flex items-center justify-center">
                  <p className="text-sm text-gray-500">Gerando QR Code...</p>
                </div>
              )}
            </div>
            <div className="flex items-center justify-center text-sm text-gray-600">
              <div className="animate-pulse flex items-center">
                <div className="w-2 h-2 bg-blue-600 rounded-full mr-2"></div>
                Aguardando conexão...
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h4 className="font-medium text-blue-900 mb-2">Como conectar:</h4>
            <ol className="text-sm text-blue-800 space-y-2">
              <li>1. Abra o WhatsApp no seu celular</li>
              <li>2. Toque em Menu (⋮) ou Configurações</li>
              <li>3. Toque em "Aparelhos conectados"</li>
              <li>4. Toque em "Conectar um aparelho"</li>
              <li>5. Aponte seu celular para esta tela e escaneie o QR Code</li>
            </ol>
          </div>

          <Button
            onClick={generateQRCode}
            variant="outline"
            className="w-full"
            disabled={loading}
          >
            Gerar Novo QR Code
          </Button>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      <div className="text-center">
        <Button variant="ghost" onClick={checkStatus} disabled={checkingStatus}>
          {checkingStatus ? 'Verificando...' : 'Verificar Status'}
        </Button>
      </div>
    </div>
  )
}
