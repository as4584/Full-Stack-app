'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useRecentCalls } from '@/lib/hooks';
import { searchContact, upsertContact } from '@/lib/api';
import styles from '../../dashboard.module.css';

export default function CallDetailPage() {
    const params = useParams();
    const router = useRouter();
    const { calls, isLoading } = useRecentCalls();

    // Find the specific call
    // Note: parameters are strings, call.id might be int or string from API
    // Find the specific call
    const callId = params.id;
    const call = calls.find((c: any) => String(c.id) === String(callId));

    // Contact State
    const [contactId, setContactId] = useState<number | null>(null);
    const [callerName, setCallerName] = useState('');
    const [isBlocked, setIsBlocked] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [saving, setSaving] = useState(false);

    // Load contact info
    useEffect(() => {
        if (call?.from_number) {
            searchContact(call.from_number).then(data => {
                if (data.found) {
                    setContactId(data.id);
                    setCallerName(data.name || '');
                    setIsBlocked(data.is_blocked || false);
                }
            });
        }
    }, [call]);

    const handleSaveContact = async () => {
        if (!call) return;
        setSaving(true);
        try {
            const res = await upsertContact({
                phone_number: call.from_number,
                name: callerName,
                is_blocked: isBlocked
            });
            setContactId(res.id);
            setIsEditing(false);
        } catch (err) {
            console.error('Failed to save contact', err);
            alert('Failed to save contact details');
        } finally {
            setSaving(false);
        }
    };

    const toggleBlock = async () => {
        if (!confirm(isBlocked ? 'Unblock this number?' : 'Block this number from calling your AI?')) return;

        const newStatus = !isBlocked;
        setIsBlocked(newStatus);

        // Auto-save on block toggle
        try {
            await upsertContact({
                phone_number: call!.from_number,
                name: callerName,
                is_blocked: newStatus
            });
        } catch (err) {
            console.error(err);
            setIsBlocked(!newStatus); // Revert
        }
    };

    if (isLoading) {
        return (
            <div className={styles.commandCenter} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className={styles.loadingOrb} />
            </div>
        );
    }

    if (!call) {
        return (
            <div className={styles.commandCenter} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                <h2>Call Not Found</h2>
                <button onClick={() => router.back()} className={styles.ctaButton}>Go Back</button>
            </div>
        );
    }

    // Format Dates
    const startDate = new Date(call.created_at);
    const durationSeconds = call.duration || 0;
    const endDate = new Date(startDate.getTime() + durationSeconds * 1000);

    return (
        <div className={styles.commandCenter}>
            <div style={{ maxWidth: '800px', margin: '0 auto', width: '100%', padding: '2rem' }}>
                <button
                    onClick={() => router.back()}
                    style={{
                        background: 'none',
                        border: 'none',
                        color: '#fff',
                        cursor: 'pointer',
                        marginBottom: '1rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                    }}
                >
                    ← Back to Dashboard
                </button>

                <section className={styles.aiStatusCard} style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '1.5rem' }}>
                    <div style={{ width: '100%', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem' }}>
                        <div className={styles.sectionAnchor}>Call Metadata</div>
                        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', color: '#333' }}>{call.from_number}</h1>
                        <span className={`${styles.chip} ${call.appointment_booked ? styles.booked : ''}`}>
                            {call.appointment_booked ? '✓ Appointment Booked' : (call.intent || 'Inquiry')}
                        </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', width: '100%', gap: '1rem' }}>
                        <div>
                            <span className={styles.textSystem}>Caller Name</span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                {isEditing ? (
                                    <div style={{ display: 'flex', gap: '4px' }}>
                                        <input
                                            value={callerName}
                                            onChange={e => setCallerName(e.target.value)}
                                            placeholder="Enter Name"
                                            style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid #ccc', width: '140px' }}
                                        />
                                        <button onClick={handleSaveContact} disabled={saving} style={{ cursor: 'pointer', background: '#3d84ff', color: 'white', border: 'none', borderRadius: '4px', padding: '4px 8px' }}>
                                            {saving ? '...' : '✓'}
                                        </button>
                                    </div>
                                ) : (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <p className={styles.textCaller} style={{ fontSize: '1.1rem', margin: 0 }}>{callerName || 'Unknown'}</p>
                                        <button onClick={() => setIsEditing(true)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.9rem', opacity: 0.5 }}>✏️</button>
                                    </div>
                                )}
                            </div>
                        </div>
                        <div>
                            <span className={styles.textSystem}>Called At</span>
                            <p className={styles.textCaller} style={{ fontSize: '1.1rem' }}>{startDate.toLocaleString()}</p>
                        </div>
                        <div>
                            <span className={styles.textSystem}>Ended At</span>
                            <p className={styles.textCaller} style={{ fontSize: '1.1rem' }}>{endDate.toLocaleString()}</p>
                        </div>
                        <div>
                            <span className={styles.textSystem}>Duration</span>
                            <p className={styles.textCaller} style={{ fontSize: '1.1rem' }}>{Math.floor(durationSeconds / 60)}m {durationSeconds % 60}s</p>
                        </div>
                        {call.recording_url && (
                            <div style={{ gridColumn: '1 / -1', marginTop: '1rem' }}>
                                <span className={styles.textSystem} style={{ display: 'block', marginBottom: '0.5rem' }}>Call Recording</span>
                                <audio controls src={call.recording_url} style={{ width: '100%' }}>
                                    Your browser does not support the audio element.
                                </audio>
                            </div>
                        )}
                    </div>
                    <div style={{ width: '100%', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '1rem', marginTop: '0.5rem' }}>
                        <button
                            onClick={toggleBlock}
                            style={{
                                background: 'none',
                                border: isBlocked ? '1px solid #7FFF00' : '1px solid #ff4444',
                                color: isBlocked ? '#7FFF00' : '#ff4444',
                                padding: '8px 16px',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                fontWeight: 'bold'
                            }}
                        >
                            {isBlocked ? '✓ Phone Number Blocked' : '🚫 Block This Number'}
                        </button>
                    </div>
                </section>

                <section className={styles.transcriptCard} style={{ marginTop: '2rem' }}>
                    <h3 className={styles.sectionAnchor}>Full Transcript</h3>
                    <div className={styles.transcriptContent} style={{ maxHeight: 'none' }}>
                        {call.transcript ? (
                            <div className={styles.transcriptText}>
                                {call.transcript.split('\n').map((line: string, i: number) => {
                                    const isAi = line.toLowerCase().startsWith('ai:') || line.toLowerCase().startsWith('aria:');
                                    const isCaller = line.toLowerCase().startsWith('caller:') || line.toLowerCase().startsWith('user:');
                                    const cleanLine = line.replace(/^(ai:|aria:|caller:|user:)\s*/i, '');

                                    return (
                                        <p key={i} style={{ marginBottom: '1rem', display: 'flex', flexDirection: 'column' }}>
                                            <span className={styles.textSystem} style={{ opacity: 0.7, marginBottom: '0.2rem' }}>
                                                {isAi ? 'AI Receptionist' : 'Caller'}
                                            </span>
                                            <span className={isAi ? styles.textAi : styles.textCaller} style={{ fontSize: '1.1rem' }}>
                                                {cleanLine || line}
                                            </span>
                                        </p>
                                    );
                                })}
                            </div>
                        ) : (
                            <p style={{ color: '#888', fontStyle: 'italic' }}>No transcript available.</p>
                        )}
                    </div>
                </section>
            </div>
        </div>
    );
}
