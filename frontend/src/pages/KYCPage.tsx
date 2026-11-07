import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useOnboarding } from '../context/OnboardingContext';
import { useAuth } from '../context/AuthContext';
import { CustomerAuthModal } from '../components/auth/CustomerAuthModal';
import { kycApi } from '../api/kyc';
import { orderApi } from '../api/orders';
import { DocumentType, KYCDocumentMetadata, KYCValidationResult } from '../types/kyc';
import {
  ShieldCheck,
  ShieldAlert,
  FileUp,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  XCircle,
  Clock,
  ArrowRight,
  FileText,
  Lock,
  Eye,
  Check,
  HelpCircle,
  FileSpreadsheet,
  Building,
  Loader2,
  Trash2,
} from 'lucide-react';

export const KYCPage: React.FC = () => {
  const navigate = useNavigate();
  const { customer, isCustomerAuthenticated } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState<boolean>(false);
  const {
    profile,
    selectedProductIds,
    quote,
    conversationId,
    kycCase,
    setKycCase,
    kycValidation,
    setKycValidation,
    setOrder,
  } = useOnboarding();

  // Consent State (Must NOT be pre-checked!)
  const [consentGranted, setConsentGranted] = useState<boolean>(false);
  const [consentRecorded, setConsentRecorded] = useState<boolean>(false);

  // Uploaded Documents
  const [uploadedDocs, setUploadedDocs] = useState<KYCDocumentMetadata[]>([]);
  const [isUploading, setIsUploading] = useState<Record<string, boolean>>({});
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [isPlacingOrder, setIsPlacingOrder] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Initialize or fetch KYC case
  useEffect(() => {
    const initOrLoadCase = async () => {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const urlCaseId = urlParams.get('case');

        if (urlCaseId) {
          const loadedCase = await kycApi.getCase(urlCaseId);
          setKycCase(loadedCase);
          setConsentRecorded(loadedCase.consent_recorded);
          setConsentGranted(loadedCase.consent_recorded);
          const docs = await kycApi.listDocuments(urlCaseId);
          setUploadedDocs(docs);
          try {
            const val = await kycApi.getValidationDetails(urlCaseId);
            setKycValidation(val);
          } catch {
            // Processing not yet run
          }
          return;
        }

        if (!kycCase) {
          const newCase = await kycApi.createCase({
            advisor_session_id: conversationId || 'conv_default_guest',
            selected_product_ids: selectedProductIds,
            quote_reference: quote?.quote_id || 'Q-SAMPLE',
          });
          setKycCase(newCase);
        } else {
          // Refresh document list
          const docs = await kycApi.listDocuments(kycCase.kyc_case_id);
          setUploadedDocs(docs);
        }
      } catch (err: any) {
        setErrorMessage('Failed to initialize KYC case: ' + err.message);
      }
    };

    initOrLoadCase();
  }, [kycCase]);

  const handleGrantConsent = async () => {
    if (!isCustomerAuthenticated) {
      setShowAuthModal(true);
      return;
    }
    if (!kycCase || !consentGranted) return;
    try {
      await kycApi.recordConsent(kycCase.kyc_case_id, true);
      setConsentRecorded(true);
      setErrorMessage(null);
    } catch (err: any) {
      setErrorMessage('Could not record consent: ' + err.message);
    }
  };

  const handleFileUpload = async (docType: DocumentType, file: File) => {
    if (!isCustomerAuthenticated) {
      setShowAuthModal(true);
      return;
    }
    if (!kycCase) return;
    setIsUploading((prev) => ({ ...prev, [docType]: true }));
    setErrorMessage(null);
    try {
      const uploaded = await kycApi.uploadDocument(kycCase.kyc_case_id, docType, file);
      setUploadedDocs((prev) => [...prev.filter((d) => d.document_type !== docType), uploaded]);
    } catch (err: any) {
      setErrorMessage(`Upload failed for ${docType}: ${err.message}`);
    } finally {
      setIsUploading((prev) => ({ ...prev, [docType]: false }));
    }
  };

  const handleProcessKYC = async () => {
    if (!kycCase) return;
    setIsProcessing(true);
    setErrorMessage(null);
    try {
      const result = await kycApi.processKYC(kycCase.kyc_case_id);
      setKycValidation(result);
    } catch (err: any) {
      setErrorMessage('KYC verification failed: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirmAndPlaceOrder = async () => {
    if (!quote || !kycCase) return;
    setIsPlacingOrder(true);
    setErrorMessage(null);
    try {
      const newOrder = await orderApi.create({
        advisor_session_id: conversationId,
        quote_reference: quote.quote_id,
        kyc_case_id: kycCase.kyc_case_id,
        selected_product_ids: selectedProductIds,
        bundle_tier: quote.bundle_tier,
        customer_info: {
          business_name: profile.business_name || 'Apex Business Solutions',
          city: profile.city || 'Bengaluru',
          segment: quote.business_segment,
        },
        pricing: {
          currency: 'INR',
          monthly_recurring_charges: quote.pricing.monthly_total_min ?? (quote.pricing as any).monthly_recurring_charges ?? 0,
          one_time_charges: quote.pricing.setup_total_min ?? (quote.pricing as any).one_time_charges ?? 0,
          estimated_first_month: quote.pricing.estimated_first_month_min ?? (quote.pricing as any).estimated_first_month_payable ?? 0,
        },
      });

      // If order is not yet at KYC_VERIFIED and KYC is verified, advance it
      let finalOrder = newOrder;
      if (finalOrder.current_state === 'QUOTE_CONFIRMED' && kycValidation && kycValidation.overall_status === 'VERIFIED') {
        await orderApi.advance(finalOrder.order_id); // to KYC_PENDING
        await orderApi.advance(finalOrder.order_id); // to KYC_VERIFICATION
        finalOrder = await orderApi.advance(finalOrder.order_id); // to KYC_VERIFIED
      }

      setOrder(finalOrder);
      navigate(`/track-order?ref=${finalOrder.order_reference}`);
    } catch (err: any) {
      setErrorMessage('Failed to place order: ' + err.message);
    } finally {
      setIsPlacingOrder(false);
    }
  };

  // Helper labels for document types
  const getDocTypeLabel = (docType: DocumentType) => {
    const labels: Record<string, { title: string; desc: string }> = {
      GST_CERTIFICATE: {
        title: 'GST Registration Certificate (Form REG-06)',
        desc: 'Official GSTIN registration containing principal place of business.',
      },
      UDYAM_CERTIFICATE: {
        title: 'Udyam Registration Certificate',
        desc: 'MSME registration certificate issued by Ministry of MSME.',
      },
      ADDRESS_PROOF: {
        title: 'Commercial Address Proof / Utility Bill',
        desc: 'Electricity bill, property tax receipt, or lease agreement within 90 days.',
      },
      SIGNATORY_ID: {
        title: 'Authorized Signatory Identity Document',
        desc: 'PAN card or Aadhaar copy of proprietor / director.',
      },
      TRADE_LICENSE: {
        title: 'Municipal Trade License',
        desc: 'Valid municipal corporation business permit.',
      },
      OTHER: {
        title: 'Supporting Business Document',
        desc: 'Additional identity verification document.',
      },
    };
    return labels[docType] || { title: docType, desc: 'Required compliance document.' };
  };

  // Ensure standard MSME compliance documents (including GST Certificate) are always uploadable
  const backendDocs: DocumentType[] = kycCase?.required_document_types || [];
  const requiredDocTypes: DocumentType[] = backendDocs.length > 0
    ? (backendDocs.includes('GST_CERTIFICATE') ? backendDocs : ['GST_CERTIFICATE', ...backendDocs])
    : ['GST_CERTIFICATE', 'ADDRESS_PROOF', 'SIGNATORY_ID', 'UDYAM_CERTIFICATE'];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Title Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Smart KYC & Document Verification
            </h1>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
              100% Local OCR
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Privacy-first business identity verification using local OCR and mock government registries.
          </p>
        </div>

        {kycCase && (
          <div className="bg-slate-100 rounded-xl p-3 border border-slate-200 text-right">
            <p className="text-[10px] font-bold uppercase text-slate-500">KYC Case Reference</p>
            <p className="text-sm font-mono font-extrabold text-slate-900">{kycCase.kyc_case_id}</p>
            <p className="text-[10px] text-slate-400">Quote: {quote?.quote_id || 'Active'}</p>
          </div>
        )}
      </div>

      {errorMessage && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Customer Identity Verification Banner */}
      {isCustomerAuthenticated ? (
        <div className="bg-emerald-50/80 border border-emerald-200 rounded-2xl p-4 sm:p-5 mb-8 flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold shadow-sm shadow-emerald-600/30">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-bold text-emerald-950">Verified MSME Customer</span>
                <span className="text-[10px] bg-emerald-200/80 text-emerald-900 font-bold px-2 py-0.5 rounded-full">
                  Authenticated Session
                </span>
              </div>
              <p className="text-xs text-emerald-700 mt-0.5">
                Mobile: <span className="font-mono font-semibold">{customer?.phone_number}</span> &bull; Account ID: {customer?.customer_id}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setShowAuthModal(true)}
            className="text-xs font-semibold text-emerald-800 hover:text-emerald-950 underline px-3 py-1.5"
          >
            Switch Account
          </button>
        </div>
      ) : (
        <div className="bg-amber-50/90 border border-amber-200 rounded-2xl p-4 sm:p-5 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-amber-500 text-white flex items-center justify-center font-bold shadow-sm shadow-amber-500/30">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-bold text-amber-950">Customer Mobile Verification Required</span>
                <span className="text-[10px] bg-amber-200 text-amber-900 font-bold px-2 py-0.5 rounded-full">
                  DPDP Protected
                </span>
              </div>
              <p className="text-xs text-amber-800 mt-0.5">
                To safeguard registration credentials and link onboarding to your business, please verify your mobile number.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setShowAuthModal(true)}
            className="px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl shadow-md transition-colors whitespace-nowrap"
          >
            Verify Mobile Number (OTP)
          </button>
        </div>
      )}

      {/* STEP 1: EXPLICIT CONSENT GATE */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs mb-8">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Step 1: Data Privacy & Customer Processing Consent
            </h2>
            <p className="text-xs text-slate-500">Mandatory consent required before processing any uploaded files.</p>
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl p-4 text-xs text-slate-600 space-y-2 border border-slate-200/80 mb-5">
          <p className="font-semibold text-slate-800">Please review our privacy commitments:</p>
          <ul className="list-disc list-inside space-y-1 text-slate-600">
            <li>
              <strong>Zero GenAI Leakage:</strong> Document images, OCR text, and business identification numbers are processed strictly on local servers. Nothing is transmitted to external LLMs.
            </li>
            <li>
              <strong>Mock Registry Validation:</strong> In accordance with the Airtel SYNC hackathon prototype environment, records are cross-checked against local synthetic GSTIN and Udyam databases.
            </li>
            <li>
              <strong>Consent Withdrawal:</strong> You may cancel this onboarding session at any time to purge uploaded specimen files.
            </li>
          </ul>
        </div>

        <div className="flex items-start space-x-3 p-3 bg-red-50/50 rounded-xl border border-red-200/60 mb-4">
          <input
            id="kyc-consent-checkbox"
            type="checkbox"
            checked={consentGranted}
            onChange={(e) => setConsentGranted(e.target.checked)}
            className="w-4 h-4 text-red-600 rounded border-slate-300 focus:ring-red-500 mt-0.5 cursor-pointer"
          />
          <label htmlFor="kyc-consent-checkbox" className="text-xs text-slate-800 font-medium cursor-pointer">
            I hereby grant explicit consent to Udyam360 to process our submitted documents through local OCR and registry verification for commercial onboarding.
          </label>
        </div>

        {!consentRecorded ? (
          <button
            onClick={handleGrantConsent}
            disabled={!consentGranted}
            className="px-5 py-2.5 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold rounded-xl text-xs shadow-xs transition-all flex items-center space-x-1.5"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Grant & Record Consent</span>
          </button>
        ) : (
          <div className="inline-flex items-center space-x-2 text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
            <Check className="w-4 h-4 text-emerald-600" />
            <span>Consent Confirmed & Audited</span>
          </div>
        )}
      </div>

      {/* STEP 2: DYNAMIC DOCUMENT UPLOADS */}
      <div
        className={`bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs mb-8 transition-opacity ${
          !consentRecorded ? 'opacity-50 pointer-events-none' : ''
        }`}
      >
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
              <FileUp className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Step 2: Upload Dynamic Required Documents
              </h2>
              <p className="text-xs text-slate-500">
                Backend calculated requirements for your selected services and business segment.
              </p>
            </div>
          </div>

          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700">
            {uploadedDocs.length} of {requiredDocTypes.length} Uploaded
          </span>
        </div>

        {/* Dynamic Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {requiredDocTypes.map((docType) => {
            const { title, desc } = getDocTypeLabel(docType);
            const uploadedMeta = uploadedDocs.find((d) => d.document_type === docType);
            const uploading = isUploading[docType];

            return (
              <div
                key={docType}
                className={`p-5 rounded-2xl border transition-all ${
                  uploadedMeta
                    ? 'border-emerald-300 bg-emerald-50/20 shadow-2xs'
                    : 'border-slate-200 bg-slate-50/50 hover:border-slate-300'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="space-y-0.5">
                    <span className="text-[10px] font-bold font-mono px-1.5 py-0.5 rounded bg-slate-200 text-slate-600">
                      {docType}
                    </span>
                    <h3 className="font-bold text-slate-900 text-sm mt-1">{title}</h3>
                  </div>

                  {uploadedMeta ? (
                    <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center">
                      <Check className="w-3.5 h-3.5" />
                    </span>
                  ) : (
                    <span className="text-xs text-slate-400 font-medium">Pending</span>
                  )}
                </div>

                <p className="text-xs text-slate-500 mb-4">{desc}</p>

                {uploadedMeta ? (
                  <div className="p-2.5 bg-white rounded-xl border border-emerald-200 flex items-center justify-between text-xs">
                    <div className="truncate pr-2">
                      <p className="font-bold text-slate-800 truncate">{uploadedMeta.original_filename}</p>
                      <p className="text-[10px] text-slate-400">
                        {(uploadedMeta.file_size_bytes / 1024).toFixed(1)} KB • {uploadedMeta.mime_type}
                      </p>
                    </div>
                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                      Uploaded
                    </span>
                  </div>
                ) : (
                  <div>
                    <label className="w-full flex items-center justify-center space-x-2 py-2.5 px-3 bg-white hover:bg-slate-100 border border-slate-300 border-dashed rounded-xl cursor-pointer text-xs font-semibold text-slate-700 transition-colors">
                      {uploading ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-red-600" />
                          <span>Uploading...</span>
                        </>
                      ) : (
                        <>
                          <FileUp className="w-3.5 h-3.5 text-slate-500" />
                          <span>Select or Drop File (PNG, JPG, PDF)</span>
                        </>
                      )}
                      <input
                        type="file"
                        accept="image/png,image/jpeg,application/pdf"
                        disabled={uploading}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) handleFileUpload(docType, file);
                        }}
                        className="hidden"
                      />
                    </label>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Verification Trigger Button */}
        <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <p className="text-xs text-slate-500">
            Note: Uploaded documents are not considered verified until local OCR and registry checking completes.
          </p>

          <button
            onClick={handleProcessKYC}
            disabled={uploadedDocs.length === 0 || isProcessing}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-md shadow-red-600/20 transition-all flex items-center justify-center space-x-2"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Running Local OCR Pipeline...</span>
              </>
            ) : (
              <>
                <ShieldCheck className="w-4 h-4" />
                <span>Verify Documents & Cross-Check Registries</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* STEP 3: EXPLAINABLE KYC VERIFICATION RESULTS */}
      {kycValidation && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-card mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-slate-900">Verification Outcome Report</h2>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase ${
                    kycValidation.overall_status === 'VERIFIED'
                      ? 'bg-emerald-100 text-emerald-800'
                      : kycValidation.overall_status === 'PENDING_REVIEW'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  {kycValidation.overall_status}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">{kycValidation.explanation}</p>
            </div>

            <p className="text-[11px] text-slate-400 font-mono">
              Processed: {new Date().toLocaleTimeString()}
            </p>
          </div>

          {/* Verification Checks Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 text-xs">
            {/* Passed Checks */}
            <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200">
              <h3 className="font-bold text-emerald-900 mb-2.5 flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Passed Verification Checks ({kycValidation.checks_passed.length})</span>
              </h3>
              <ul className="space-y-1.5">
                {kycValidation.checks_passed.map((chk: any, i) => (
                  <li key={i} className="text-emerald-800 flex items-start space-x-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" />
                    <span>
                      <strong>{chk.check_name}:</strong> {chk.message || (typeof chk.details === 'string' ? chk.details : 'Verified')}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Warnings or Reviews */}
            <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200">
              <h3 className="font-bold text-amber-900 mb-2.5 flex items-center space-x-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Compliance Flags & Advisories</span>
              </h3>
              {kycValidation.warnings.length > 0 || kycValidation.review_reasons.length > 0 ? (
                <ul className="space-y-1.5 text-amber-800">
                  {kycValidation.review_reasons.map((r, i) => (
                    <li key={i}>• {r}</li>
                  ))}
                  {kycValidation.warnings.map((w: any, i) => (
                    <li key={i}>• {w.message || (typeof w === 'string' ? w : JSON.stringify(w))}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-emerald-700 italic">Zero compliance flags or document warnings detected.</p>
              )}
            </div>
          </div>

          {/* Final Action to Place Order */}
          <div className="pt-6 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <p className="text-xs font-bold text-slate-800">Ready to activate your business order?</p>
              <p className="text-[11px] text-slate-500">
                Generates your unique tracking reference and initializes fulfillment.
              </p>
            </div>

            <button
              onClick={handleConfirmAndPlaceOrder}
              disabled={isPlacingOrder}
              className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center space-x-2"
            >
              {isPlacingOrder ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Submitting Order...</span>
                </>
              ) : (
                <>
                  <span>Place Order & Track Activation</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Customer Mobile OTP Verification Modal */}
      <CustomerAuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onSuccess={() => {
          setShowAuthModal(false);
          setErrorMessage(null);
        }}
        advisorSessionId={conversationId || undefined}
      />
    </div>
  );
};
