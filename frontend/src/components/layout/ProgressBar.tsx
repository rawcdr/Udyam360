import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Check, Sparkles, Package, FileCheck, ShieldCheck, Truck } from 'lucide-react';

export const ProgressBar: React.FC = () => {
  const location = useLocation();

  const steps = [
    { id: 1, name: 'AI Advisor', path: '/advisor', icon: Sparkles },
    { id: 2, name: 'Bundles & Catalogue', path: '/recommendations', icon: Package },
    { id: 3, name: 'Quote Review', path: '/quote', icon: FileCheck },
    { id: 4, name: 'Smart KYC', path: '/kyc', icon: ShieldCheck },
    { id: 5, name: 'Order Status', path: '/track-order', icon: Truck },
  ];

  const getCurrentStepIndex = () => {
    const path = location.pathname;
    if (path.startsWith('/advisor')) return 0;
    if (path.startsWith('/recommendations')) return 1;
    if (path.startsWith('/quote')) return 2;
    if (path.startsWith('/kyc')) return 3;
    if (path.startsWith('/track-order') || path.startsWith('/order')) return 4;
    return -1;
  };

  const currentIndex = getCurrentStepIndex();
  if (currentIndex === -1) return null; // Don't show on landing page

  return (
    <div className="bg-white border-b border-slate-200 py-3 shadow-xs">
      <div className="max-w-5xl mx-auto px-4">
        <div className="flex items-center justify-between">
          {steps.map((step, idx) => {
            const isCompleted = idx < currentIndex;
            const isCurrent = idx === currentIndex;
            const Icon = step.icon;

            return (
              <React.Fragment key={step.id}>
                {/* Step Item */}
                <Link
                  to={isCompleted || isCurrent ? step.path : '#'}
                  className={`flex items-center space-x-2.5 transition-colors ${
                    !isCompleted && !isCurrent ? 'pointer-events-none opacity-60' : ''
                  }`}
                >
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                      isCompleted
                        ? 'bg-emerald-600 text-white'
                        : isCurrent
                        ? 'bg-red-600 text-white ring-4 ring-red-100 shadow'
                        : 'bg-slate-200 text-slate-500'
                    }`}
                  >
                    {isCompleted ? <Check className="w-3.5 h-3.5" /> : idx + 1}
                  </div>
                  <span
                    className={`text-xs font-semibold hidden sm:inline ${
                      isCurrent
                        ? 'text-slate-900 font-bold'
                        : isCompleted
                        ? 'text-emerald-700'
                        : 'text-slate-500'
                    }`}
                  >
                    {step.name}
                  </span>
                </Link>

                {/* Connecting Line */}
                {idx < steps.length - 1 && (
                  <div className="flex-1 mx-2 sm:mx-4 h-0.5 bg-slate-200 relative overflow-hidden">
                    <div
                      className={`absolute inset-0 bg-emerald-500 transition-all duration-300 ${
                        idx < currentIndex ? 'w-full' : 'w-0'
                      }`}
                    />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
};

