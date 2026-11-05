import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { orderApi } from '../api/orders';
import { OrderResponse, OrderState, OrderTimelineEvent } from '../types/order';
import {
  Search,
  Truck,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileCheck,
  ShieldCheck,
  Cpu,
  Radio,
  Sparkles,
  ArrowRight,
  RotateCw,
  Building,
  HelpCircle,
  Loader2,
} from 'lucide-react';

export const OrderTrackerPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialRef = searchParams.get('ref') || '';

  const [searchRef, setSearchRef] = useState<string>(initialRef);
  const [order, setOrder] = useState<OrderResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isAdvancing, setIsAdvancing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchOrder = async (ref: string) => {
    if (!ref.trim()) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await orderApi.trackByReference(ref.trim());
      setOrder(data);
      setSearchParams({ ref: ref.trim() });
    } catch (err: any) {
      setOrder(null);
      setErrorMessage(err.message || `No order found matching '${ref}'.`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (initialRef) {
      fetchOrder(initialRef);
    }
  }, [initialRef]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchOrder(searchRef);
  };

  const handleAdvanceSimulation = async () => {
    if (!order) return;
    setIsAdvancing(true);
    try {
      const updated = await orderApi.advance(order.order_id);
      setOrder(updated);
    } catch (err: any) {
      setErrorMessage('Could not advance state: ' + err.message);
    } finally {
      setIsAdvancing(false);
    }
  };

  // State Stepper definition
  const allMilestones: { state: OrderState; label: string; desc: string }[] = [
    {
      state: 'QUOTE_CONFIRMED',
      label: 'Quote Confirmed',
      desc: 'Selected bundle & rates registered in catalogue.',
    },
    {
      state: 'KYC_PENDING',
      label: 'KYC Required',
      desc: 'Pending customer consent & document submission.',
    },
    {
      state: 'KYC_VERIFICATION',
      label: 'OCR Verification',
      desc: 'Local OCR parsing & registry cross-check.',
    },
    {
      state: 'KYC_VERIFIED',
      label: 'Identity Approved',
      desc: 'Business identity verified against registries.',
    },
    {
      state: 'ORDER_PROCESSING',
      label: 'Provisioning Order',
      desc: 'Backend allocation of IP, SIM & circuits (Simulated).',
    },
    {
      state: 'ACTIVATION_IN_PROGRESS',
      label: 'Field Dispatch',
      desc: 'CPE router delivery & on-site line setup (Simulated).',
    },
    {
      state: 'ACTIVATED',
      label: 'Services Active',
      desc: 'Commercial broadband & cloud lines online (Simulated).',
    },
  ];

  const getStepIndex = (state: OrderState) => {
    if (state === 'MANUAL_REVIEW') return 2; // Under verification
    return allMilestones.findIndex((m) => m.state === state);
  };

  const currentIdx = order ? getStepIndex(order.current_state) : -1;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto mb-8">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold mb-3">
          <Truck className="w-3.5 h-3.5 text-red-600" />
          <span>Real-Time Activation Lifecycle</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Track Your Business Onboarding
        </h1>
        <p className="text-sm text-slate-500 mt-2">
          Enter your order reference number to view live state transitions, fulfillment stages, and service activation milestones.
        </p>

        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="mt-6 flex items-center justify-center max-w-md mx-auto gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchRef}
              onChange={(e) => setSearchRef(e.target.value)}
              placeholder="e.g. UDYAM-ORD-2026-..."
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-300 rounded-xl text-sm font-mono focus:outline-hidden focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all shadow-xs"
            />
          </div>
          <button
            type="submit"
            aria-label="Track"
            disabled={isLoading || !searchRef.trim()}
            className="px-5 py-2.5 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-xs transition-colors flex items-center space-x-1.5"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Track</span>}
          </button>
        </form>
      </div>

      {errorMessage && (
        <div className="max-w-md mx-auto mb-8 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Order Details Display */}
      {order && (
        <div className="space-y-8">
          {/* Status Banner */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Tracking Reference
                </span>
                <h2 className="text-2xl font-black font-mono text-slate-900 mt-0.5">
                  {order.order_reference}
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  Entity: <strong>{order.customer_info.business_name}</strong> • Location: {order.customer_info.city || 'India'}
                </p>
              </div>

              <div className="flex flex-col sm:items-end">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Current Lifecycle State
                </span>
                <div className="flex items-center space-x-2 mt-1">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase ${
                      order.current_state === 'ACTIVATED'
                        ? 'bg-emerald-100 text-emerald-800'
                        : order.current_state === 'MANUAL_REVIEW'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}
                  >
                    {order.current_state.replace(/_/g, ' ')}
                  </span>
                </div>
                {order.is_simulated_stage && (
                  <span className="text-[10px] text-purple-600 font-bold mt-1 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                    Demo Simulated Stage
                  </span>
                )}
              </div>
            </div>

            {/* Next Action Prompt */}
            {order.next_action_prompt && (
              <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-slate-500" />
                  <span className="text-slate-700 font-medium">
                    Status Note: {order.next_action_prompt}
                  </span>
                </div>

                {/* Simulation trigger */}
                {order.current_state !== 'ACTIVATED' && order.current_state !== 'CANCELLED' && (
                  <button
                    onClick={handleAdvanceSimulation}
                    disabled={isAdvancing}
                    title="Click to simulate next lifecycle event"
                    className="ml-2 px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white font-bold text-[11px] rounded-lg shadow-xs flex items-center space-x-1 shrink-0 transition-colors"
                  >
                    {isAdvancing ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <RotateCw className="w-3.5 h-3.5" />
                    )}
                    <span>Simulate Next Step</span>
                  </button>
                )}
              </div>
            )}

            {/* Stepper Visualization */}
            <div className="mt-8 pt-4">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-6">
                Lifecycle Progression
              </h3>

              <div className="relative">
                <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
                  {allMilestones.map((m, idx) => {
                    const isCompleted = idx < currentIdx;
                    const isCurrent = idx === currentIdx;

                    return (
                      <div
                        key={m.state}
                        className={`p-3 rounded-xl border transition-all ${
                          isCurrent
                            ? 'bg-red-50/50 border-red-300 ring-2 ring-red-500/20 shadow-xs'
                            : isCompleted
                            ? 'bg-emerald-50/30 border-emerald-200'
                            : 'bg-slate-50/60 border-slate-200 opacity-60'
                        }`}
                      >
                        <div className="flex items-center space-x-1.5 mb-1.5">
                          <div
                            className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                              isCompleted
                                ? 'bg-emerald-600 text-white'
                                : isCurrent
                                ? 'bg-red-600 text-white animate-pulse'
                                : 'bg-slate-300 text-slate-600'
                            }`}
                          >
                            {isCompleted ? <CheckCircle2 className="w-3.5 h-3.5" /> : idx + 1}
                          </div>
                          <span
                            className={`text-xs font-bold leading-tight ${
                              isCurrent
                                ? 'text-red-700'
                                : isCompleted
                                ? 'text-emerald-800'
                                : 'text-slate-600'
                            }`}
                          >
                            {m.label}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 leading-snug">{m.desc}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Timeline Event Log + Order Specs */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left: Audit Timeline Events (7 cols) */}
            <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
                Milestone Event History ({order.timeline.length})
              </h3>

              <div className="space-y-4">
                {order.timeline.map((evt) => (
                  <div key={evt.event_id} className="flex items-start space-x-3 text-xs">
                    <div
                      className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 ${
                        evt.is_simulated ? 'bg-purple-500' : 'bg-emerald-500'
                      }`}
                    />
                    <div className="flex-1 pb-3 border-b border-slate-100">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900">{evt.title}</span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {new Date(evt.timestamp).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                          })}
                        </span>
                      </div>
                      <p className="text-slate-600 mt-0.5 leading-relaxed">{evt.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Order Snapshot (5 cols) */}
            <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4 text-xs">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider pb-2 border-b border-slate-100">
                Order Configuration Snapshot
              </h3>

              <div className="space-y-2.5">
                <div className="flex justify-between">
                  <span className="text-slate-500">Selected Bundle:</span>
                  <span className="font-bold text-slate-900">{order.bundle_tier || 'Custom'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Quote Reference:</span>
                  <span className="font-mono font-bold text-slate-900">{order.quote_reference}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">KYC Case ID:</span>
                  <span className="font-mono font-bold text-slate-900">
                    {order.kyc_case_id || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Monthly Recurring (MRC):</span>
                  <span className="font-bold text-slate-900">
                    ₹{order.pricing.monthly_recurring_charges.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">One-Time Setup (OTC):</span>
                  <span className="font-bold text-slate-900">
                    ₹{order.pricing.one_time_charges.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between pt-2 border-t border-slate-100 text-sm font-extrabold text-red-600">
                  <span>First Month Payable:</span>
                  <span>₹{order.pricing.estimated_first_month.toLocaleString()}</span>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100">
                <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] block mb-2">
                  Active Products ({order.selected_product_ids.length})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {order.selected_product_ids.map((pid) => (
                    <span
                      key={pid}
                      className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono font-semibold text-[11px]"
                    >
                      {pid}
                    </span>
                  ))}
                </div>
              </div>

              {/* Prototype Notice Box */}
              <div className="p-3 bg-purple-50 rounded-xl border border-purple-200 text-purple-900 text-[11px] leading-relaxed">
                <p className="font-bold mb-0.5 flex items-center space-x-1">
                  <HelpCircle className="w-3.5 h-3.5 text-purple-600" />
                  <span>Prototype Provisioning Simulation</span>
                </p>
                Later provisioning and network activation steps are simulated demonstrations for the Airtel SYNC Hackathon 2026.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
