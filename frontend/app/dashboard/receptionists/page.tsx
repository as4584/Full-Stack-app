'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getRecentCalls, redirectToGoogleOAuth } from '@/lib/api';
import { useBusiness } from '@/lib/hooks';
import styles from '../dashboard.module.css';

export default function LogsPage() {
    const router = useRouter();
    const { business, isLoading: bizLoading } = useBusiness();
    const [calls, setCalls] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function loadCalls() {
            try {
                const data = await getRecentCalls();
                setCalls(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        loadCalls();
    }, []);

    return (
        <div className={styles.commandCenter}>
            <aside className={styles.sidebar}>
                <nav className={styles.sidebarNav}>
                    <a href="/dashboard" className={styles.navItem}>
                        <span className={styles.navIcon}>🏠</span>
                        <span className={styles.navLabel}>Home</span>
                    </a>
                    <a href="/dashboard/receptionists" className={`${styles.navItem} ${styles.active}`}>
                        <span className={styles.navIcon}>📋</span>
                        <span className={styles.navLabel}>Logs</span>
                    </a>
                    <button
                        onClick={() => redirectToGoogleOAuth(business?.id)}
                        className={styles.navItem}
                        style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer', padding: '0.75rem 1rem' }}
                    >
                        <span className={styles.navIcon}>📅</span>
                        <span className={styles.navLabel}>Calendar</span>
                    </button>
                    <a href="/dashboard/settings" className={styles.navItem}>
                        <span className={styles.navIcon}>⚙️</span>
                        <span className={styles.navLabel}>Settings</span>
                    </a>
                </nav>
            </aside>

            <main className={styles.mainContent} style={{ padding: '2rem' }}>
                <header style={{ marginBottom: '2rem' }}>
                    <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Call History</h1>
                    <p style={{ color: '#666' }}>A complete record of all interactions handled by Aria.</p>
                </header>

                <section className={styles.recentLogsCard} style={{ width: '100%', maxWidth: '1000px' }}>
                    {loading ? (
                        <div style={{ padding: '2rem', textAlign: 'center' }}>
                            <div className={styles.loadingOrb} style={{ margin: 'auto' }} />
                            <p>Loading your history...</p>
                        </div>
                    ) : calls.length === 0 ? (
                        <div className={styles.emptyState}>
                            <span className={styles.emptyIcon}>📞</span>
                            <h3>No calls found</h3>
                            <p>Once you start receiving calls, they will appear here.</p>
                        </div>
                    ) : (
                        <div className={styles.logsList}>
                            {calls.map((log: any, i: number) => (
                                <div
                                    key={i}
                                    className={styles.logItem}
                                    onClick={() => router.push(`/dashboard/call/${log.id}`)}
                                    style={{ cursor: 'pointer', padding: '1.5rem', borderBottom: '1px solid #eee' }}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                        <div>
                                            <span style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>{log.from_number}</span>
                                            <div style={{ color: '#666', fontSize: '0.9rem', marginTop: '4px' }}>
                                                {new Date(log.created_at).toLocaleString()} • {Math.floor((log.duration || 0) / 60)}m {(log.duration || 0) % 60}s
                                            </div>
                                            <p style={{ marginTop: '10px', color: '#444', fontStyle: log.summary ? 'normal' : 'italic' }}>
                                                {log.summary || 'No summary generated for this call.'}
                                            </p>
                                        </div>
                                        <div style={{ display: 'flex', gap: '10px' }}>
                                            <span className={`${styles.chip} ${log.appointment_booked ? styles.booked : ''}`}>
                                                {log.appointment_booked ? '✓ Appointment' : log.intent || 'Inquiry'}
                                            </span>
                                            <span className={styles.chip} style={{ background: log.status === 'completed' ? '#e8f5e9' : '#fff3e0', color: log.status === 'completed' ? '#2e7d32' : '#ef6c00' }}>
                                                {log.status === 'completed' ? 'Finished' : 'Interrupted'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </section>
            </main>
        </div>
    );
}
