import React from 'react';
import { NavLink, Outlet, useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  BarChart3,
  Users,
  BrainCircuit,
  FileCheck2,
  TrendingUp,
  Loader2,
} from 'lucide-react';

export const AdminLayout: React.FC = () => {
  const { isAdminAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // 1. Loading state while session cookie is being verified against backend
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-8 text-white">
        <Loader2 className="w-10 h-10 text-red-600 animate-spin mb-4" />
        <p className="text-sm font-medium text-slate-300">Verifying administrator session...</p>
      </div>
    );
  }

  // 2. Strict Authentication Guard: Redirect to Admin Login if unauthenticated
  if (!isAdminAuthenticated) {
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }

  return (
    <div className="min-h-screen bg-slate-100/70 pb-10">
      {/* Subnavigation Bar */}
      <div className="bg-white border-b border-slate-200 shadow-xs sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <nav className="flex space-x-6 sm:space-x-8">
            <NavLink
              to="/admin"
              end
              className={({ isActive }) =>
                `flex items-center space-x-2 py-3.5 text-sm font-semibold border-b-2 transition-colors ${
                  isActive
                    ? 'border-red-600 text-red-600'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                }`
              }
            >
              <BarChart3 className="w-4 h-4" />
              <span>Funnel & KPI Analytics</span>
            </NavLink>

            <NavLink
              to="/admin/leads"
              className={({ isActive }) =>
                `flex items-center space-x-2 py-3.5 text-sm font-semibold border-b-2 transition-colors ${
                  isActive
                    ? 'border-red-600 text-red-600'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                }`
              }
            >
              <Users className="w-4 h-4" />
              <span>Lead Management</span>
            </NavLink>

            <NavLink
              to="/admin/kyc-exceptions"
              className={({ isActive }) =>
                `flex items-center space-x-2 py-3.5 text-sm font-semibold border-b-2 transition-colors ${
                  isActive
                    ? 'border-red-600 text-red-600'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                }`
              }
            >
              <FileCheck2 className="w-4 h-4" />
              <span>KYC Exception Copilot</span>
            </NavLink>

            <NavLink
              to="/admin/model"
              className={({ isActive }) =>
                `flex items-center space-x-2 py-3.5 text-sm font-semibold border-b-2 transition-colors ${
                  isActive
                    ? 'border-red-600 text-red-600'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                }`
              }
            >
              <BrainCircuit className="w-4 h-4" />
              <span>ML Model & Explainability</span>
            </NavLink>
          </nav>

          <div className="hidden lg:flex items-center space-x-2 text-xs text-slate-500 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
            <span className="font-medium text-slate-600">Benchmark:</span>
            <span className="font-bold text-emerald-700">368 / 5,000 (7.36%)</span>
          </div>
        </div>
      </div>

      {/* Main Content View */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        <Outlet />
      </div>
    </div>
  );
};

