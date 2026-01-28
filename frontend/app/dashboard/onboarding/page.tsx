'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createBusiness, updateBusiness, searchNumbers, buyNumber, releaseNumber, redirectToGoogleOAuth, getBusinessId, setBusinessId as setStorageBusinessId, createCheckoutSession } from '@/lib/api';
import styles from '../../auth.module.css';

type Step = 0 | 1 | 2 | 3 | 4; // 0 = Subscription

export default function OnboardingPage() {
    const router = useRouter();

    // Step management
    const [currentStep, setCurrentStep] = useState<Step>(0); // Start at payment step

    // Step 1: Business Profile
    const [businessName, setBusinessName] = useState('');
    const [industry, setIndustry] = useState('');
    const [businessDescription, setBusinessDescription] = useState('');

    // Step 2: Phone Number
    const [availableNumbers, setAvailableNumbers] = useState<any[]>([]);
    const [selectedNumber, setSelectedNumber] = useState('');
    const [loadingNumbers, setLoadingNumbers] = useState(false);
    const [areaCode, setAreaCode] = useState('');

    // ID of the created business record
    const [businessId, setBusinessId] = useState<string | number | null>(null);
    const [purchasedNumber, setPurchasedNumber] = useState('');

    // Step 3: AI Persona
    const [greetingStyle, setGreetingStyle] = useState('professional');
    const [businessHours, setBusinessHours] = useState('9 AM - 5 PM, Monday - Friday');
    const [commonServices, setCommonServices] = useState('');
    const [faqEntries, setFaqEntries] = useState<{ question: string, answer: string }[]>([
        { question: '', answer: '' }
    ]);

    // Step 4: Finalize
    const [timezone, setTimezone] = useState('America/New_York');
    const [calConnected, setCalConnected] = useState(false);

    // General state
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [isResuming, setIsResuming] = useState(false);

    // Initial load: Check for success flag or restore businessId
    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('success') === 'sub_active') {
            setCurrentStep(1); // Payment done, move to profile
            // Clean URL
            window.history.replaceState({}, '', '/app/onboarding');
        }

        const savedId = getBusinessId();
        if (savedId && currentStep !== 1) { // Only resume if we're not just landing from payment
            setBusinessId(savedId);
            setIsResuming(true);
            setCurrentStep(2);
        }
    }, []);

    // Load Twilio numbers when reaching step 2
    useEffect(() => {
        if (currentStep === 2 && availableNumbers.length === 0) {
            handleSearchNumbers();
        }
    }, [currentStep, availableNumbers.length]);

    const handleSearchNumbers = async (overrideAreaCode?: string) => {
        const searchAreaCode = overrideAreaCode ?? areaCode;
        setLoadingNumbers(true);
        setError('');
        try {
            let numbers = await searchNumbers(searchAreaCode);
            
            // Auto-fallback: If area code specified but no results, try without area code
            if (numbers.length === 0 && searchAreaCode) {
                console.log('No numbers for area code, trying fallback...');
                const fallback = await searchNumbers('');
                if (fallback.length > 0) {
                    numbers = fallback;
                    // Don't show error - we found alternatives
                }
            }
            
            setAvailableNumbers(numbers);
            if (numbers.length > 0) {
                setSelectedNumber(numbers[0].phoneNumber);
            }
        } catch (err) {
            console.error('Failed to load numbers:', err);
            setError('Could not load available phone numbers.');
        } finally {
            setLoadingNumbers(false);
        }
    };

    const handleAddFaq = () => {
        setFaqEntries([...faqEntries, { question: '', answer: '' }]);
    };

    const handleRemoveFaq = (index: number) => {
        setFaqEntries(faqEntries.filter((_, i) => i !== index));
    };

    const handleFaqChange = (index: number, field: 'question' | 'answer', value: string) => {
        const updated = [...faqEntries];
        updated[index][field] = value;
        setFaqEntries(updated);
    };

    const handleConnectCalendar = async () => {
        setError('');
        setLoading(true);
        try {
            // We MUST create the business record first to get a real ID for the OAuth state
            const biz = await createBusiness({
                name: businessName || 'My Business',
                industry,
                description: businessDescription,
                phone_number: selectedNumber || undefined,
                timezone,
                greeting_style: greetingStyle,
                business_hours: businessHours,
                common_services: commonServices,
                faqs: faqEntries,
            });

            if (biz && biz.id) {
                redirectToGoogleOAuth(biz.id);
            } else {
                throw new Error('Business ID missing from response');
            }
        } catch (err) {
            console.error('Failed to start calendar connection:', err);
            setError('Failed to prepare calendar connection. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleNext = async () => {
        if (currentStep === 1) {
            if (!businessName) {
                setError('Business Name is required');
                return;
            }
            setLoading(true);
            try {
                const biz = await createBusiness({
                    name: businessName,
                    industry,
                    description: businessDescription
                });
                setBusinessId(biz.id);
                setStorageBusinessId(biz.id);
                setCurrentStep(2);
            } catch (err) {
                setError('Failed to create business profile');
            } finally {
                setLoading(false);
            }
        } else if (currentStep === 2) {
            if (!selectedNumber || !businessId) {
                setError('Please select a number');
                return;
            }
            setLoading(true);
            try {
                await buyNumber(selectedNumber, businessId);
                setPurchasedNumber(selectedNumber);
                setCurrentStep(3);
            } catch (err) {
                setError('Failed to purchase phone number. Please try again.');
            } finally {
                setLoading(false);
            }
        } else if (currentStep < 4) {
            setCurrentStep((currentStep + 1) as Step);
        }
    };

    const handleReleaseNumber = async () => {
        if (!businessId) return;
        setLoading(true);
        try {
            await releaseNumber(businessId);
            setPurchasedNumber('');
            setSelectedNumber('');
        } catch (err) {
            setError('Failed to release number');
        } finally {
            setLoading(false);
        }
    };


    const handleBack = () => {
        if (currentStep > 1) {
            setCurrentStep((currentStep - 1) as Step);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await updateBusiness({
                name: businessName,
                industry,
                description: businessDescription,
                phone_number: purchasedNumber || selectedNumber || undefined,
                timezone,
                greeting_style: greetingStyle,
                business_hours: businessHours,
                common_services: commonServices,
                faqs: faqEntries,
            });

            // Success! Head to the dashboard
            router.push('/dashboard');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to update business profile');
        } finally {
            setLoading(false);
        }
    };

    const handleSubscribe = async () => {
        setLoading(true);
        setError('');
        try {
            // We need a temporary business ID to attach the customer to?
            // Actually, we can just create the checkout session. 
            // The backend handles customer creation by email.
            const { url } = await createCheckoutSession();
            window.location.href = url;
        } catch (err: any) {
            console.error(err);
            setError('Failed to load checkout: ' + (err.message || 'Unknown error'));
            setLoading(false);
        }
    };

    const stepTitles = ['Plan', 'Business', 'Number', 'AI Style', 'Finalize'];

    return (
        <div className={styles.container}>
            <div className={styles.card} style={{ maxWidth: '600px', width: '95%' }}>
                {/* Progress Indicator */}
                {currentStep > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem' }}>
                        {[1, 2, 3, 4].map((step) => (
                            <div key={step} style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                flex: 1
                            }}>
                                <div style={{
                                    width: '40px',
                                    height: '40px',
                                    borderRadius: '50%',
                                    background: currentStep >= step ? 'linear-gradient(135deg, #60aaff 0%, #3d84ff 100%)' : '#e0e0e0',
                                    color: currentStep >= step ? 'white' : '#666',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontWeight: 'bold',
                                    transition: 'all 0.3s ease'
                                }}>
                                    {currentStep > step ? '✓' : step}
                                </div>
                                <span style={{
                                    fontSize: '0.75rem',
                                    marginTop: '0.5rem',
                                    color: currentStep >= step ? '#3d84ff' : '#999'
                                }}>
                                    {stepTitles[step]}
                                </span>
                            </div>
                        ))}
                    </div>
                )}

                <form onSubmit={handleSubmit} className={styles.form}>
                    {error && <div className={styles.error} style={{
                        background: '#fff5f5',
                        color: '#c53030',
                        padding: '1rem',
                        borderRadius: '0.5rem',
                        marginBottom: '1rem',
                        border: '1px solid #feb2b2'
                    }}>{error}</div>}

                    {/* Step 0: Payment Gate */}
                    {currentStep === 0 && (
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💎</div>
                            <h2 style={{ marginBottom: '1rem' }}>Activate Your Plan</h2>
                            <p style={{ color: '#666', marginBottom: '2rem', lineHeight: '1.6' }}>
                                To launch your AI Receptionist, you need an active subscription.
                                <br />
                                Start with our <strong>Starter Plan</strong> for just $75/mo.
                            </p>

                            <div style={{
                                background: '#f8f9fa',
                                padding: '1.5rem',
                                borderRadius: '16px',
                                marginBottom: '2rem',
                                border: '1px solid #e9ecef',
                                textAlign: 'left'
                            }}>
                                <h3 style={{ margin: '0 0 1rem 0' }}>Starter Plan Includes:</h3>
                                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.8rem' }}>
                                    <li style={{ display: 'flex', gap: '10px' }}>✅ <span><strong>250 Minutes</strong> / month</span></li>
                                    <li style={{ display: 'flex', gap: '10px' }}>✅ <span><strong>1 Dedicated Phone Number</strong></span></li>
                                    <li style={{ display: 'flex', gap: '10px' }}>✅ <span>Google Calendar Integration</span></li>
                                    <li style={{ display: 'flex', gap: '10px' }}>✅ <span>24/7 AI Availability</span></li>
                                </ul>
                            </div>

                            <button
                                type="button"
                                onClick={handleSubscribe}
                                disabled={loading}
                                style={{
                                    width: '100%',
                                    padding: '1rem',
                                    background: 'linear-gradient(135deg, #FFD700 0%, #FDB931 100%)', // Gold gradient
                                    color: '#000',
                                    border: 'none',
                                    borderRadius: '12px',
                                    fontWeight: 'bold',
                                    fontSize: '1.1rem',
                                    cursor: loading ? 'wait' : 'pointer',
                                    boxShadow: '0 4px 15px rgba(253, 185, 49, 0.4)'
                                }}
                            >
                                {loading ? 'Redirecting...' : 'Subscribe & Continue ($75/mo)'}
                            </button>
                            <p style={{ fontSize: '0.8rem', color: '#999', marginTop: '1rem' }}>
                                Secure payment via Stripe. Cancel anytime.
                            </p>
                        </div>
                    )}

                    {/* Step 1: Business Profile */}
                    {currentStep === 1 && (
                        <div>
                            <h2 style={{ marginBottom: '1rem' }}>Business Profile</h2>
                            <div className={styles.field}>
                                <label>Business Name *</label>
                                <input
                                    type="text"
                                    value={businessName}
                                    onChange={(e) => setBusinessName(e.target.value)}
                                    required
                                    placeholder="e.g., Acme Dental"
                                />
                            </div>
                            <div className={styles.field}>
                                <label>Industry</label>
                                <input
                                    type="text"
                                    value={industry}
                                    onChange={(e) => setIndustry(e.target.value)}
                                    placeholder="e.g., Healthcare"
                                />
                            </div>
                        </div>
                    )}

                    {/* Step 2: Phone Number */}
                    {currentStep === 2 && (
                        <div>
                            <h2 style={{ marginBottom: '1rem' }}>Choose Phone Number</h2>
                            <p style={{ fontSize: '0.9rem', color: '#718096', marginBottom: '1.5rem' }}>
                                Selected number will be assigned to your AI receptionist.
                                <strong style={{ color: '#3d84ff' }}> $2.00 setup fee</strong> applies.
                            </p>

                            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
                                <input
                                    type="text"
                                    placeholder="Area Code (e.g. 212)"
                                    value={areaCode}
                                    onChange={(e) => setAreaCode(e.target.value)}
                                    style={{ flex: 1 }}
                                />
                                <button
                                    type="button"
                                    onClick={() => handleSearchNumbers()}
                                    style={{ padding: '0 1.5rem', background: '#f7fafc', border: '1px solid #e2e8f0', borderRadius: '10px' }}
                                >
                                    Search
                                </button>
                            </div>

                            {purchasedNumber && (
                                <div style={{
                                    padding: '1rem',
                                    background: '#ebf8ff',
                                    borderRadius: '10px',
                                    marginBottom: '1.5rem',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    border: '1px solid #bee3f8'
                                }}>
                                    <span>Current: <strong>{purchasedNumber}</strong></span>
                                    <button
                                        type="button"
                                        onClick={handleReleaseNumber}
                                        style={{ color: '#e53e3e', fontSize: '0.8rem', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                                    >
                                        Release & Change
                                    </button>
                                </div>
                            )}

                            {loadingNumbers ? <p>Searching available numbers...</p> : (
                                <div className={styles.field}>
                                    <select
                                        value={selectedNumber}
                                        onChange={(e) => setSelectedNumber(e.target.value)}
                                        style={{ width: '100%', padding: '0.8rem', borderRadius: '10px' }}
                                    >
                                        <option value="">Select a number...</option>
                                        {availableNumbers.map(n => (
                                            <option key={n.phoneNumber} value={n.phoneNumber}>
                                                {n.friendlyName} {n.locality ? `(${n.locality}, ${n.region})` : ''} - $2.00
                                            </option>
                                        ))}
                                    </select>
                                    {availableNumbers.length === 0 && !loadingNumbers && (
                                        <div style={{ 
                                            padding: '1rem', 
                                            background: '#fffbeb', 
                                            borderRadius: '10px', 
                                            border: '1px solid #fcd34d',
                                            marginTop: '1rem'
                                        }}>
                                            <p style={{ color: '#92400e', fontSize: '0.9rem', marginBottom: '0.75rem' }}>
                                                <strong>No numbers found for this area code.</strong>
                                            </p>
                                            <p style={{ color: '#78716c', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
                                                Some area codes may have limited availability. Try:
                                            </p>
                                            <button 
                                                type="button"
                                                onClick={() => { setAreaCode(''); handleSearchNumbers(); }}
                                                style={{
                                                    background: '#3d84ff',
                                                    color: 'white',
                                                    padding: '0.5rem 1rem',
                                                    borderRadius: '8px',
                                                    border: 'none',
                                                    cursor: 'pointer',
                                                    fontSize: '0.85rem'
                                                }}
                                            >
                                                🔍 Show Any Available Number
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Step 3: AI Persona */}
                    {currentStep === 3 && (
                        <div>
                            <h2 style={{ marginBottom: '1.5rem' }}>AI Persona</h2>
                            <div className={styles.field}>
                                <label>Greeting Style</label>
                                <select value={greetingStyle} onChange={(e) => setGreetingStyle(e.target.value)}>
                                    <option value="professional">Professional</option>
                                    <option value="friendly">Friendly</option>
                                </select>
                            </div>
                            <div className={styles.field}>
                                <label>FAQs (AI Knowledge)</label>
                                {faqEntries.map((faq, idx) => (
                                    <div key={idx} style={{ marginBottom: '1rem' }}>
                                        <input
                                            placeholder="Question"
                                            value={faq.question}
                                            onChange={(e) => handleFaqChange(idx, 'question', e.target.value)}
                                            style={{ marginBottom: '0.5rem' }}
                                        />
                                        <textarea
                                            placeholder="Answer"
                                            value={faq.answer}
                                            onChange={(e) => handleFaqChange(idx, 'answer', e.target.value)}
                                        />
                                    </div>
                                ))}
                                <button type="button" onClick={handleAddFaq}>+ Add FAQ</button>
                            </div>
                        </div>
                    )}

                    {/* Step 4: Finalize & Calendar */}
                    {currentStep === 4 && (
                        <div>
                            <h2 style={{ marginBottom: '1rem' }}>Finalize Setup</h2>
                            <div className={styles.field}>
                                <label>Timezone</label>
                                <select value={timezone} onChange={(e) => setTimezone(e.target.value)}>
                                    <option value="America/New_York">Eastern Time</option>
                                    <option value="America/Los_Angeles">Pacific Time</option>
                                </select>
                            </div>

                            <div style={{ marginTop: '2rem', padding: '1.5rem', background: '#f0f9ff', borderRadius: '16px', border: '1px solid #bee3f8' }}>
                                <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: '#2b6cb0' }}>🚀 Calendar Access</h3>
                                <p style={{ fontSize: '0.9rem', color: '#4a5568', marginBottom: '1rem' }}>
                                    Connect your Google Calendar so the AI can book appointments for you.
                                </p>
                                <button
                                    type="button"
                                    onClick={handleConnectCalendar}
                                    style={{
                                        width: '100%',
                                        padding: '0.8rem',
                                        background: 'white',
                                        border: '2px solid #3d84ff',
                                        borderRadius: '12px',
                                        color: '#3d84ff',
                                        fontWeight: 'bold',
                                        cursor: 'pointer'
                                    }}
                                >
                                    🔗 Connect Google Calendar
                                </button>
                            </div>

                            <div style={{ margin: '1.5rem 0', fontSize: '0.9rem', color: '#718096' }}>
                                <p>By launching, your AI receptionist will be active on <strong>{selectedNumber || 'your demo line'}</strong>.</p>
                            </div>
                        </div>
                    )}

                    {/* Nav Buttons */}
                    <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                        {currentStep > 1 && (
                            <button type="button" onClick={handleBack} style={{ flex: 1 }}>Back</button>
                        )}
                        <button
                            type={currentStep === 4 ? "submit" : "button"}
                            onClick={currentStep < 4 ? handleNext : undefined}
                            style={{
                                flex: 2,
                                background: 'linear-gradient(135deg, #60aaff 0%, #3d84ff 100%)',
                                color: 'white',
                                border: 'none',
                                padding: '0.8rem',
                                borderRadius: '12px',
                                fontWeight: 'bold'
                            }}
                            disabled={loading}
                        >
                            {loading ? 'Launching...' : currentStep === 4 ? 'Launch AI Receptionist' : 'Continue'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
