'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { logout, getBusiness, type Business } from '@/lib/api';
import styles from '../app/dashboard/dashboard.module.css';

/**
 * APP LAYOUT CLIENT COMPONENT
 * 
 * Contains dashboard shell (header, nav, sidebar)
 * Always renders the same structure on server and client
 * Business data loads progressively without blocking render
 */
// Auth app URL - completely separate Next.js app
const AUTH_URL = process.env.NEXT_PUBLIC_AUTH_URL || 'https://auth.lexmakesit.com';

export default function AppLayoutClient({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const [business, setBusiness] = useState<Business | null>(null);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        getBusiness()
            .then(data => setBusiness(data))
            .catch(() => console.log('Not logged in or no business'));
    }, []);

    const handleLogout = async () => {
        await logout();
        // Redirect to auth app after logout (external redirect)
        window.location.href = `${AUTH_URL}/login`;
    };

    return (
        <div className={styles.appContainer}>
            <header className={styles.header}>
                <div className={styles.headerContent}>
                    <div className={styles.logo} onClick={() => router.push('/dashboard')}>
                        <span style={{
                            color: 'white',
                            fontWeight: '900',
                            fontSize: '1.5rem',
                            letterSpacing: '-1px',
                            background: 'linear-gradient(135deg, white 0%, #3d84ff 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            fontFamily: 'Orbitron, sans-serif'
                        }}>lexmakesit</span>
                    </div>

                    <nav className={styles.nav}>
                        <button onClick={() => router.push('/dashboard')} className={styles.navLink}>Dashboard</button>
                        <button onClick={() => window.open('https://lexmakesit.com/projects/ai-receptionist', '_blank')} className={styles.navLink}>
                            Pricing & Plans
                        </button>
                    </nav>

                    <div className={styles.headerRight}>
                        {business?.phone_number && (
                            <div className={styles.phoneBadge}>
                                📞 {business.phone_number}
                            </div>
                        )}
                        <button onClick={handleLogout} className={styles.logoutBtn}>Logout</button>
                    </div>
                </div>
            </header>

            <main className={styles.main}>
                {children}
            </main>
        </div>
    );
}
