import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Escola Saudável - Plataforma de Saúde Escolar',
  description: 'Gerencie a saúde de seus alunos',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  )
}
