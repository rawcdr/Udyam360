import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  Package,
  ShieldCheck,
  Truck,
  ArrowRight,
  Store,
  Briefcase,
  CheckCircle2,
  Clock,
  Layers,
  FileCheck,
} from 'lucide-react';
import { catalogueApi } from '../api/catalogue';
import { advisorApi } from '../api/advisor';
import { CatalogueSummary } from '../types/catalogue';

export const LandingPage: React.FC = () => {
  const [summary, setSummary] = useState<CatalogueSummary | null>(null);
  const [advisorOnline, setAdvisorOnline] = useState<boolean>(true);

  useEffect(() => {
    catalogueApi
      .getSummary()
      .then(setSummary)
      .catch((err) => console.warn('Could not load catalogue summary:', err));

    advisorApi
      .getHealth()
      .then((h) => setAdvisorOnline(h.status === 'HEALTHY'))
      .catch(() => setAdvisorOnline(false));
  }, []);

  return (
    <div className="relative overflow-hidden">
      {/* Hero Section */}
      <section className="relative pt-12 pb-20 md:pt-20 md:pb-32 gradient-hero">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            {/* Tag pill */}
            <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-red-50 border border-red-200/60 text-red-700 text-xs font-semibold mb-6 shadow-xs">
              <span className="w-2 h-2 rounded-full bg-red-600 animate-ping"></span>
              <span>Airtel SYNC Hackathon 2026 — Enterprise Track A</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Your Entire Business, Connected in{' '}
              <span className="text-red-600 underline decoration-red-200 underline-offset-8">
                One Place.
              </span>
            </h1>

            {/* Supporting Text */}
            <p className="mt-6 text-lg sm:text-xl text-slate-600 font-normal leading-relaxed">
              Get business connectivity, communication, cloud and security services tailored to your needs — with a simple digital onboarding experience.
            </p>

            {/* CTAs */}
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/advisor"
                className="w-full sm:w-auto px-8 py-3.5 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl shadow-lg shadow-red-600/30 hover:shadow-xl transition-all flex items-center justify-center space-x-2 text-base"
              >
                <span>Get Started</span>
                <ArrowRight className="w-5 h-5" />
              </Link>

              <Link
                to="/track-order"
                className="w-full sm:w-auto px-8 py-3.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold rounded-xl border border-slate-300 shadow-sm transition-all flex items-center justify-center space-x-2 text-base"
              >
                <Clock className="w-5 h-5 text-slate-500" />
                <span>Track My Order</span>
              </Link>
            </div>

            {/* Trust / Stats Banner */}
            <div className="mt-12 pt-8 border-t border-slate-200/80 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="p-3">
                <p className="text-2xl font-extrabold text-slate-900">
                  {summary ? `${summary.total_products}` : '25'}
                </p>
                <p className="text-xs font-medium text-slate-500">Catalogue Products</p>
              </div>
              <div className="p-3">
                <p className="text-2xl font-extrabold text-slate-900">3 Tiers</p>
                <p className="text-xs font-medium text-slate-500">Essential, Growth, Premium</p>
              </div>
              <div className="p-3">
                <p className="text-2xl font-extrabold text-slate-900">100%</p>
                <p className="text-xs font-medium text-slate-500">Local OCR & Private KYC</p>
              </div>
              <div className="p-3">
                <div className="flex items-center justify-center space-x-1.5 text-2xl font-extrabold text-emerald-600">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  <span>{advisorOnline ? 'Live' : 'Standby'}</span>
                </div>
                <p className="text-xs font-medium text-slate-500">GenAI Business Advisor</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4 Key Journey Steps */}
      <section className="py-20 bg-white border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-xs font-bold text-red-600 tracking-wider uppercase mb-2">
              Four Seamless Steps
            </h2>
            <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
              From natural conversation to live activation
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Step 1 */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-6 relative hover:shadow-card-hover transition-all">
              <div className="w-12 h-12 rounded-xl bg-red-100 text-red-600 flex items-center justify-center mb-5 font-bold">
                <Sparkles className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-red-600 uppercase tracking-wider">Step 1</span>
              <h3 className="text-lg font-bold text-slate-900 mt-1 mb-2">Understand your business</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Describe your store, clinic, or firm in everyday language. Our GenAI Advisor extracts requirements and maps your eligibility.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-6 relative hover:shadow-card-hover transition-all">
              <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center mb-5 font-bold">
                <Package className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">Step 2</span>
              <h3 className="text-lg font-bold text-slate-900 mt-1 mb-2">Personalized recommendations</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Compare deterministic Essential, Growth, and Premium bundles. Customize add-ons with instant server-authoritative quotes.
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-6 relative hover:shadow-card-hover transition-all">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-5 font-bold">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">Step 3</span>
              <h3 className="text-lg font-bold text-slate-900 mt-1 mb-2">Complete digital onboarding</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Consent-first KYC with local document OCR and mock GSTIN/Udyam registry cross-verification with zero cloud PII leakage.
              </p>
            </div>

            {/* Step 4 */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-6 relative hover:shadow-card-hover transition-all">
              <div className="w-12 h-12 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center mb-5 font-bold">
                <Truck className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-purple-600 uppercase tracking-wider">Step 4</span>
              <h3 className="text-lg font-bold text-slate-900 mt-1 mb-2">Track your activation</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Receive an authoritative order reference. Follow real-time milestone transitions through field fulfillment to active service.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Target Segments Feature */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-xs font-bold text-red-600 tracking-wider uppercase mb-2">
              Tailored For Your Industry
            </h2>
            <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Designed specifically for Indian MSME Segments
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Micro Retail */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-card hover:shadow-card-hover transition-all">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center">
                  <Store className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Micro Retail</h3>
                  <p className="text-xs text-slate-500 font-medium">Kiranas, Pharmacies, Salons, Outlets</p>
                </div>
              </div>
              <p className="text-sm text-slate-600 mb-6 leading-relaxed">
                Affordable, high-uptime commercial broadband bundled with digital POS payment backup, CCTV store security, and quick Udyam-based onboarding without requiring GST registration.
              </p>
              <ul className="space-y-2.5 text-xs text-slate-700 font-medium">
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span>Budget-friendly packages starting under ₹1,500/month</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span>Dual WAN POS fallback for zero payment downtime</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span>Udyam and Trade License validation support</span>
                </li>
              </ul>
            </div>

            {/* Professional Offices */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-card hover:shadow-card-hover transition-all">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center">
                  <Briefcase className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Professional Offices</h3>
                  <p className="text-xs text-slate-500 font-medium">Clinics, CA Firms, Coaching Centers, Consultancies</p>
                </div>
              </div>
              <p className="text-sm text-slate-600 mb-6 leading-relaxed">
                Enterprise fiber connectivity, virtual cloud PBX, corporate Google Workspace / Microsoft 365 productivity suites, and secure multi-user branch routing.
              </p>
              <ul className="space-y-2.5 text-xs text-slate-700 font-medium">
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span>Dedicated bandwidth with enterprise 99.5% SLAs</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span>Multi-line business calling and virtual receptionist</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span>GSTIN-compliant invoicing and automatic tax verification</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Box */}
      <section className="py-16 bg-red-600 text-white">
        <div className="max-w-5xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
            Ready to empower your business?
          </h2>
          <p className="mt-4 text-lg text-red-100 max-w-2xl mx-auto">
            Experience our intelligent GenAI advisor. No technical expertise required.
          </p>
          <div className="mt-8 flex justify-center">
            <Link
              to="/advisor"
              className="px-8 py-3.5 bg-white text-red-600 hover:bg-slate-100 font-bold rounded-xl shadow-lg transition-all"
            >
              Start Free Assessment
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

