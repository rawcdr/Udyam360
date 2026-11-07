import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useOnboarding } from '../../context/OnboardingContext';
import { useAuth } from '../../context/AuthContext';
import { CustomerAuthModal } from '../auth/CustomerAuthModal';
import {
  Sparkles,
  ShieldCheck,
  Shield,
  Search,
  RotateCcw,
  BarChart3,
  User,
  LogOut,
  ArrowLeft,
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { conversationId, resetOnboarding } = useOnboarding();
  const {
    customer,
    admin,
    isCustomerAuthenticated,
    isAdminAuthenticated,
    customerLogout,
    adminLogout,
  } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState<boolean>(false);

  const isAdminRoute = location.pathname.startsWith('/admin');
  const isOnboardingRoute = [
    '/advisor',
    '/recommendations',
    '/quote',
    '/kyc',
    '/track-order',
    '/order',
  ].some((p) => location.pathname.startsWith(p));

  return (
    <>
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand / Logo */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-red-600 to-rose-500 flex items-center justify-center shadow-md shadow-red-500/20 group-hover:scale-105 transition-transform">
              <span className="text-white font-extrabold text-xl tracking-tight">360</span>
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-extrabold text-lg text-slate-900 tracking-tight">Udyam360</span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-100 text-red-700 tracking-wide uppercase">
                  Airtel SYNC
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">MSME Digital Onboarding</p>
            </div>
          </Link>

          {/* Right Action Items */}
          <div className="flex items-center space-x-3">
            {/* Conversation reset (only on active onboarding routes) */}
            {conversationId && isOnboardingRoute && (
              <button
                onClick={resetOnboarding}
                title="Reset conversation and start over"
                className="flex items-center space-x-1 px-2.5 py-1.5 text-xs font-medium text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-200"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset Flow</span>
              </button>
            )}

            {/* STATE 1: ADMINISTRATOR LOGGED IN */}
            {isAdminAuthenticated ? (
              <>
                <div className="flex items-center space-x-2 bg-slate-900 text-white border border-slate-700 px-3 py-1.5 rounded-lg shadow-xs">
                  <Shield className="w-4 h-4 text-red-500" />
                  <span className="text-xs font-bold text-white">
                    {admin?.username || 'admin'}
                  </span>
                  <span className="text-[10px] bg-red-600 text-white font-extrabold px-1.5 py-0.5 rounded uppercase tracking-wider">
                    {admin?.role || 'Admin'}
                  </span>
                  <button
                    onClick={adminLogout}
                    title="Sign out administrator"
                    className="text-slate-400 hover:text-red-400 ml-1 p-0.5 rounded transition-colors"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                  </button>
                </div>

                {!isAdminRoute ? (
                  <Link
                    to="/admin"
                    className="flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition-colors"
                  >
                    <BarChart3 className="w-3.5 h-3.5 text-red-600" />
                    <span>Executive Admin</span>
                  </Link>
                ) : (
                  <Link
                    to="/"
                    className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition-colors"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Customer Flow</span>
                  </Link>
                )}

                <Link
                  to="/track-order"
                  className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition-colors"
                >
                  <Search className="w-3.5 h-3.5 text-slate-500" />
                  <span>Track Order</span>
                </Link>
              </>
            ) : isCustomerAuthenticated ? (
              /* STATE 2: CUSTOMER LOGGED IN */
              <>
                <div className="flex items-center space-x-2 bg-emerald-50 border border-emerald-200 px-2.5 py-1.5 rounded-lg shadow-xs">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span className="text-xs font-semibold text-emerald-900 hidden sm:inline">
                    {customer?.phone_number}
                  </span>
                  <button
                    onClick={customerLogout}
                    title="Sign out customer"
                    className="text-emerald-700 hover:text-red-600 p-0.5 rounded transition-colors"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                  </button>
                </div>

                <Link
                  to="/admin"
                  className="flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition-colors"
                >
                  <BarChart3 className="w-3.5 h-3.5 text-red-600" />
                  <span>Executive Admin</span>
                </Link>

                <Link
                  to="/track-order"
                  className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition-colors"
                >
                  <Search className="w-3.5 h-3.5 text-slate-500" />
                  <span>Track Order</span>
                </Link>

                {!isOnboardingRoute && !isAdminRoute && (
                  <Link
                    to="/advisor"
                    className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-red-600 hover:bg-red-700 rounded-lg shadow-sm shadow-red-600/30 transition-all hover:shadow"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Get Started</span>
                  </Link>
                )}
              </>
            ) : (
              /* STATE 3: ANONYMOUS GUEST (NEITHER ADMIN NOR CUSTOMER LOGGED IN) */
              <>
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition-colors"
                >
                  <User className="w-3.5 h-3.5 text-slate-500" />
                  <span>Sign In</span>
                </button>

                <Link
                  to="/admin"
                  className="flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition-colors"
                >
                  <BarChart3 className="w-3.5 h-3.5 text-red-600" />
                  <span>Executive Admin</span>
                </Link>

                <Link
                  to="/track-order"
                  className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition-colors"
                >
                  <Search className="w-3.5 h-3.5 text-slate-500" />
                  <span>Track Order</span>
                </Link>

                {!isOnboardingRoute && !isAdminRoute && (
                  <Link
                    to="/advisor"
                    className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-red-600 hover:bg-red-700 rounded-lg shadow-sm shadow-red-600/30 transition-all hover:shadow"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Get Started</span>
                  </Link>
                )}
              </>
            )}
          </div>
        </div>
      </header>

      {/* Auth Modal Triggered from Header */}
      <CustomerAuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onSuccess={() => setShowAuthModal(false)}
        advisorSessionId={conversationId || undefined}
      />
    </>
  );
};
