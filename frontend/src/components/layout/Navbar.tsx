import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useOnboarding } from '../../context/OnboardingContext';
import {
  Sparkles,
  Package,
  FileCheck,
  ShieldCheck,
  Search,
  RotateCcw,
  Activity,
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { conversationId, resetOnboarding } = useOnboarding();

  const navLinks = [
    { path: '/advisor', label: 'AI Advisor', icon: Sparkles },
    { path: '/recommendations', label: 'Bundles & Catalogue', icon: Package },
    { path: '/quote', label: 'Quote Review', icon: FileCheck },
    { path: '/kyc', label: 'Smart KYC', icon: ShieldCheck },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm">
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

        {/* Navigation Step Pills */}
        <nav className="hidden md:flex items-center space-x-1 bg-slate-100/80 p-1 rounded-xl border border-slate-200">
          {navLinks.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-red-600' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right Action Buttons */}
        <div className="flex items-center space-x-3">
          {conversationId && (
            <button
              onClick={resetOnboarding}
              title="Reset conversation and start over"
              className="hidden lg:flex items-center space-x-1 px-2.5 py-1.5 text-xs font-medium text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-200"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Flow</span>
            </button>
          )}

          <Link
            to="/track-order"
            className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition-colors"
          >
            <Search className="w-3.5 h-3.5 text-slate-500" />
            <span>Track Order</span>
          </Link>

          <Link
            to="/advisor"
            className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-red-600 hover:bg-red-700 rounded-lg shadow-sm shadow-red-600/30 transition-all hover:shadow"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Get Started</span>
          </Link>
        </div>
      </div>
    </header>
  );
};

