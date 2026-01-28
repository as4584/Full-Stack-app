import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * MIDDLEWARE - MINIMAL ROUTING ONLY
 * 
 * CRITICAL: Middleware must NOT redirect based on auth cookies.
 * Any auth-based redirects cause hydration mismatches and white screens.
 * 
 * The ONLY redirect here is / → /app, which lets AuthGate handle auth.
 * Auth enforcement happens entirely client-side in AuthGate component.
 */
export function middleware(request: NextRequest) {
    // NO redirects at all - all routing handled client-side
    // This prevents build-time confusion about which layouts apply to which routes
    return NextResponse.next();
}

export const config = {
    matcher: '/:path*',
};
