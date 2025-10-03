'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { authApi, setAuthToken } from '@/lib/api'

export default function AuthPage() {
  const router = useRouter()
  const [isLogin, setIsLogin] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Login form
  const [loginData, setLoginData] = useState({
    email: '',
    password: '',
  })

  // Register form
  const [registerData, setRegisterData] = useState({
    company_name: '',
    email: '',
    password: '',
    phone: '',
    full_name: '',
  })

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await authApi.login(loginData)
      setAuthToken(response.access_token)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Erro ao fazer login')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await authApi.register(registerData)
      setAuthToken(response.access_token)
      // Redireciona para onboarding após registro
      router.push('/onboarding')
    } catch (err: any) {
      setError(err.message || 'Erro ao criar conta')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">🤖 GasBot</h1>
          <p className="text-gray-600">
            Sistema de Atendimento Automatizado via WhatsApp
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{isLogin ? 'Entrar' : 'Criar Conta'}</CardTitle>
            <CardDescription>
              {isLogin
                ? 'Acesse seu dashboard'
                : 'Comece seu trial gratuito de 7 dias'}
            </CardDescription>
          </CardHeader>

          <CardContent>
            {/* Login Form */}
            {isLogin ? (
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="seu@email.com"
                    value={loginData.email}
                    onChange={(e) =>
                      setLoginData({ ...loginData, email: e.target.value })
                    }
                    required
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="password">Senha</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={loginData.password}
                    onChange={(e) =>
                      setLoginData({ ...loginData, password: e.target.value })
                    }
                    required
                    className="mt-1"
                  />
                </div>

                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                )}

                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? 'Entrando...' : 'Entrar'}
                </Button>
              </form>
            ) : (
              /* Register Form */
              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <Label htmlFor="company_name">
                    Nome da Empresa <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="company_name"
                    type="text"
                    placeholder="Distribuidora Exemplo"
                    value={registerData.company_name}
                    onChange={(e) =>
                      setRegisterData({
                        ...registerData,
                        company_name: e.target.value,
                      })
                    }
                    required
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="full_name">
                    Seu Nome <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="full_name"
                    type="text"
                    placeholder="João Silva"
                    value={registerData.full_name}
                    onChange={(e) =>
                      setRegisterData({
                        ...registerData,
                        full_name: e.target.value,
                      })
                    }
                    required
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="phone">
                    Telefone <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="(11) 99999-9999"
                    value={registerData.phone}
                    onChange={(e) =>
                      setRegisterData({ ...registerData, phone: e.target.value })
                    }
                    required
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="reg_email">
                    Email <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="reg_email"
                    type="email"
                    placeholder="seu@email.com"
                    value={registerData.email}
                    onChange={(e) =>
                      setRegisterData({ ...registerData, email: e.target.value })
                    }
                    required
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="reg_password">
                    Senha <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="reg_password"
                    type="password"
                    placeholder="Mínimo 6 caracteres"
                    value={registerData.password}
                    onChange={(e) =>
                      setRegisterData({
                        ...registerData,
                        password: e.target.value,
                      })
                    }
                    required
                    minLength={6}
                    className="mt-1"
                  />
                </div>

                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                )}

                <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                  <p className="text-sm text-blue-800">
                    ✨ Trial gratuito de 7 dias • Sem cartão de crédito
                  </p>
                </div>

                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? 'Criando conta...' : 'Criar Conta Grátis'}
                </Button>
              </form>
            )}

            {/* Toggle Login/Register */}
            <div className="mt-6 text-center">
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin)
                  setError('')
                }}
                className="text-sm text-blue-600 hover:underline"
              >
                {isLogin
                  ? 'Não tem conta? Criar conta grátis'
                  : 'Já tem conta? Fazer login'}
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="text-center text-sm text-gray-600 mt-6">
          Precisa de ajuda?{' '}
          <a href="#" className="text-blue-600 hover:underline">
            Fale conosco
          </a>
        </p>
      </div>
    </div>
  )
}
