import React from 'react';
import { NavLink, Outlet, Link } from 'react-router-dom';
import {
  BarChart3,
  Users,
  BrainCircuit,
  ShieldAlert,
  ArrowLeft,
  Building2,
  TrendingUp,
} from 'lucide-react';

export const AdminLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-100/70 pb-16">
      {/* Enterprise Top Banner */}
      <div className="bg-slate-900 text-white border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-red-600 flex items-center justify-center font-bold text-white shadow-lg shadow-red-600/30">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold tracking-tight">Executive Admin & Sales Intelligence</h1>
                <span className="text-[11px] font-semibold bg-red-950/80 text-red-300 border border-red-700/50 px-2 py-0.5 rounded-full flex items-center space-x-1">
                  <ShieldAlert className="w-3 h-3 inline mr-1 text-red-400" />
                  Role: ExecutiveAdmin
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Airtel SYNC Hackathon 2026 — Track A Lead Propensity & Conversion Telemetry
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold text-slate-300">Dataset: 5,000 Accounts</div>
              <div className="text-[11px] text-emerald-400 font-medium flex items-center justify-end space-x-1">
                <TrendingUp className="w-3 h-3 mr-0.5 inline" />
                <span>Benchmark: 368 Activations (7.36%)</span>
              </div>
            </div>
            <Link
              to="/"
              className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Customer Flow</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Subnavigation Bar */}
      <div className="bg-white border-b border-slate-200 shadow-sm sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
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
              <span>Lead Management & Propensity</span>
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
        </div>
      </div>

      {/* Main Content View */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        <Outlet />
      </div>
    </div>
  );
};

