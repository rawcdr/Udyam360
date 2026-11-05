import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useOnboarding } from '../context/OnboardingContext';
import { quoteApi } from '../api/quotes';
import { kycApi } from '../api/kyc';
import {
  FileCheck,
  ShieldCheck,
  ArrowRight,
  Clock,
  Calendar,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  Building,
  MapPin,
  Check,
  Loader2,
} from 'lucide-react';

export const QuotePage: React.FC = () => {
  const navigate = useNavigate();
  const {
    profile,
    selectedProductIds,
    selectedBundleTier,
    quote,
    setQuote,
    conversationId,
    setKycCase,
  } = useOnboarding();

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isCreatingKYC, setIsCreatingKYC] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrRefreshQuote = async () => {
      if (selectedProductIds.length === 0) {
        navigate('/recommendations');
        return;
      }
      setIsLoading(true);
      try {
        const q = await quoteApi.previewQuote({
          profile,
          selected_product_ids: selectedProductIds,
          bundle_tier: selectedBundleTier,
        });
        setQuote(q);
      } catch (err: any) {
        setErrorMessage(err.message || 'Could not retrieve server quote preview.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchOrRefreshQuote();
  }, [selectedProductIds, selectedBundleTier]);

  const handleProceedToKYC = async () => {
    if (!quote) return;
    setIsCreatingKYC(true);
    setErrorMessage(null);
    try {
      // Create KYC case linked to advisor session, products, and quote reference
      const kycResponse = await kycApi.createCase({
        advisor_session_id: conversationId,
        selected_product_ids: selectedProductIds,
        quote_reference: quote.quote_id,
      });
      setKycCase(kycResponse);
      navigate('/kyc');
    } catch (err: any) {
      setErrorMessage('Could not initialize KYC onboarding case: ' + err.message);
    } finally {
      setIsCreatingKYC(false);
    }
  };

  if (isLoading || !quote) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <Loader2 className="w-10 h-10 text-red-600 animate-spin mx-auto mb-4" />
        <h2 className="text-xl font-bold text-slate-800">Calculating Server Authoritative Quote...</h2>
        <p className="text-xs text-slate-500 mt-1">Verifying catalogue dependencies and decimal pricing breakdown</p>
      </div>
    );
  }

  const { pricing } = quote;
  const mrc = pricing.monthly_total_min ?? (pricing as any).monthly_recurring_charges ?? 0;
  const otc = pricing.setup_total_min ?? (pricing as any).one_time_charges ?? 0;
  const firstMonth = pricing.estimated_first_month_min ?? (pricing as any).estimated_first_month_payable ?? (mrc + otc);
  const items = pricing.product_breakdown || (pricing as any).itemized_breakdown || [];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Title & Quote Reference */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Commercial Quote Preview
            </h1>
            <span className="px-2.5 py-0.5 rounded-full bg-red-100 text-red-700 text-xs font-bold uppercase">
              {quote.bundle_tier} Tier
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Official server-generated price quote based on Airtel commercial catalogue rates.
          </p>
        </div>

        <div className="bg-slate-100/90 rounded-xl p-3 border border-slate-200 text-right">
          <p className="text-[10px] font-bold uppercase text-slate-500">Quote Reference ID</p>
          <p className="text-base font-mono font-extrabold text-slate-900">{quote.quote_id}</p>
          <p className="text-[10px] text-slate-400">Valid for 30 calendar days</p>
        </div>
      </div>

      {errorMessage && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Grid: Itemized Breakdown + Summary Box */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start mb-8">
        {/* Left Column: Itemized Line Items (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Customer & Location Summary */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              Customer & Provisioning Site
            </h3>
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-slate-500 block">Business Entity:</span>
                <span className="font-bold text-slate-900">
                  {profile.business_name || 'Registered MSME Business'}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block">Target Location:</span>
                <span className="font-bold text-slate-900">
                  {profile.city || 'Bengaluru'} (Tier {profile.city_tier || 1})
                </span>
              </div>
              <div>
                <span className="text-slate-500 block">Customer Segment:</span>
                <span className="font-bold text-slate-900 uppercase">{quote.business_segment}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Total Sites:</span>
                <span className="font-bold text-slate-900">{profile.sites_count || 1} Location</span>
              </div>
            </div>
          </div>

          {/* Itemized Table */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
              Itemized Products & Services ({items.length})
            </h3>

            <div className="divide-y divide-slate-100">
              {items.map((item: any) => {
                const subtotal = item.monthly_subtotal_min ?? item.monthly_subtotal ?? 0;
                const setup = item.setup_subtotal ?? item.one_time_setup_fee ?? 0;
                const unit = item.unit || item.pricing_unit || 'unit';

                return (
                  <div key={item.product_id} className="py-3.5 flex items-center justify-between">
                    <div className="space-y-0.5">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-slate-900 text-sm">{item.product_name}</span>
                        <span className="text-[10px] font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-500">
                          {item.product_id}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">
                        Category: {item.category} • Qty: {item.quantity} ({unit})
                      </p>
                    </div>

                    <div className="text-right">
                      <p className="font-extrabold text-slate-900 text-sm">
                        ₹{subtotal.toLocaleString()}
                        <span className="text-[10px] font-normal text-slate-500">/mo</span>
                      </p>
                      {setup > 0 && (
                        <p className="text-[10px] text-slate-500 font-medium">
                          + ₹{setup.toLocaleString()} setup
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Delivery & SLA Guarantees */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center shrink-0">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Fulfillment Turnaround</p>
                <p className="text-sm font-extrabold text-slate-900">
                  {quote.typical_install_days} Business Days
                </p>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-purple-100 text-purple-600 flex items-center justify-center shrink-0">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Contract Commitment</p>
                <p className="text-sm font-extrabold text-slate-900">
                  {quote.min_contract_months} Months Term
                </p>
              </div>
            </div>
          </div>

          {/* Terms & Conditions */}
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 text-xs">
            <h4 className="font-bold text-slate-800 mb-2">Commercial Terms & Regulatory Conditions</h4>
            <ul className="space-y-1 text-slate-600 list-disc list-inside text-[11px]">
              {quote.terms_and_conditions.map((term, i) => (
                <li key={i}>{term}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right Column: Pricing Summary & Checkout Card (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-card sticky top-24">
            <h3 className="text-base font-extrabold text-slate-900 pb-3 border-b border-slate-100 mb-4">
              Billing & Charges Summary
            </h3>

            {/* Recurring vs OTC breakdown */}
            <div className="space-y-3 text-xs mb-6">
              <div className="flex items-center justify-between text-slate-600">
                <span>Monthly Recurring Charges (MRC)</span>
                <span className="font-bold text-slate-900 text-sm">
                  ₹{mrc.toLocaleString()}
                </span>
              </div>

              <div className="flex items-center justify-between text-slate-600">
                <span>One-Time Setup & Hardware (OTC)</span>
                <span className="font-bold text-slate-900 text-sm">
                  ₹{otc.toLocaleString()}
                </span>
              </div>

              <div className="flex items-center justify-between text-slate-500 pt-2 border-t border-slate-100 text-[11px]">
                <span>Applicable GST (18%)</span>
                <span>Calculated on invoicing</span>
              </div>

              {/* First Month Total Highlight */}
              <div className="pt-3 border-t border-slate-200 mt-2 bg-red-50/60 -mx-6 px-6 py-4">
                <div className="flex items-baseline justify-between">
                  <div>
                    <span className="text-xs font-bold text-red-700 block uppercase tracking-wider">
                      Estimated First-Month Payable
                    </span>
                    <span className="text-[11px] text-slate-500 font-medium">Includes MRC + OTC</span>
                  </div>
                  <span className="text-2xl font-black text-red-600">
                    ₹{firstMonth.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Subsequent Months */}
              <div className="flex items-baseline justify-between pt-2 text-slate-700 font-medium">
                <span>Subsequent Monthly Billing:</span>
                <span className="font-bold text-slate-900">
                  ₹{mrc.toLocaleString()} /mo
                </span>
              </div>
            </div>

            {/* Prototype Notice */}
            <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-800 text-[11px] mb-6 flex items-start space-x-2">
              <HelpCircle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
              <div>
                <p className="font-bold">Prototype Demonstration Notice</p>
                <p className="text-amber-700 mt-0.5">
                  No real payment gateway transaction is executed in this prototype. Proceed directly to Smart KYC document verification.
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <button
                onClick={handleProceedToKYC}
                disabled={isCreatingKYC}
                className="w-full py-3.5 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold rounded-xl shadow-md shadow-red-600/25 hover:shadow-lg transition-all flex items-center justify-center space-x-2 text-sm"
              >
                {isCreatingKYC ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Initializing KYC Case...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Confirm Quote & Proceed to KYC</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>

              <button
                onClick={() => navigate('/recommendations')}
                className="w-full py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition-colors"
              >
                Modify Products & Add-ons
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
