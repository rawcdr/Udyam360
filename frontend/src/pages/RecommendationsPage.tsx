import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useOnboarding } from '../context/OnboardingContext';
import { recommendationApi } from '../api/recommendations';
import { catalogueApi } from '../api/catalogue';
import { RecommendedBundle } from '../types/recommendations';
import { Product } from '../types/catalogue';
import {
  Package,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Check,
  Plus,
  Minus,
  Sparkles,
  Layers,
  ChevronDown,
  ChevronUp,
  Info,
  DollarSign,
  Loader2,
} from 'lucide-react';

export const RecommendationsPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    profile,
    recommendations,
    setRecommendations,
    selectedBundleTier,
    selectedProductIds,
    selectBundle,
    toggleAddon,
    quote,
    isRecalculatingQuote,
  } = useOnboarding();

  const [catalogue, setCatalogue] = useState<Product[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showCatalogueDrawer, setShowCatalogueDrawer] = useState<boolean>(false);
  const [expandedTier, setExpandedTier] = useState<string | null>('Growth');

  useEffect(() => {
    // If recommendations are not yet loaded, fetch them from backend
    const loadRecommendationsAndCatalogue = async () => {
      setIsLoading(true);
      try {
        if (!recommendations) {
          const recs = await recommendationApi.getRecommendations(profile);
          setRecommendations(recs);
          if (recs.growth_bundle && selectedProductIds.length <= 2) {
            await selectBundle(recs.growth_bundle);
          }
        }
        const prods = await catalogueApi.getAll();
        setCatalogue(prods);
      } catch (err) {
        console.error('Error loading recommendations or catalogue:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadRecommendationsAndCatalogue();
  }, []);

  const bundles: RecommendedBundle[] = recommendations
    ? ([
        recommendations.essential_bundle,
        recommendations.growth_bundle,
        recommendations.premium_bundle,
      ].filter(Boolean) as RecommendedBundle[])
    : [];

  const categories = ['All', ...new Set(catalogue.map((p) => p.category))];

  const filteredCatalogue =
    selectedCategory === 'All'
      ? catalogue
      : catalogue.filter((p) => p.category === selectedCategory);

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'Essential':
        return {
          border: 'border-blue-200',
          badge: 'bg-blue-100 text-blue-800',
          highlight: 'text-blue-600',
          bg: 'bg-blue-50/50',
          button: 'bg-blue-600 hover:bg-blue-700',
        };
      case 'Growth':
        return {
          border: 'border-red-400 ring-2 ring-red-500/20',
          badge: 'bg-red-600 text-white',
          highlight: 'text-red-600',
          bg: 'bg-red-50/30',
          button: 'bg-red-600 hover:bg-red-700',
        };
      case 'Premium':
        return {
          border: 'border-purple-200',
          badge: 'bg-purple-100 text-purple-800',
          highlight: 'text-purple-600',
          bg: 'bg-purple-50/50',
          button: 'bg-purple-700 hover:bg-purple-800',
        };
      default:
        return {
          border: 'border-slate-200',
          badge: 'bg-slate-100 text-slate-800',
          highlight: 'text-slate-600',
          bg: 'bg-slate-50',
          button: 'bg-slate-800 hover:bg-slate-900',
        };
    }
  };

  const getBudgetStatusBadge = (status: string) => {
    if (status === 'WITHIN_BUDGET') {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          <span>Within Monthly Budget</span>
        </span>
      );
    }
    if (status === 'PARTIALLY_WITHIN_BUDGET') {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 text-[11px] font-bold">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
          <span>Partially Within Budget</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-rose-100 text-rose-800 text-[11px] font-bold">
        <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
        <span>Exceeds Budget Range</span>
      </span>
    );
  };

  if (isLoading && !recommendations) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <Loader2 className="w-10 h-10 text-red-600 animate-spin mx-auto mb-4" />
        <h2 className="text-xl font-bold text-slate-800">Calculating Deterministic Recommendations...</h2>
        <p className="text-sm text-slate-500 mt-1">Applying catalogue constraints and hard eligibility rules</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Recommended Product Bundles
            </h1>
            <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold">
              {profile.business_type || 'MSME'} • {profile.city || 'India'}
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Engine-scored packages tailored for your budget (₹
            {profile.budget_monthly?.toLocaleString() || '3,000'}/mo) and operational profile.
          </p>
        </div>

        {/* Live Quote summary pill */}
        {quote && (
          <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-xs flex items-center space-x-4">
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-400">Monthly Recurring</p>
              <p className="text-lg font-extrabold text-slate-900">
                ₹{(quote.pricing.monthly_total_min ?? (quote.pricing as any).monthly_recurring_charges ?? 0).toLocaleString()}
                <span className="text-xs font-normal text-slate-500">/mo</span>
              </p>
            </div>
            <div className="h-8 w-px bg-slate-200" />
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-400">First Month Payable</p>
              <p className="text-base font-extrabold text-red-600">
                ₹{(quote.pricing.estimated_first_month_min ?? (quote.pricing as any).estimated_first_month_payable ?? 0).toLocaleString()}
              </p>
            </div>
            <button
              onClick={() => navigate('/quote')}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded-lg shadow-sm transition-all flex items-center space-x-1"
            >
              <span>Review Quote</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* 3 Bundle Option Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
        {bundles.map((bundle) => {
          const tier = bundle.bundle_tier || (bundle as any).tier;
          const colors = getTierColor(tier);
          const isSelected = selectedBundleTier === tier;
          const isExpanded = expandedTier === tier;

          const minMonthly = bundle.pricing?.monthly_total_min ?? (bundle as any).monthly_price_min ?? 0;
          const maxMonthly = bundle.pricing?.monthly_total_max ?? (bundle as any).monthly_price_max ?? 0;
          const setupFee = bundle.pricing?.setup_total_min ?? (bundle as any).one_time_setup_total ?? 0;
          const productsList = bundle.products || (bundle as any).included_products || [];
          const rationale = bundle.explanation?.operational_rationale || (bundle as any).target_profile_summary || '';

          return (
            <div
              key={tier}
              className={`rounded-2xl bg-white border ${colors.border} ${
                isSelected ? 'shadow-card-hover' : 'shadow-card'
              } flex flex-col transition-all overflow-hidden relative`}
            >
              {/* Popular / Recommended Tag */}
              {tier === 'Growth' && (
                <div className="absolute top-0 right-0 bg-red-600 text-white text-[10px] font-extrabold px-3 py-1 rounded-bl-xl tracking-wider uppercase shadow-xs">
                  ★ Recommended Fit
                </div>
              )}

              {/* Card Header */}
              <div className={`p-6 ${colors.bg} border-b border-slate-100`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs font-extrabold px-2.5 py-0.5 rounded-full ${colors.badge}`}>
                    {tier} Bundle
                  </span>
                  {getBudgetStatusBadge(bundle.budget_status)}
                </div>

                <h3 className="text-xl font-bold text-slate-900 mt-2">{bundle.bundle_name}</h3>
                <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                  {rationale}
                </p>

                {/* Price Display */}
                <div className="mt-4 pt-3 border-t border-slate-200/60 flex items-baseline justify-between">
                  <div>
                    <span className="text-2xl font-extrabold text-slate-900">
                      ₹{minMonthly.toLocaleString()}
                    </span>
                    {minMonthly !== maxMonthly && (
                      <span className="text-sm font-semibold text-slate-500">
                        {' '}– ₹{maxMonthly.toLocaleString()}
                      </span>
                    )}
                    <span className="text-xs text-slate-500 font-medium"> /month</span>
                  </div>

                  <span className="text-xs font-semibold text-slate-500">
                    + ₹{setupFee.toLocaleString()} setup
                  </span>
                </div>
              </div>

              {/* Products in this bundle */}
              <div className="p-6 flex-1 flex flex-col justify-between space-y-4">
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                    Included Services ({productsList.length})
                  </h4>
                  <ul className="space-y-3">
                    {productsList.map((item: any) => (
                      <li key={item.product_id} className="flex items-start space-x-2.5 text-xs">
                        <div className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 mt-0.5">
                          <Check className="w-3 h-3" />
                        </div>
                        <div>
                          <div className="flex items-center space-x-1.5">
                            <span className="font-bold text-slate-900">{item.product_name}</span>
                            <span className="text-[10px] px-1 py-0.2 bg-slate-100 text-slate-500 font-mono rounded">
                              {item.product_id}
                            </span>
                          </div>
                          <p className="text-slate-500 text-[11px] mt-0.5 leading-snug">
                            {item.relevance_reason || item.description || ''}
                          </p>
                        </div>
                      </li>
                    ))}
                  </ul>

                  {/* Accordion: Full Explanation & Advantages */}
                  <button
                    onClick={() => setExpandedTier(isExpanded ? null : tier)}
                    className="mt-4 text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center space-x-1 py-1"
                  >
                    <span>{isExpanded ? 'Hide' : 'Show'} Engine Explanation & Advantages</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>

                  {isExpanded && bundle.explanation && (
                    <div className="mt-3 p-3 bg-slate-50 rounded-xl text-xs space-y-2 border border-slate-200/80">
                      <p className="text-slate-700 font-medium">{bundle.explanation.budget_fit_text || bundle.explanation.operational_rationale}</p>
                      {bundle.explanation.key_advantages?.length > 0 && (
                        <div>
                          <p className="font-bold text-slate-800 text-[11px] mb-1">Key Advantages:</p>
                          <ul className="list-disc list-inside space-y-0.5 text-slate-600 text-[11px]">
                            {bundle.explanation.key_advantages.map((adv: string, idx: number) => (
                              <li key={idx}>{adv}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {bundle.explanation.risk_warnings?.length > 0 && (
                        <div className="text-amber-800 bg-amber-50 p-2 rounded border border-amber-200">
                          <p className="font-bold text-[11px]">Considerations:</p>
                          <p className="text-[11px]">{bundle.explanation.risk_warnings.join(' • ')}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Select Bundle Button */}
                <div className="pt-4 border-t border-slate-100">
                  <button
                    onClick={() => selectBundle(bundle)}
                    disabled={isRecalculatingQuote}
                    className={`w-full py-2.5 rounded-xl font-bold text-xs flex items-center justify-center space-x-2 transition-all ${
                      isSelected
                        ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm'
                        : `${colors.button} text-white shadow-xs`
                    }`}
                  >
                    {isSelected ? (
                      <>
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Selected Bundle</span>
                      </>
                    ) : (
                      <>
                        <span>Select {tier}</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Catalogue & Add-on Management Drawer/Section */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
                Catalogue Add-ons & Customization
              </h2>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                {selectedProductIds.length} Products Active
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Toggle individual services. Server recalculated quote updates instantly with strict decimal pricing.
            </p>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 sm:pb-0">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shrink-0 ${
                  selectedCategory === cat
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Product Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCatalogue.map((prod) => {
            const isSelected = selectedProductIds.includes(prod.product_id);

            return (
              <div
                key={prod.product_id}
                className={`p-4 rounded-xl border transition-all ${
                  isSelected
                    ? 'border-red-400 bg-red-50/20 shadow-2xs ring-1 ring-red-400'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                      {prod.product_id} • {prod.category}
                    </span>
                    <h4 className="font-bold text-slate-900 text-sm leading-snug">
                      {prod.product_name}
                    </h4>
                  </div>

                  <button
                    onClick={() => toggleAddon(prod.product_id)}
                    disabled={isRecalculatingQuote}
                    className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                      isSelected
                        ? 'bg-red-600 text-white hover:bg-red-700'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {isSelected ? <Minus className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                  </button>
                </div>

                <p className="text-xs text-slate-500 mb-3 line-clamp-2 leading-relaxed">
                  {prod.description}
                </p>

                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-extrabold text-slate-900">
                      ₹{(prod.monthly_price_min ?? (prod as any).price_min_inr_per_month ?? 0).toLocaleString()}
                    </span>
                    {(prod.monthly_price_min ?? (prod as any).price_min_inr_per_month ?? 0) !==
                      (prod.monthly_price_max ?? (prod as any).price_max_inr_per_month ?? 0) && (
                      <span className="text-slate-500">
                        {' '}– ₹{(prod.monthly_price_max ?? (prod as any).price_max_inr_per_month ?? 0).toLocaleString()}
                      </span>
                    )}
                    <span className="text-[10px] text-slate-400">/{prod.pricing_unit ?? (prod as any).unit ?? 'per site'}</span>
                  </div>

                  {prod.requires_gstin && (
                    <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                      GSTIN Required
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom CTA Bar */}
        <div className="mt-8 pt-6 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="text-xs text-slate-500">
            {isRecalculatingQuote ? (
              <span className="flex items-center space-x-1.5 text-red-600 font-semibold">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Recalculating backend quote...</span>
              </span>
            ) : (
              <span>All prices validated by backend PricingEngine with decimal arithmetic.</span>
            )}
          </div>

          <button
            onClick={() => navigate('/quote')}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-bold text-sm rounded-xl shadow-md shadow-red-600/20 hover:shadow-lg transition-all flex items-center justify-center space-x-2"
          >
            <span>Proceed to Quote Review</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
