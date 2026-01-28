'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { searchNumbers, buyNumber, redirectToGoogleOAuth, toggleReceptionist, type PhoneNumberDraft } from '@/lib/api';
import { useUser, useBusiness, useRecentCalls } from '@/lib/hooks';
import styles from './dashboard.module.css';

// --- Loading Skeletons ---
function SkeletonCard() {
    return (
        <div className={styles.recentLogsCard}>
            <div className={`${styles.skeleton} ${styles.skeletonTitle}`} />
            <div className={`${styles.skeleton} ${styles.skeletonText}`} />
            <div className={`${styles.skeleton} ${styles.skeletonText}`} />
            <div className={`${styles.skeleton} ${styles.skeletonText}`} />
        </div>
    );
}

function StatusSkeleton() {
    return (
        <section className={styles.aiStatusCard}>
            <div className={styles.aiStatusContent}>
                <div className={`${styles.skeleton} ${styles.skeletonOrb}`} />
                <div style={{ flex: 1 }}>
                    <div className={`${styles.skeleton} ${styles.skeletonTitle}`} />
                    <div className={`${styles.skeleton} ${styles.skeletonText}`} />
                </div>
            </div>
        </section>
    );
}

export default function DashboardPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { user, isLoading: userLoading, isError: userError } = useUser();
    const { business, isLoading: bizLoading, isError: bizError, mutate: mutateBiz } = useBusiness();
    const { calls: recentCalls, isLoading: callsLoading, isError: callsError, mutate: mutateCalls } = useRecentCalls();

    const [aiActive, setAiActive] = useState(true);
    const [currentTime, setCurrentTime] = useState(new Date());

    // Sync local AI status with business data when it loads
    useEffect(() => {
        if (business) {
            setAiActive(business.receptionist_enabled ?? true);
        }
    }, [business]);

    // Phone Search State
    const [isPhoneModalOpen, setIsPhoneModalOpen] = useState(false);
    const [areaCode, setAreaCode] = useState('');
    const [searchResults, setSearchResults] = useState<PhoneNumberDraft[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [isBuying, setIsBuying] = useState(false);
    const [purchaseError, setPurchaseError] = useState('');

    // Calendar Toast Logic
    const [toastMsg, setToastMsg] = useState<{ msg: string, type: 'success' | 'error' } | null>(null);

    useEffect(() => {
        const timeInterval = setInterval(() => setCurrentTime(new Date()), 1000);
        return () => clearInterval(timeInterval);
    }, []);

    // Handle Calendar Redirect Params
    useEffect(() => {
        const error = searchParams.get('error');
        const success = searchParams.get('success');

        if (success === 'calendar_connected') {
            setToastMsg({ msg: '✅ Calendar Connected Successfully!', type: 'success' });
            // Clear URL params
            router.replace('/dashboard');
        } else if (error) {
            const details = searchParams.get('details') || 'Unknown error';
            setToastMsg({ msg: `❌ Calendar Connection Failed: ${details}`, type: 'error' });
            router.replace('/dashboard');
        }

        if (success || error) {
            setTimeout(() => setToastMsg(null), 5000);
        }
    }, [searchParams, router]);

    // Handle SWR API Errors
    useEffect(() => {
        if (userError) {
            console.error('[Dashboard] User fetch error:', userError);
            // Only show error for actual HTTP errors (not for null/empty responses)
            if (userError?.status && userError.status >= 400) {
                setToastMsg({ msg: '⚠️ Failed to load user data', type: 'error' });
                setTimeout(() => setToastMsg(null), 4000);
            }
        }
        if (bizError) {
            console.error('[Dashboard] Business fetch error:', bizError);
            // Don't show error for new users without business (backend returns null)
        }
        if (callsError) {
            console.error('[Dashboard] Calls fetch error:', callsError);
            // Only show error if it's a real HTTP error (500, 401, etc), not for empty data
            if (callsError?.status && callsError.status >= 400) {
                setToastMsg({ msg: '⚠️ Failed to load recent calls', type: 'error' });
                setTimeout(() => setToastMsg(null), 4000);
            }
        }
    }, [userError, bizError, callsError]);

    const handleRefreshCalls = async () => {
        await mutateCalls();
    };

    const handleSearchNumbers = async () => {
        setIsSearching(true);
        try {
            const results = await searchNumbers(areaCode);
            setSearchResults(results);
        } catch (err) {
            console.error(err);
        } finally {
            setIsSearching(false);
        }
    };

    const handleBuyNumber = async (phoneNumber: string) => {
        setIsBuying(true);
        setPurchaseError('');
        try {
            await buyNumber(phoneNumber, business?.id);
            await mutateBiz();
            setIsPhoneModalOpen(false);
        } catch (err) {
            setPurchaseError('Failed to purchase number');
            console.error(err);
        } finally {
            setIsBuying(false);
        }
    };

    const [isToggling, setIsToggling] = useState(false);

    const handleToggleStatus = async (checked: boolean) => {
        if (!business?.id || isToggling) return;

        // Optimistic update
        setAiActive(checked);
        setIsToggling(true);

        try {
            const { toggleReceptionist } = await import('@/lib/api');
            await toggleReceptionist(checked);
            await mutateBiz(); // Refresh actual data
        } catch (err) {
            console.error('Failed to toggle status:', err);
            // Revert on error
            setAiActive(!checked);
            setToastMsg({ msg: '❌ Failed to update status', type: 'error' });
            setTimeout(() => setToastMsg(null), 3000);
        } finally {
            setIsToggling(false);
        }
    };

    // Derived State
    const hasPhoneNumber = business?.phone_number != null;
    const activeCalls = recentCalls.filter((c: any) => c.status === 'in-progress');

    return (
        <div className={styles.commandCenter}>
            {/* Toast Notification */}
            {toastMsg && (
                <div style={{
                    position: 'fixed',
                    top: '20px',
                    right: '20px',
                    backgroundColor: toastMsg.type === 'success' ? '#4caf50' : '#f44336',
                    color: 'white',
                    padding: '1rem 2rem',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                    zIndex: 1000,
                    animation: 'slideIn 0.3s ease-out'
                }}>
                    {toastMsg.msg}
                </div>
            )}

            {/* Left Sidebar - Instant Load */}
            <aside className={styles.sidebar}>
                <nav className={styles.sidebarNav}>
                    <a href="/dashboard" className={`${styles.navItem} ${styles.active}`}>
                        <span className={styles.navIcon}>🏠</span>
                        <span className={styles.navLabel}>Home</span>
                    </a>
                    <a href="/dashboard/receptionists" className={styles.navItem}>
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

            {/* Main Content */}
            <main className={styles.mainContent}>
                {/* AI Status Card - Streamed UI */}
                {bizLoading ? <StatusSkeleton /> : (() => {
                    const isOverLimit = (business?.minutes_used || 0) >= (business?.minutes_limit || 100);
                    const isBillingIssue = business?.subscription_status !== 'active' && business?.subscription_status !== 'trialing';
                    const isUnavailable = isOverLimit || isBillingIssue;

                    let statusClass = styles.inactive;
                    let statusLabel = 'Paused';
                    let orbClass = styles.inactive;

                    if (isUnavailable) {
                        statusClass = styles.unavailable;
                        statusLabel = 'Unavailable';
                        orbClass = styles.warning;
                    } else if (aiActive) {
                        statusClass = styles.active;
                        statusLabel = 'Active';
                        orbClass = styles.active;
                    }

                    return (
                        <section className={styles.aiStatusCard}>
                            <h2 className={styles.cardTitle}>AI Receptionist Status</h2>
                            <div className={styles.aiStatusContent}>
                                <div className={`${styles.statusOrb} ${orbClass}`}>
                                    <div className={styles.orbInner} />
                                </div>
                                <div className={styles.statusInfo}>
                                    <h3>{business?.name || 'My Business'}</h3>
                                    <span className={`${styles.statusText} ${statusClass}`}>{statusLabel}</span>
                                    {isUnavailable && (
                                        <p className={styles.warningText}>
                                            {isOverLimit ? 'Minute limit reached' : 'Billing issue detected'}
                                        </p>
                                    )}
                                </div>
                                <label className={styles.toggleWrapper}>
                                    {isToggling && <span className={styles.loadingSpinnerSmall} />}
                                    <input
                                        type="checkbox"
                                        checked={aiActive}
                                        onChange={(e) => handleToggleStatus(e.target.checked)}
                                        className={styles.toggleInput}
                                        disabled={!hasPhoneNumber || isUnavailable || isToggling}
                                    />
                                    <span className={styles.toggleSlider}>
                                        <span className={styles.toggleKnob} />
                                    </span>
                                    <span className={styles.toggleLabel}>{aiActive ? 'ON' : 'OFF'}</span>
                                </label>
                            </div>
                            {!hasPhoneNumber && (
                                <div className={styles.emptyStateInline}>
                                    <p>⚠️ Phone number required to activate AI receptionist</p>
                                    <button onClick={() => setIsPhoneModalOpen(true)} className={styles.ctaLink} style={{ background: 'none', border: 'none', color: 'inherit', textDecoration: 'underline', cursor: 'pointer', padding: 0, font: 'inherit' }}>Configure Phone Number →</button>
                                </div>
                            )}
                        </section>
                    );
                })()}

                {hasPhoneNumber ? (
                    <>
                        {/* Queue Card */}
                        <section className={styles.callQueueCard}>
                            <div className={styles.queueHeader}>
                                <div className={styles.queueOrb}>
                                    <span>{activeCalls.length}</span>
                                </div>
                                <div>
                                    <h3>Active Calls</h3>
                                    <span className={styles.queueSubtext}>
                                        {activeCalls.length > 0
                                            ? `Current: ${activeCalls.map((c: any) => c.from_number).join(', ')}`
                                            : 'No calls in progress'}
                                    </span>
                                </div>
                            </div>
                        </section>

                        {/* Recent Logs - Instant showing of cached data */}
                        <section className={styles.recentLogsCard}>
                            <div className={styles.cardHeaderWithAction}>
                                <h3>Recent Call Logs</h3>
                                <button onClick={handleRefreshCalls} className={styles.refreshBtn} title="Refresh Logs">
                                    🔄
                                </button>
                            </div>
                            {callsLoading && recentCalls.length === 0 ? (
                                <div className={styles.logsList}>
                                    <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ height: '50px' }} />
                                    <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ height: '50px' }} />
                                </div>
                            ) : recentCalls.length === 0 ? (
                                <div className={styles.emptyState}>
                                    <span className={styles.emptyIcon}>📞</span>
                                    <h4>No Calls Yet</h4>
                                    <p>Once your AI receptionist receives calls, they will appear here</p>
                                </div>
                            ) : (
                                <div className={styles.logsList}>
                                    {recentCalls.slice(0, 10).map((log: any, i: number) => (
                                        <div
                                            key={i}
                                            className={styles.logItem}
                                            onClick={() => log.id && router.push(`/dashboard/call/${log.id}`)}
                                            style={{ cursor: 'pointer', transition: 'background 0.2s', position: 'relative' }}
                                        >
                                            <div className={styles.logMainInfo}>
                                                <span className={styles.logName}>{log.from_number}</span>
                                                <p className={styles.logSummary} style={{
                                                    fontWeight: 400,
                                                    display: '-webkit-box',
                                                    WebkitLineClamp: 2,
                                                    WebkitBoxOrient: 'vertical',
                                                    overflow: 'hidden',
                                                    marginTop: '4px'
                                                }}>
                                                    {log.summary || 'No summary available'}
                                                </p>
                                            </div>
                                            <div className={styles.logTags}>
                                                <span className={styles.logDuration}>
                                                    {Math.floor((log.duration || 0) / 60)}m {(log.duration || 0) % 60}s
                                                </span>
                                                <span className={`${styles.chip} ${log.appointment_booked ? styles.booked : ''}`}>
                                                    {log.appointment_booked ? '✓ Booked' : log.intent || 'Call'}
                                                </span>
                                                <span className={styles.chip}>{new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </section>
                    </>
                ) : (
                    <section className={styles.emptyStateCard}>
                        <div className={styles.emptyState}>
                            <span className={styles.emptyIcon}>📱</span>
                            <h3>Welcome, {user?.full_name || 'Business Owner'}</h3>
                            <p>Set up your business phone number to start receiving AI-powered calls</p>
                            <button onClick={() => setIsPhoneModalOpen(true)} className={styles.ctaButton}>
                                Configure Phone Number
                            </button>
                        </div>
                    </section>
                )}
            </main>

            {/* Right Column */}
            <aside className={styles.rightColumn}>
                {/* Last Conversation - Cached UI */}
                <section className={styles.transcriptCard}>
                    <h3 className={styles.sectionAnchor}>Last Conversation</h3>
                    <div className={styles.transcriptContent}>
                        {recentCalls.length > 0 && recentCalls[0].transcript ? (
                            <div className={styles.transcriptText}>
                                {recentCalls[0].transcript.split('\n').map((line: string, i: number) => {
                                    const isAi = line.toLowerCase().startsWith('ai:') || line.toLowerCase().startsWith('aria:');
                                    const isCaller = line.toLowerCase().startsWith('caller:') || line.toLowerCase().startsWith('user:');
                                    const cleanLine = line.replace(/^(ai:|aria:|caller:|user:)\s*/i, '');

                                    return (
                                        <p key={i} style={{ marginBottom: '0.5rem', display: 'flex', flexDirection: 'column' }}>
                                            <span className={styles.textSystem} style={{ opacity: 0.7, fontSize: '0.75rem', marginBottom: '0.1rem' }}>
                                                {isAi ? 'AI' : isCaller ? 'Caller' : ''}
                                            </span>
                                            <span className={isAi ? styles.textAi : styles.textCaller}>
                                                {cleanLine || line}
                                            </span>
                                        </p>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className={styles.emptyStateInline} style={{ textAlign: 'center', padding: '2rem' }}>
                                <p style={{ color: '#888' }}>
                                    {recentCalls.length > 0 ? "No transcript available for the last call." : "No calls recorded yet."}
                                </p>
                            </div>
                        )}
                    </div>
                </section>

                {/* System Health */}
                <section className={styles.healthCard}>
                    <h3>System Health</h3>
                    <div className={styles.healthGrid}>
                        <div className={styles.healthItem}>
                            <div className={`${styles.healthOrb} ${bizLoading ? styles.inactive : styles.connected}`} />
                            <div>
                                <span>Phone</span>
                                <small>{business?.phone_number || 'Disconnected'}</small>
                            </div>
                        </div>
                        <div className={styles.healthItem}>
                            <div>
                                <span>LLM</span>
                                <small>Active</small>
                            </div>
                        </div>
                        <div className={styles.healthItem}>
                            <div className={`${styles.healthOrb} ${styles.ok}`} />
                            <div>
                                <span>Minutes</span>
                                <small>{business?.minutes_used || 0} / {business?.minutes_limit || 250}</small>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Schedule/Booking */}
                <section className={styles.scheduleCard}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h3>Schedule</h3>
                        <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#3d84ff' }}>
                            {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                    </div>
                    <div className={styles.miniCalendar}>
                        <div className={styles.calendarHeader}>
                            <span>S</span><span>M</span><span>T</span><span>W</span><span>T</span><span>F</span><span>S</span>
                        </div>
                        <div className={styles.calendarDays}>
                            {[...Array(31)].map((_, i) => {
                                const day = i + 1;
                                const isToday = day === currentTime.getDate();
                                const hasBooking = recentCalls.some(c =>
                                    c.appointment_booked &&
                                    new Date(c.created_at).getDate() === day &&
                                    new Date(c.created_at).getMonth() === currentTime.getMonth()
                                );

                                return (
                                    <span
                                        key={i}
                                        className={`${isToday ? styles.today : ''} ${hasBooking ? styles.hasBooking : ''}`}
                                        title={hasBooking ? 'Appointment Booked' : undefined}
                                    >
                                        {day}
                                        {hasBooking && <div className={styles.bookingDot} />}
                                    </span>
                                );
                            })}
                        </div>
                    </div>
                </section>
            </aside>

            {/* Phone Number Modal */}
            {isPhoneModalOpen && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modalContent}>
                        <div className={styles.modalHeader}>
                            <h2>Get New Number</h2>
                            <button onClick={() => setIsPhoneModalOpen(false)}>×</button>
                        </div>
                        {!isBuying ? (
                            <>
                                <div className={styles.searchBox}>
                                    <input
                                        placeholder="Area Code"
                                        value={areaCode}
                                        onChange={(e) => setAreaCode(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && handleSearchNumbers()}
                                    />
                                    <button onClick={handleSearchNumbers} disabled={isSearching}>
                                        {isSearching ? '...' : 'Search'}
                                    </button>
                                </div>
                                <div className={styles.searchResults}>
                                    {searchResults.map((num) => (
                                        <div key={num.phoneNumber} className={styles.searchResultItem}>
                                            <span>{num.friendlyName}</span>
                                            <button onClick={() => handleBuyNumber(num.phoneNumber)}>Buy</button>
                                        </div>
                                    ))}
                                </div>
                            </>
                        ) : (
                            <div style={{ textAlign: 'center', padding: '2rem' }}>
                                <div className={styles.loadingOrb} style={{ margin: 'auto' }} />
                                <p>Configuring Line...</p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
