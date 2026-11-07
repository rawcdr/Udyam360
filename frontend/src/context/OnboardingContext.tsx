import React, { createContext, useContext, useState, useEffect } from 'react';
import { BusinessProfile } from '../types/advisor';
import { RecommendationResponse, RecommendedBundle } from '../types/recommendations';
import { QuotePreviewResponse } from '../types/quote';
import { KYCCaseResponse, KYCValidationResult } from '../types/kyc';
import { OrderResponse } from '../types/order';
import { quoteApi } from '../api/quotes';
import { kycApi } from '../api/kyc';

interface OnboardingContextType {
  conversationId: string | null;
  setConversationId: (id: string | null) => void;
  profile: BusinessProfile;
  setProfile: (profile: BusinessProfile) => void;
  recommendations: RecommendationResponse | null;
  setRecommendations: (rec: RecommendationResponse | null) => void;
  selectedBundleTier: string;
  setSelectedBundleTier: (tier: string) => void;
  selectedProductIds: string[];
  setSelectedProductIds: (ids: string[]) => void;
  quote: QuotePreviewResponse | null;
  setQuote: (q: QuotePreviewResponse | null) => void;
  isRecalculatingQuote: boolean;
  kycCase: KYCCaseResponse | null;
  setKycCase: (k: KYCCaseResponse | null) => void;
  kycValidation: KYCValidationResult | null;
  setKycValidation: (v: KYCValidationResult | null) => void;
  order: OrderResponse | null;
  setOrder: (o: OrderResponse | null) => void;
  selectBundle: (bundle: RecommendedBundle) => Promise<void>;
  toggleAddon: (productId: string) => Promise<void>;
  recalculateQuote: (overrideProductIds?: string[]) => Promise<QuotePreviewResponse | null>;
  resetOnboarding: () => void;
}

const defaultProfile: BusinessProfile = {
  business_name: 'Apollo Care Pharmacy',
  business_type: 'Pharmacy',
  segment: 'micro',
  sites_count: 1,
  num_employees: 4,
  city: 'Bengaluru',
  city_tier: 1,
  gstin_available: true,
  udyam_available: true,
  budget_monthly: 4000,
  requested_services: ['Office Internet', 'Business Calling SIM'],
};

const OnboardingContext = createContext<OnboardingContextType | undefined>(undefined);

export const OnboardingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [conversationId, setConversationId] = useState<string | null>(() => {
    return sessionStorage.getItem('udyam360_conv_id') || null;
  });

  const [profile, setProfileState] = useState<BusinessProfile>(() => {
    const saved = sessionStorage.getItem('udyam360_profile');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return defaultProfile;
      }
    }
    return defaultProfile;
  });

  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [selectedBundleTier, setSelectedBundleTier] = useState<string>('Growth');
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>(['P01', 'P03']);
  const [quote, setQuote] = useState<QuotePreviewResponse | null>(null);
  const [isRecalculatingQuote, setIsRecalculatingQuote] = useState<boolean>(false);
  const [kycCase, setKycCase] = useState<KYCCaseResponse | null>(null);
  const [kycValidation, setKycValidation] = useState<KYCValidationResult | null>(null);
  const [order, setOrder] = useState<OrderResponse | null>(null);

  useEffect(() => {
    if (conversationId) {
      sessionStorage.setItem('udyam360_conv_id', conversationId);
    } else {
      sessionStorage.removeItem('udyam360_conv_id');
    }
  }, [conversationId]);

  const normalizeProfile = (p: BusinessProfile): BusinessProfile => {
    const employeeCount = p.employee_count ?? p.num_employees ?? null;
    const budgetMonthly = p.monthly_budget_inr ?? p.budget_monthly ?? null;
    const hasGstin = p.has_gstin ?? p.gstin_available ?? true;
    const hasUdyam = p.has_udyam ?? p.udyam_available ?? true;
    const numSites = p.num_sites ?? p.sites_count ?? 1;
    const segment = p.business_segment ?? p.segment ?? null;

    return {
      ...p,
      employee_count: employeeCount,
      num_employees: employeeCount,
      monthly_budget_inr: budgetMonthly,
      budget_monthly: budgetMonthly,
      has_gstin: hasGstin,
      gstin_available: hasGstin,
      has_udyam: hasUdyam,
      udyam_available: hasUdyam,
      num_sites: numSites,
      sites_count: numSites,
      business_segment: segment,
      segment: segment,
    };
  };

  const setProfile = (newProfile: BusinessProfile) => {
    const normalized = normalizeProfile(newProfile);
    setProfileState(normalized);
    sessionStorage.setItem('udyam360_profile', JSON.stringify(normalized));
  };

  const recalculateQuote = async (overrideProductIds?: string[]): Promise<QuotePreviewResponse | null> => {
    const productIds = overrideProductIds || selectedProductIds;
    if (productIds.length === 0) return null;

    setIsRecalculatingQuote(true);
    try {
      const q = await quoteApi.previewQuote({
        profile,
        selected_product_ids: productIds,
        bundle_tier: selectedBundleTier,
      });
      setQuote(q);
      return q;
    } catch (err) {
      console.error('Failed to recalculate quote:', err);
      return null;
    } finally {
      setIsRecalculatingQuote(false);
    }
  };

  const selectBundle = async (bundle: RecommendedBundle) => {
    setSelectedBundleTier(bundle.bundle_tier);
    setSelectedProductIds(bundle.product_ids);
    setIsRecalculatingQuote(true);
    try {
      const q = await quoteApi.previewQuote({
        profile,
        selected_product_ids: bundle.product_ids,
        bundle_tier: bundle.bundle_tier,
      });
      setQuote(q);
    } catch (err) {
      console.error('Failed to quote selected bundle:', err);
    } finally {
      setIsRecalculatingQuote(false);
    }
  };

  const toggleAddon = async (productId: string) => {
    let nextIds: string[];
    if (selectedProductIds.includes(productId)) {
      nextIds = selectedProductIds.filter((id) => id !== productId);
    } else {
      nextIds = [...selectedProductIds, productId];
    }
    setSelectedProductIds(nextIds);
    await recalculateQuote(nextIds);
  };

  const resetOnboarding = () => {
    setConversationId(null);
    setProfile(defaultProfile);
    setRecommendations(null);
    setSelectedBundleTier('Growth');
    setSelectedProductIds(['P01', 'P03']);
    setQuote(null);
    setKycCase(null);
    setKycValidation(null);
    setOrder(null);
    sessionStorage.removeItem('udyam360_conv_id');
    sessionStorage.removeItem('udyam360_profile');
    sessionStorage.removeItem('udyam360_session_token');
  };

  return (
    <OnboardingContext.Provider
      value={{
        conversationId,
        setConversationId,
        profile,
        setProfile,
        recommendations,
        setRecommendations,
        selectedBundleTier,
        setSelectedBundleTier,
        selectedProductIds,
        setSelectedProductIds,
        quote,
        setQuote,
        isRecalculatingQuote,
        kycCase,
        setKycCase,
        kycValidation,
        setKycValidation,
        order,
        setOrder,
        selectBundle,
        toggleAddon,
        recalculateQuote,
        resetOnboarding,
      }}
    >
      {children}
    </OnboardingContext.Provider>
  );
};

export const useOnboarding = () => {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error('useOnboarding must be used within an OnboardingProvider');
  }
  return context;
};
