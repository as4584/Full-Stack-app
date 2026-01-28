/**
 * APP LAYOUT - Pure Server Component
 * 
 * CRITICAL: This MUST be a pure server component with:
 * - NO 'use client' directive
 * - NO hooks (useState, useEffect, useRouter)
 * - NO conditional rendering based on auth
 * - NO data fetching
 * 
 * Auth protection is handled by individual pages using <AuthGate>
 * This ensures server HTML always matches first client render.
 */

import AppLayoutClient from '@/components/AppLayoutClient';

export default function AppLayout({ children }: { children: React.ReactNode }) {
    // Pure passthrough - no logic, no conditionals
    return (
        <AppLayoutClient>
            {children}
        </AppLayoutClient>
    );
}
