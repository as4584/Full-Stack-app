'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/**
 * ROOT PAGE - Redirects to /login
 * 
 * The auth app only serves login functionality.
 * All other routes redirect to the dashboard.
 */
export default function RootPage() {
    const router = useRouter();
    
    useEffect(() => {
        router.replace('/login');
    }, [router]);
    
    return (
        <div className="container">
            <div className="card">
                <p style={{ textAlign: 'center', color: '#666' }}>Redirecting to login...</p>
            </div>
        </div>
    );
}
