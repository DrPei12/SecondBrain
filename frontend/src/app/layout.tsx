import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Second Brain',
  description: 'Personal Knowledge Management Platform',
  icons: {
    icon: '/favicon.svg',
    apple: '/favicon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh">
      <body className="min-h-screen bg-gray-50">
        {children}
      </body>
    </html>
  )
}
