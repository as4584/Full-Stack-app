
import './globals.css'
import type { Metadata } from 'next'
import Script from 'next/script'
import AeroBackground from '@/components/AeroBackground'

export const metadata: Metadata = {
    title: 'AI Receptionist Dashboard',
    description: 'Manage your AI receptionist',
}

/**
 * ROOT LAYOUT - MUST ALWAYS RENDER CHILDREN
 * This is a server component - NO client hooks allowed
 * ErrorBoundaries and Suspense are in child components
 */
export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <body>
                <AeroBackground />
                {children}
                
                {/* White screen failsafe - last resort fallback */}
                <Script
                    src="/white-screen-failsafe.js"
                    strategy="afterInteractive"
                />
            </body>
        </html>
    )
}
