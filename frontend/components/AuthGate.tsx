'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

/**
 * AUTH GATE - Client-only authentication guard
 * 
 * CRITICAL: This component prevents hydration mismatches by:
 * 1. Rendering the SAME loading UI on server SSR and first client render
 * 2. Checking auth state ONLY in useEffect (client-side only)
 * 3. NEVER returning null during hydration
 * 4. Handling ALL auth redirects client-side (middleware does nothing)
 * 
 * This ensures server HTML matches client HTML on first render,
 * eliminating React hydration errors that cause white screens.
 * 
 * Why this works:
 * - Server renders: <AuthGate> → loading UI
 * - Client first render: <AuthGate> → same loading UI (no mismatch!)
 * - Client after useEffect: check auth → redirect OR show children
 */

// Auth app URL - completely separate Next.js app
const AUTH_URL = process.env.NEXT_PUBLIC_AUTH_URL || 'https://auth.lexmakesit.com';

interface AuthGateProps {
    children: React.ReactNode;
    fallback?: React.ReactNode;
}

// API URL for auth check
const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api.lexmakesit.com';

export default function AuthGate({ children, fallback }: AuthGateProps) {
    const router = useRouter();
    const [isChecking, setIsChecking] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    useEffect(() => {
        // Auth check runs ONLY on client, AFTER first render
        const checkAuth = async () => {
            try {
                // Call the /api/auth/me endpoint to verify authentication
                // This works because the HttpOnly cookie is sent automatically
                const response = await fetch(`${API_URL}/api/auth/me`, {
                    method: 'GET',
                    credentials: 'include', // CRITICAL: Send cookies with request
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });
                
                if (response.ok) {
                    // User is authenticated
                    console.log('[AuthGate] User authenticated via /api/auth/me');
                    setIsAuthenticated(true);
                    setIsChecking(false);
                } else {
                    // Not authenticated - redirect to auth app
                    console.log('[AuthGate] Not authenticated, redirecting to auth app');
                    window.location.href = `${AUTH_URL}/login`;
                }
            } catch (error) {
                // Network error or other issue - redirect to login
                console.error('[AuthGate] Auth check failed:', error);
                window.location.href = `${AUTH_URL}/login`;
            }
        };

        // Run auth check after component mounts
        const timer = setTimeout(checkAuth, 50);
        return () => clearTimeout(timer);
    }, [router]);

    // CRITICAL: Always render visible UI during hydration
    // Never return null - this causes hydration mismatches
    if (isChecking) {
        return fallback || (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '100vh',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                fontFamily: 'system-ui, -apple-system, sans-serif'
            }}>
                <div style={{
                    textAlign: 'center',
                    padding: '2rem'
                }}>
                    <div style={{
                        fontSize: '3rem',
                        marginBottom: '1rem',
                        animation: 'pulse 2s ease-in-out infinite'
                    }}>
                        🤖
                    </div>
                    <h2 style={{ 
                        fontSize: '1.5rem', 
                        fontWeight: 600,
                        marginBottom: '0.5rem'
                    }}>
                        AI Receptionist
                    </h2>
                    <p style={{ 
                        fontSize: '1rem',
                        opacity: 0.9
                    }}>
                        Verifying authentication...
                    </p>
                </div>
                <style>{`
                    @keyframes pulse {
                        0%, 100% { transform: scale(1); opacity: 1; }
                        50% { transform: scale(1.1); opacity: 0.8; }
                    }
                `}</style>
            </div>
        );
    }

    // Only render children after auth is verified
    if (isAuthenticated) {
        return <>{children}</>;
    }

    // Redirecting - show same loading UI
    return fallback || (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white'
        }}>
            <p>Redirecting to login...</p>
        </div>
    );
}
