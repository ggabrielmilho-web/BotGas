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
          <div className="bg-white rounded-lg shadow-md p-6 max-w-md mx-auto">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">
              Sistema em Desenvolvimento
            </h2>
            <p className="text-gray-600">
              Frontend Next.js 14 configurado com sucesso!
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}