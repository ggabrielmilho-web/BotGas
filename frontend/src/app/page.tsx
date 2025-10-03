import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🤖 GasBot
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Sistema SaaS de Atendimento Automatizado para Distribuidoras via WhatsApp
          </p>

          {/* CTA Principal */}
          <div className="mb-12">
            <Link
              href="/auth"
              className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Começar Agora - 7 Dias Grátis
            </Link>
            <p className="text-sm text-gray-600 mt-2">Sem cartão de crédito</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto mt-12">
            <Link href="/onboarding" className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                📋 Onboarding
              </h2>
              <p className="text-gray-600">
                Configure sua distribuidora em 5 passos simples
              </p>
            </Link>

            <Link href="/dashboard" className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                📊 Dashboard
              </h2>
              <p className="text-gray-600">
                Gerencie pedidos e conversas em tempo real
              </p>
            </Link>

            <Link href="/plans" className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                💳 Planos
              </h2>
              <p className="text-gray-600">
                Escolha o plano ideal para seu negócio
              </p>
            </Link>
          </div>

          <div className="mt-12 max-w-2xl mx-auto">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                ✅ Sistema Funcional
              </h3>
              <ul className="text-left text-gray-600 space-y-2">
                <li>✅ Backend API rodando (porta 8000)</li>
                <li>✅ Banco de dados configurado</li>
                <li>✅ Evolution API conectada</li>
                <li>✅ Ngrok túnel ativo para webhooks</li>
                <li>✅ Sistema de trial (7 dias)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}