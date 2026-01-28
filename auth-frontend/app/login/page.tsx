'use client';

import { useState } from 'react';

/**
 * LOGIN PAGE - auth.lexmakesit.com/login
 * 
 * This is a completely standalone login page with:
 * - NO shared layouts with dashboard
 * - NO dashboard components
 * - NO middleware auth enforcement
 * 
 * Flow:
 * 1. User enters credentials
 * 2. POST to backend API
 * 3. Backend sets lex_token cookie (domain=.lexmakesit.com)
 * 4. On success: redirect to https://dashboard.lexmakesit.com
 * 5. On failure: show error message
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.lexmakesit.com';
const DASHBOARD_URL = process.env.NEXT_PUBLIC_DASHBOARD_URL || 'https://dashboard.lexmakesit.com';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
                credentials: 'include', // CRITICAL: Include cookies in request
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Login failed');
            }

            // Success! Redirect to dashboard
            // The backend has already set the lex_token cookie
            window.location.href = DASHBOARD_URL;
        } catch (err: any) {
            setError(err.message || 'An error occurred. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container">
            <div className="card">
                <div className="logo">
                    <span className="logoIcon">🤖</span>
                    <h1>AI Receptionist</h1>
                </div>

                <h2 className="title">Welcome Back</h2>
                <p className="subtitle">Sign in to manage your AI assistant</p>

                <form className="form" onSubmit={handleSubmit}>
                    {error && <div className="error">{error}</div>}

                    <div className="field">
                        <label htmlFor="email">Email Address</label>
                        <input
                            id="email"
                            type="email"
                            required
                            placeholder="you@company.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            autoComplete="email"
                        />
                    </div>

                    <div className="field">
                        <label htmlFor="password">Password</label>
                        <div className="passwordWrapper">
                            <input
                                id="password"
                                type={showPassword ? 'text' : 'password'}
                                required
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                autoComplete="current-password"
                            />
                            <button
                                type="button"
                                className="eyeBtn"
                                onClick={() => setShowPassword(!showPassword)}
                                title={showPassword ? 'Hide password' : 'Show password'}
                            >
                                {showPassword ? '🙈' : '👁️'}
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="submitBtn"
                        disabled={loading}
                    >
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>

                <div className="footer">
                    Don&apos;t have an account?{' '}
                    <a href={`${DASHBOARD_URL}/signup`}>Sign Up</a>
                </div>
            </div>
        </div>
    );
}
