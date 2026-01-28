'use client';

import { Suspense } from 'react';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import AuthGate from '@/components/AuthGate';
import DashboardLoading from '@/components/DashboardLoading';
import DashboardContent from './DashboardContent';

/**
 * DASHBOARD PAGE - Protected by AuthGate
 * 
 * AuthGate ensures:
 * 1. Same UI on server render and first client render
 * 2. Auth check happens client-side in useEffect
 * 3. No hydration mismatch = no white screen
 */
export default function DashboardPage() {
  return (
    <AuthGate>
      <ErrorBoundary>
        <Suspense fallback={<DashboardLoading />}>
          <DashboardContent />
        </Suspense>
      </ErrorBoundary>
    </AuthGate>
  );
}
