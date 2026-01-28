'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/**
 * ROOT PAGE - Simple client-side redirect
 * 
 * This avoids middleware redirects which can confuse Next.js
 * build-time prerendering and cause wrong layouts to be applied.
 */
export default function RootPage() {
    const router = useRouter();
    
    useEffect(() => {
        router.replace('/dashboard');
    }, [router]);
    
    // Show minimal loading UI (same as what client will see after redirect)
    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        }}>
            <div style={{ color: 'white', fontSize: '1.2rem' }}>Loading...</div>
        </div>
    );
}
