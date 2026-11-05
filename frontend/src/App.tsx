import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { OnboardingProvider } from './context/OnboardingContext';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { ProgressBar } from './components/layout/ProgressBar';
import { LandingPage } from './pages/LandingPage';
import { AdvisorPage } from './pages/AdvisorPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { QuotePage } from './pages/QuotePage';
import { KYCPage } from './pages/KYCPage';
import { OrderTrackerPage } from './pages/OrderTrackerPage';
import { AdminLayout } from './pages/admin/AdminLayout';
import { AdminOverviewPage } from './pages/admin/AdminOverviewPage';
import { AdminLeadsPage } from './pages/admin/AdminLeadsPage';
import { AdminModelPage } from './pages/admin/AdminModelPage';

export const App: React.FC = () => {
  return (
    <OnboardingProvider>
      <BrowserRouter>
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
              <Route path="/admin" element={<AdminLayout />}>
                <Route index element={<AdminOverviewPage />} />
                <Route path="overview" element={<AdminOverviewPage />} />
                <Route path="leads" element={<AdminLeadsPage />} />
                <Route path="model" element={<AdminModelPage />} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </BrowserRouter>
    </OnboardingProvider>
  );
};

export default App;

