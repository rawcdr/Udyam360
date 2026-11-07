import React, { useState, useEffect } from 'react';
import {
  adminApi,
  KYCExceptionCase,
  KYCExceptionResolution,
} from '../../api/admin';
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Building2,
  FileCheck2,
  Clock,
  Sparkles,
  ArrowRight,
  ExternalLink,
  RotateCw,
  Search,
  Check,
  Info,
  Loader2,
  UserCheck,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const AdminKYCExceptionsPage: React.FC = () => {
  const [exceptions, setExceptions] = useState<KYCExceptionCase[]>([]);
  const [selectedCase, setSelectedCase] = useState<KYCExceptionCase | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isResolving, setIsResolving] = useState<boolean>(false);
  const [resolutionSuccess, setResolutionSuccess] = useState<KYCExceptionResolution | null>(null);
  const [officerNotes, setOfficerNotes] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchExceptions = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await adminApi.getKYCExceptions(statusFilter);
      setExceptions(data);
      if (data.length > 0 && (!selectedCase || !data.some((c) => c.case_id === selectedCase.case_id))) {
        setSelectedCase(data[0]);
        setOfficerNotes(
          'Approved following AI Copilot cross-check. Trade name matches GSTIN principal place; signatory verified.'
        );
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load KYC exceptions queue.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchExceptions();
  }, [statusFilter]);

  const handleSelectCase = (c: KYCExceptionCase) => {
    setSelectedCase(c);
    setResolutionSuccess(null);
    setOfficerNotes(
      c.status === 'APPROVED'
        ? c.review_notes || 'Approved exception override.'
        : 'Approved following AI Copilot cross-check. Trade name matches GSTIN principal place; signatory verified.'
    );
  };

  const handleResolve = async (action: 'APPROVE' | 'REJECT' | 'REQUEST_REUPLOAD') => {
    if (!selectedCase) return;
    setIsResolving(true);
    setErrorMessage(null);
    try {
      const res = await adminApi.resolveKYCException(
        selectedCase.case_id,
        action,
        officerNotes || `${action} by KYC Operations Officer.`
      );
      setResolutionSuccess(res);
      // Update in-memory state
      setExceptions((prev) =>
        prev.map((item) =>
          item.case_id === selectedCase.case_id
            ? {
                ...item,
                status: res.status as any,
                reviewed_at: res.reviewed_at,
                reviewed_by: res.reviewed_by,
                review_notes: res.notes,
              }
            : item
        )
      );
      setSelectedCase((prev) =>
        prev
          ? {
              ...prev,
              status: res.status as any,
              reviewed_at: res.reviewed_at,
              reviewed_by: res.reviewed_by,
              review_notes: res.notes,
            }
          : null
      );
    } catch (err: any) {
      setErrorMessage(err.message || 'Error resolving KYC exception.');
    } finally {
      setIsResolving(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Approved</span>
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300">
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>Rejected</span>
          </span>
        );
      case 'INFO_REQUESTED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
            <Clock className="w-3.5 h-3.5 text-amber-600" />
            <span>Clarification Sent</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-300 animate-pulse">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Pending Review</span>
          </span>
        );
    }
  };

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'LOW':
        return (
          <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
            Low Risk
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 border border-amber-200">
            Medium Risk
          </span>
        );
      default:
        return (
          <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-rose-50 text-rose-700 border border-rose-200">
            High Risk
          </span>
        );
    }
  };

  const getCrossCheckIcon = (checkStatus: string) => {
    switch (checkStatus) {
      case 'MATCH':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />;
      case 'MINOR_VARIATION':
        return <Info className="w-4 h-4 text-amber-500 shrink-0" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* KPI Headline Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs">
          <p className="text-xs font-medium text-slate-500">Pending Exceptions</p>
          <div className="flex items-baseline space-x-2 mt-1">
            <span className="text-2xl font-black text-slate-900">
              {exceptions.filter((e) => e.status === 'PENDING_REVIEW').length}
            </span>
            <span className="text-xs text-amber-600 font-semibold">Active Queue</span>
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs">
          <p className="text-xs font-medium text-slate-500">Sole Proprietorship Matches</p>
          <div className="flex items-baseline space-x-2 mt-1">
            <span className="text-2xl font-black text-slate-900">67%</span>
            <span className="text-xs text-emerald-600 font-semibold">Standard Trade Name</span>
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs">
          <p className="text-xs font-medium text-slate-500">Avg Resolution SLA</p>
          <div className="flex items-baseline space-x-2 mt-1">
            <span className="text-2xl font-black text-slate-900">45 Sec</span>
            <span className="text-xs text-emerald-600 font-semibold">vs 7 Days Manual</span>
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs">
          <p className="text-xs font-medium text-slate-500">Auto Order Advancement</p>
          <div className="flex items-baseline space-x-2 mt-1">
            <span className="text-2xl font-black text-emerald-600">100%</span>
            <span className="text-xs text-slate-500 font-medium">To Provisioning</span>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Status:</span>
          {['ALL', 'PENDING_REVIEW', 'APPROVED', 'INFO_REQUESTED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                statusFilter === st
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {st === 'ALL' ? 'All Exceptions' : st.replace('_', ' ')}
            </button>
          ))}
        </div>

        <button
          onClick={fetchExceptions}
          disabled={isLoading}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
        >
          <RotateCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-red-500" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Split-Screen Workdesk */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Exceptions Queue (5 cols) */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Exceptions Review Queue</h2>
              <p className="text-[11px] text-slate-500">Cases requiring officer verification</p>
            </div>
            <span className="text-xs font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
              {exceptions.length} Cases
            </span>
          </div>

          <div className="divide-y divide-slate-100 max-h-[620px] overflow-y-auto">
            {exceptions.map((c) => {
              const isSelected = selectedCase?.case_id === c.case_id;
              return (
                <div
                  key={c.case_id}
                  onClick={() => handleSelectCase(c)}
                  className={`p-4 cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-red-50/50 border-l-4 border-red-600'
                      : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono font-bold text-slate-600">{c.case_id}</span>
                    {getStatusBadge(c.status)}
                  </div>

                  <h3 className="text-sm font-extrabold text-slate-900">{c.business_name}</h3>
                  <p className="text-xs text-slate-500 mt-0.5 flex items-center space-x-1">
                    <UserCheck className="w-3.5 h-3.5 text-slate-400" />
                    <span>{c.customer_name}</span>
                    <span className="text-slate-300">•</span>
                    <span>{c.city}</span>
                  </p>

                  <div className="mt-2.5 p-2 rounded-lg bg-slate-50 border border-slate-200/80 text-[11px] text-slate-600">
                    <span className="font-semibold text-slate-700">Flag Reason: </span>
                    {c.flag_reason}
                  </div>

                  <div className="mt-2.5 flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-1.5">
                      {getRiskBadge(c.risk_level)}
                      <span className="text-[11px] font-semibold text-slate-500">
                        Match Score: <strong className="text-slate-800">{c.confidence_score}%</strong>
                      </span>
                    </div>
                    {c.order_reference && (
                      <span className="text-[10px] font-mono text-slate-400">
                        {c.order_reference.slice(0, 14)}...
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: AI KYC Copilot & Cross-Check Dossier (7 cols) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-6">
          {selectedCase ? (
            <>
              {/* Case Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-lg font-black text-slate-900">{selectedCase.business_name}</h2>
                    {getStatusBadge(selectedCase.status)}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Case: <strong className="font-mono text-slate-700">{selectedCase.case_id}</strong> • Segment:{' '}
                    <strong className="text-slate-700">{selectedCase.segment}</strong>
                  </p>
                </div>

                {selectedCase.order_reference && (
                  <Link
                    to={`/track-order?ref=${selectedCase.order_reference}`}
                    className="inline-flex items-center space-x-1 px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
                  >
                    <span>View Order Track</span>
                    <ExternalLink className="w-3 h-3 text-slate-500" />
                  </Link>
                )}
              </div>

              {/* Success Notification Banner after Resolution */}
              {resolutionSuccess && (
                <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-300 text-emerald-900 text-xs flex items-start space-x-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold">
                      Case {resolutionSuccess.case_id} Successfully {resolutionSuccess.action_taken}!
                    </p>
                    <p className="text-emerald-700 mt-0.5">
                      Order {resolutionSuccess.order_reference} transitioned to{' '}
                      <strong>{resolutionSuccess.order_status}</strong>. Customer notification queued via Airtel IQ.
                    </p>
                    <p className="text-[11px] text-emerald-600 mt-1">
                      Audit Record logged by {resolutionSuccess.reviewed_by} at{' '}
                      {new Date(resolutionSuccess.reviewed_at).toLocaleTimeString()}.
                    </p>
                  </div>
                </div>
              )}

              {/* AI Copilot Risk Analysis Card */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-red-50/70 to-rose-50/60 border border-red-200">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-6 h-6 rounded-md bg-red-600 text-white flex items-center justify-center">
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                  <h3 className="text-xs font-bold text-red-900 uppercase tracking-wide">
                    Airtel AI KYC Copilot Risk Intelligence
                  </h3>
                  <span className="ml-auto text-xs font-extrabold text-emerald-700 bg-white px-2 py-0.5 rounded border border-emerald-300">
                    Confidence: {selectedCase.confidence_score}%
                  </span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed font-normal">
                  {selectedCase.copilot_analysis}
                </p>
                <div className="mt-3 pt-2.5 border-t border-red-200/60 flex items-center space-x-2">
                  <span className="text-[11px] font-bold text-red-800">Copilot Directive:</span>
                  <span className="text-xs font-bold text-slate-900 bg-white px-2 py-1 rounded-md border border-slate-200 shadow-2xs">
                    {selectedCase.copilot_recommendation}
                  </span>
                </div>
              </div>

              {/* Entity Structure Details */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2.5">
                  Business Entity Identification
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-slate-500 block text-[11px]">Trade Name:</span>
                    <span className="font-bold text-slate-900">{selectedCase.trade_name}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[11px]">Legal Entity Name:</span>
                    <span className="font-bold text-slate-900">{selectedCase.legal_name}</span>
                  </div>
                  <div className="sm:col-span-2">
                    <span className="text-slate-500 block text-[11px]">Structure & Registrations:</span>
                    <span className="font-semibold text-slate-800">{selectedCase.entity_structure}</span>
                  </div>
                </div>
              </div>

              {/* Registry Cross-Checks Matrix */}
              <div>
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
                  Government Registry Cross-Checks (Local Air-Gapped OCR)
                </h4>
                <div className="space-y-2.5">
                  {selectedCase.cross_checks.map((check, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-white rounded-xl border border-slate-200 flex items-start space-x-3 text-xs"
                    >
                      {getCrossCheckIcon(check.status)}
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-0.5">
                          <span className="font-bold text-slate-900">{check.check_name}</span>
                          <span
                            className={`text-[10px] font-extrabold uppercase px-1.5 py-0.5 rounded ${
                              check.status === 'MATCH'
                                ? 'bg-emerald-100 text-emerald-800'
                                : check.status === 'MINOR_VARIATION'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {check.status.replace('_', ' ')}
                          </span>
                        </div>
                        <p className="text-slate-600 leading-normal">{check.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Compliance Officer Decision Studio */}
              <div className="p-5 rounded-2xl bg-slate-900 text-white space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-white">KYC Officer Decision Console</h4>
                    <p className="text-xs text-slate-400">
                      Authoritative resolution will update customer order pipeline and append audit trail.
                    </p>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">Role: ExecutiveAdmin / KYCOfficer</span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Regulatory Audit Note (Immutable Log Entry):
                  </label>
                  <textarea
                    rows={2}
                    value={officerNotes}
                    onChange={(e) => setOfficerNotes(e.target.value)}
                    disabled={isResolving}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-hidden focus:ring-2 focus:ring-red-500"
                    placeholder="Enter compliance rationale..."
                  />
                </div>

                <div className="flex flex-wrap items-center gap-3 pt-1">
                  <button
                    onClick={() => handleResolve('APPROVE')}
                    disabled={isResolving || selectedCase.status === 'APPROVED'}
                    className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-xs transition-colors flex items-center space-x-1.5"
                  >
                    {isResolving ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4" />
                    )}
                    <span>
                      {selectedCase.status === 'APPROVED'
                        ? 'Exception Approved'
                        : 'Approve & Release Order'}
                    </span>
                  </button>

                  <button
                    onClick={() => handleResolve('REQUEST_REUPLOAD')}
                    disabled={isResolving}
                    className="px-4 py-2.5 bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-xs transition-colors flex items-center space-x-1.5"
                  >
                    <Clock className="w-4 h-4" />
                    <span>Request Re-upload</span>
                  </button>

                  <button
                    onClick={() => handleResolve('REJECT')}
                    disabled={isResolving || selectedCase.status === 'REJECTED'}
                    className="px-4 py-2.5 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-xs transition-colors flex items-center space-x-1.5"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject Case</span>
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-16 text-slate-500">
              <p>Select an exception case from the queue to view dossier.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

