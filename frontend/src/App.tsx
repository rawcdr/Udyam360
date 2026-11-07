import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { OnboardingProvider } from './context/OnboardingContext';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { ProgressBar } from './components/layout/ProgressBar';
import { LandingPage } from './pages/LandingPage';
import { AdvisorPage } from './pages/AdvisorPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { QuotePage } from './pages/QuotePage';
import { KYCPage } from './pages/KYCPage';
import { OrderTrackerPage } from './pages/OrderTrackerPage';
import { AdminLoginPage } from './pages/admin/AdminLoginPage';

import { ScrollToTop } from './components/layout/ScrollToTop';

// Lazy-load admin portal routes to decouple recharts and admin bundles from customer journey
const AdminLayout = lazy(() =>
  import('./pages/admin/AdminLayout').then((m) => ({ default: m.AdminLayout }))
);
const AdminOverviewPage = lazy(() =>
  import('./pages/admin/AdminOverviewPage').then((m) => ({ default: m.AdminOverviewPage }))
);
const AdminLeadsPage = lazy(() =>
  import('./pages/admin/AdminLeadsPage').then((m) => ({ default: m.AdminLeadsPage }))
);
const AdminKYCExceptionsPage = lazy(() =>
  import('./pages/admin/AdminKYCExceptionsPage').then((m) => ({ default: m.AdminKYCExceptionsPage }))
);
const AdminModelPage = lazy(() =>
  import('./pages/admin/AdminModelPage').then((m) => ({ default: m.AdminModelPage }))
);

const AdminLoadingFallback: React.FC = () => (
  <div className="min-h-[400px] flex flex-col items-center justify-center p-12 text-slate-500">
    <div className="w-8 h-8 border-4 border-red-600 border-t-transparent rounded-full animate-spin mb-4" />
    <p className="text-sm font-medium">Loading executive portal...</p>
  </div>
);

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <OnboardingProvider>
        <BrowserRouter>
          <ScrollToTop />
          <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
            <Navbar />
            <ProgressBar />
            <main className="flex-1">
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/onboarding" element={<Navigate to="/advisor" replace />} />
                <Route path="/advisor" element={<AdvisorPage />} />
                <Route path="/recommendations" element={<RecommendationsPage />} />
                <Route path="/quote" element={<QuotePage />} />
                <Route path="/kyc" element={<KYCPage />} />
                <Route path="/kyc/status" element={<KYCPage />} />
                <Route path="/order/confirmation" element={<OrderTrackerPage />} />
                <Route path="/track-order" element={<OrderTrackerPage />} />

                {/* Administrator Authentication & Portal */}
                <Route path="/admin/login" element={<AdminLoginPage />} />
                <Route
                  path="/admin"
                  element={
                    <Suspense fallback={<AdminLoadingFallback />}>
                      <AdminLayout />
                    </Suspense>
                  }
                >
                  <Route
                    index
                    element={
                      <Suspense fallback={<AdminLoadingFallback />}>
                        <AdminOverviewPage />
                      </Suspense>
                    }
                  />
                  <Route
                    path="overview"
                    element={
                      <Suspense fallback={<AdminLoadingFallback />}>
                        <AdminOverviewPage />
                      </Suspense>
                    }
                  />
                  <Route
                    path="leads"
                    element={
                      <Suspense fallback={<AdminLoadingFallback />}>
                        <AdminLeadsPage />
                      </Suspense>
                    }
                  />
                  <Route
                    path="kyc-exceptions"
                    element={
                      <Suspense fallback={<AdminLoadingFallback />}>
                        <AdminKYCExceptionsPage />
                      </Suspense>
                    }
                  />
                  <Route
                    path="model"
                    element={
                      <Suspense fallback={<AdminLoadingFallback />}>
                        <AdminModelPage />
                      </Suspense>
                    }
                  />
                </Route>
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
            <Footer />
          </div>
        </BrowserRouter>
      </OnboardingProvider>
    </AuthProvider>
  );
};

export default App;
