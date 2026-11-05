import React from 'react';
import { ShieldCheck, Cpu, HardDrive, HelpCircle } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-400 text-xs border-t border-slate-800 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand Col */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-lg bg-red-600 flex items-center justify-center text-white font-bold text-sm">
                360
              </div>
              <span className="text-white font-bold text-base">Udyam360</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              AI-driven digital onboarding and connectivity intelligence platform built for Indian MSMEs.
            </p>
            <div className="inline-flex items-center space-x-1.5 px-2 py-1 rounded bg-slate-800 text-[11px] text-slate-300 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Airtel SYNC 2026 Prototype</span>
            </div>
          </div>

          {/* Privacy & Guardrails */}
          <div>
            <h4 className="text-slate-200 font-semibold mb-3 flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Data Privacy Guardrails</span>
            </h4>
            <ul className="space-y-2">
              <li>100% Local OCR Execution</li>
              <li>Zero KYC Bytes sent to GenAI</li>
              <li>Encrypted Specimen Storage</li>
              <li>Masked Registry Verification</li>
            </ul>
          </div>

          {/* Core Modules */}
          <div>
            <h4 className="text-slate-200 font-semibold mb-3 flex items-center space-x-1.5">
              <Cpu className="w-4 h-4 text-blue-400" />
              <span>Architecture Components</span>
            </h4>
            <ul className="space-y-2">
              <li>Gemini Conversational Advisor</li>
              <li>Deterministic Bundle Resolver</li>
              <li>Strict Decimal Pricing Engine</li>
              <li>Order State Machine Engine</li>
            </ul>
          </div>

          {/* Hackathon Specs */}
          <div>
            <h4 className="text-slate-200 font-semibold mb-3 flex items-center space-x-1.5">
              <HelpCircle className="w-4 h-4 text-amber-400" />
              <span>Hackathon Prototype Notice</span>
            </h4>
            <p className="text-slate-400 leading-relaxed">
              Developed for Airtel SYNC Hackathon 2026, Enterprise Track A (Project Udyam Digital). All telecom activation events and registry lookups use hackathon datasets and simulated staging.
            </p>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between text-slate-500">
          <p>© 2026 Udyam360 Team. Built with FastAPI, Gemini API, and React.</p>
          <p className="mt-2 sm:mt-0 font-medium text-slate-400">Enterprise Track A — Project Udyam Digital</p>
        </div>
      </div>
    </footer>
  );
};

