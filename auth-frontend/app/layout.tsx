import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'Login - AI Receptionist',
    description: 'Sign in to your AI Receptionist account',
};

/**
 * AUTH APP ROOT LAYOUT
 * 
 * This is a MINIMAL layout with:
 * - No shared components with dashboard
 * - No auth logic
 * - No Suspense boundaries
 * - No client-side hooks
 * 
 * The auth app is completely isolated from the dashboard app.
 */
export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
