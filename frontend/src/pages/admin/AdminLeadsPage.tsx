import React, { useEffect, useState } from 'react';
import {
  adminApi,
  ScoredLead,
  PropensityOverview,
  LeadDetail,
} from '../../api/admin';
import {
  Search,
  Filter,
  ArrowUpDown,
  Flame,
  AlertCircle,
  CheckCircle,
  PhoneCall,
  UserCheck,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  X,
  Send,
  Building,
  MapPin,
  TrendingUp,
  Sparkles,
} from 'lucide-react';

export const AdminLeadsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [leads, setLeads] = useState<ScoredLead[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Filter States
  const [search, setSearch] = useState('');
  const [segment, setSegment] = useState('All');
  const [stage, setStage] = useState('All');
  const [band, setBand] = useState('All');
  const [unconvertedOnly, setUnconvertedOnly] = useState(true);
  const [sortBy, setSortBy] = useState('propensity_score');
  const [sortOrder, setSortOrder] = useState('desc');

  // Propensity Overview Stats
  const [overview, setOverview] = useState<PropensityOverview | null>(null);

  // Selected Lead for Detail Modal
  const [selectedLead, setSelectedLead] = useState<LeadDetail | null>(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [actionType, setActionType] = useState('Phone Call');
  const [actionNotes, setActionNotes] = useState('');
  const [repName, setRepName] = useState('Airtel Enterprise Sales Rep');
  const [actionSubmitting, setActionSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState(false);

  const fetchOverview = async () => {
    try {
      const res = await adminApi.getPropensityOverview();
      setOverview(res);
    } catch (e) {
      console.error('Failed to load propensity overview:', e);
    }
  };

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getLeads({
        search: search || undefined,
        segment: segment !== 'All' ? segment : undefined,
        stage: stage !== 'All' ? stage : undefined,
        band: band !== 'All' ? band : undefined,
        unconverted_only: unconvertedOnly,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: pageSize,
      });
      setLeads(res.leads);
      setTotalCount(res.total_count);
      setTotalPages(res.total_pages);
    } catch (e) {
      console.error('Failed to load leads table:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  useEffect(() => {
    fetchLeads();
  }, [page, segment, stage, band, unconvertedOnly, sortBy, sortOrder]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchLeads();
  };

  const handleOpenLead = async (leadId: string) => {
    setModalLoading(true);
    setSelectedLead(null);
    setActionSuccess(false);
    try {
      const detail = await adminApi.getLeadDetail(leadId);
      setSelectedLead(detail);
    } catch (e) {
      console.error('Failed to load lead details:', e);
    } finally {
      setModalLoading(false);
    }
  };

  const handleLogAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLead || !actionNotes.trim()) return;
    setActionSubmitting(true);
    try {
      const actionRes = await adminApi.recordSalesAction(
        selectedLead.lead_id,
        actionType,
        actionNotes,
        repName
      );
      // Append to local state
      setSelectedLead({
        ...selectedLead,
        sales_action_history: [...(selectedLead.sales_action_history || []), actionRes],
      });
      setActionNotes('');
      setActionSuccess(true);
      setTimeout(() => setActionSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to record action note:', err);
    } finally {
      setActionSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Propensity Band Headline Cards */}
      {overview && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-xs font-bold text-slate-500 uppercase">Unconverted Pipeline</div>
            <div className="text-2xl font-extrabold text-slate-900 mt-1">
              {overview.total_unconverted_leads.toLocaleString()}
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">Accounts pending activation</p>
          </div>

          <div className="bg-emerald-50/70 p-4 rounded-xl border border-emerald-200 shadow-sm">
            <div className="flex items-center justify-between text-xs font-bold text-emerald-800 uppercase">
              <span>High Propensity (&ge;70%)</span>
              <Flame className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-extrabold text-emerald-700 mt-1">
              {overview.high_propensity_count.toLocaleString()}
            </div>
            <p className="text-[11px] text-emerald-600 font-semibold mt-0.5">
              {overview.high_propensity_pct}% — Immediate Sales Action
            </p>
          </div>

          <div className="bg-amber-50/70 p-4 rounded-xl border border-amber-200 shadow-sm">
            <div className="flex items-center justify-between text-xs font-bold text-amber-800 uppercase">
              <span>Medium Propensity (40–70%)</span>
              <TrendingUp className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-2xl font-extrabold text-amber-700 mt-1">
              {overview.medium_propensity_count.toLocaleString()}
            </div>
            <p className="text-[11px] text-amber-700 font-medium mt-0.5">
              {overview.medium_propensity_pct}% — Nurture & Consultative Demo
            </p>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-xs font-bold text-slate-600 uppercase">
              <span>Low Propensity (&lt;40%)</span>
              <AlertCircle className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-2xl font-extrabold text-slate-700 mt-1">
              {overview.low_propensity_count.toLocaleString()}
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {overview.low_propensity_pct}% — Automated Digital Follow-Up
            </p>
          </div>
        </div>
      )}

      {/* 2. Search & Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search by Lead ID (e.g. L00001), Business Name, or City..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded-lg transition-colors"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-100 text-xs">
          <div className="flex items-center space-x-1.5 text-slate-600 font-medium">
            <Filter className="w-3.5 h-3.5" />
            <span>Filters:</span>
          </div>

          {/* Segment Filter */}
          <select
            value={segment}
            onChange={(e) => {
              setSegment(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-xs font-medium focus:outline-none"
          >
            <option value="All">All Segments</option>
            <option value="Micro retail & services">Micro Retail & Services</option>
            <option value="Professional offices">Professional Offices</option>
            <option value="Small manufacturers">Small Manufacturers</option>
            <option value="Small multi-site businesses">Small Multi-Site</option>
          </select>

          {/* Stage Filter */}
          <select
            value={stage}
            onChange={(e) => {
              setStage(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-xs font-medium focus:outline-none"
          >
            <option value="All">All Stages</option>
            <option value="Lead">Lead (Intake)</option>
            <option value="Contacted">Contacted</option>
            <option value="Needs assessed">Needs Assessed</option>
            <option value="Quote accepted">Quote Accepted</option>
            <option value="KYC complete">KYC Complete</option>
          </select>

          {/* Propensity Band Filter */}
          <select
            value={band}
            onChange={(e) => {
              setBand(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-xs font-medium focus:outline-none"
          >
            <option value="All">All Propensities</option>
            <option value="HIGH">High (&ge;70%)</option>
            <option value="MEDIUM">Medium (40-70%)</option>
            <option value="LOW">Low (&lt;40%)</option>
          </select>

          {/* Unconverted Only Toggle */}
          <label className="flex items-center space-x-1.5 cursor-pointer text-slate-700 font-medium ml-auto">
            <input
              type="checkbox"
              checked={unconvertedOnly}
              onChange={(e) => {
                setUnconvertedOnly(e.target.checked);
                setPage(1);
              }}
              className="rounded text-red-600 focus:ring-red-500 h-3.5 w-3.5"
            />
            <span>Unconverted accounts only</span>
          </label>
        </div>
      </div>

      {/* 3. Prioritized Leads Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="text-xs font-bold text-slate-700">
            Showing {leads.length > 0 ? (page - 1) * pageSize + 1 : 0} –{' '}
            {Math.min(page * pageSize, totalCount)} of {totalCount.toLocaleString()} leads
          </div>
          <div className="flex items-center space-x-2 text-xs text-slate-500">
            <span>Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="font-medium bg-transparent border-0 text-slate-800 underline focus:ring-0 cursor-pointer"
            >
              <option value="propensity_score">Propensity Score</option>
              <option value="monthly_telecom_spend_inr">Monthly Spend</option>
              <option value="employee_count">Employees</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
              className="p-1 hover:bg-slate-100 rounded"
              title="Toggle sort direction"
            >
              <ArrowUpDown className="w-3.5 h-3.5 text-slate-600" />
            </button>
          </div>
        </div>

        {loading ? (
          <div className="py-16 text-center text-xs text-slate-500">
            Evaluating lead signals with zero-leakage ML pipeline...
          </div>
        ) : leads.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-500">
            No leads matching current filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Lead & Business</th>
                  <th className="px-4 py-3">Vertical & Location</th>
                  <th className="px-4 py-3">Channel</th>
                  <th className="px-4 py-3">Current Stage</th>
                  <th className="px-4 py-3 text-center">Propensity</th>
                  <th className="px-4 py-3">Primary Signal</th>
                  <th className="px-4 py-3">Recommended Next Step</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {leads.map((l) => (
                  <tr key={l.lead_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-3.5">
                      <div className="font-bold text-slate-900">{l.business_name || l.lead_id}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{l.lead_id} &bull; {l.business_type}</div>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="text-slate-800">{l.segment}</div>
                      <div className="text-[11px] text-slate-400">{l.city} (Tier {l.city_tier})</div>
                    </td>
                    <td className="px-4 py-3.5 text-slate-600">
                      <div>{l.lead_source}</div>
                      <div className="text-[11px] text-slate-400">₹{l.monthly_telecom_spend_inr?.toLocaleString()}/mo</div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                        {l.stage_reached}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-center">
                      <div
                        className={`inline-flex items-center px-2 py-1 rounded-lg text-xs font-extrabold ${
                          l.propensity_band === 'HIGH'
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                            : l.propensity_band === 'MEDIUM'
                            ? 'bg-amber-100 text-amber-800 border border-amber-300'
                            : 'bg-slate-100 text-slate-700 border border-slate-200'
                        }`}
                      >
                        {l.propensity_score}%
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">{l.propensity_band}</div>
                    </td>
                    <td className="px-4 py-3.5 max-w-[200px]">
                      {l.positive_factors && l.positive_factors.length > 0 ? (
                        <div className="text-[11px] text-emerald-700 truncate" title={l.positive_factors[0]}>
                          &bull; {l.positive_factors[0]}
                        </div>
                      ) : l.negative_factors && l.negative_factors.length > 0 ? (
                        <div className="text-[11px] text-red-600 truncate" title={l.negative_factors[0]}>
                          &bull; {l.negative_factors[0]}
                        </div>
                      ) : (
                        <div className="text-[11px] text-slate-400">Neutral profile</div>
                      )}
                    </td>
                    <td className="px-4 py-3.5 max-w-[220px]">
                      <div className="text-[11px] text-slate-600 line-clamp-2" title={l.recommended_next_action}>
                        {l.recommended_next_action}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <button
                        onClick={() => handleOpenLead(l.lead_id)}
                        className="px-2.5 py-1.5 bg-slate-100 hover:bg-red-50 hover:text-red-600 text-slate-700 font-bold text-xs rounded-lg border border-slate-200 hover:border-red-200 transition-colors inline-flex items-center space-x-1"
                      >
                        <span>Engage</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div className="px-6 py-4 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
          <div>
            Page <span className="font-bold text-slate-900">{page}</span> of{' '}
            <span className="font-bold text-slate-900">{totalPages}</span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 4. Lead Detail & Action Logging Modal */}
      {(selectedLead || modalLoading) && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200 flex flex-col">
            {modalLoading ? (
              <div className="p-12 text-center text-sm text-slate-500">Loading lead intelligence...</div>
            ) : selectedLead ? (
              <>
                {/* Modal Header */}
                <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between sticky top-0 bg-white z-10">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-red-100 text-red-700 flex items-center justify-center font-bold">
                      <Building className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="font-bold text-base text-slate-900">
                          {selectedLead.business_name || selectedLead.lead_id}
                        </h3>
                        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                          {selectedLead.lead_id}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">
                        {selectedLead.business_type} &bull; {selectedLead.segment} &bull; {selectedLead.city}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedLead(null)}
                    className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="p-6 space-y-6">
                  {/* Propensity Card & Stage Guidance */}
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div>
                      <div className="text-xs font-semibold text-slate-500 uppercase">Conversion Propensity</div>
                      <div className="flex items-baseline space-x-2 mt-0.5">
                        <span className="text-3xl font-extrabold text-slate-900">
                          {selectedLead.propensity_score}%
                        </span>
                        <span
                          className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                            selectedLead.propensity_band === 'HIGH'
                              ? 'bg-emerald-100 text-emerald-800'
                              : selectedLead.propensity_band === 'MEDIUM'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-slate-200 text-slate-700'
                          }`}
                        >
                          {selectedLead.propensity_band} PRIORITY
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-1">
                        Current Funnel Stage: <span className="font-bold text-slate-800">{selectedLead.stage_reached}</span>
                      </p>
                    </div>

                    <div className="max-w-xs bg-white p-3 rounded-lg border border-slate-200 text-xs">
                      <div className="font-bold text-red-600 flex items-center space-x-1 mb-1">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Recommended Play</span>
                      </div>
                      <p className="text-slate-600">{selectedLead.recommended_next_action}</p>
                    </div>
                  </div>

                  {/* Explainability Drivers */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-3.5 bg-emerald-50/70 border border-emerald-200 rounded-xl text-xs space-y-2">
                      <div className="font-bold text-emerald-900 flex items-center space-x-1">
                        <CheckCircle className="w-4 h-4 text-emerald-600" />
                        <span>Positive Conversion Drivers</span>
                      </div>
                      <ul className="space-y-1 text-emerald-800 text-[11px]">
                        {selectedLead.positive_factors.map((f, i) => (
                          <li key={i}>&bull; {f}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="p-3.5 bg-rose-50/70 border border-rose-200 rounded-xl text-xs space-y-2">
                      <div className="font-bold text-rose-900 flex items-center space-x-1">
                        <AlertCircle className="w-4 h-4 text-rose-600" />
                        <span>Friction Points & Risk Factors</span>
                      </div>
                      <ul className="space-y-1 text-rose-800 text-[11px]">
                        {selectedLead.negative_factors.map((f, i) => (
                          <li key={i}>&bull; {f}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Lead Profile Specs */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-slate-50 p-4 rounded-xl border border-slate-200">
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Acquisition Source</span>
                      <span className="font-semibold text-slate-800">{selectedLead.lead_source}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Monthly Spend</span>
                      <span className="font-semibold text-slate-800">₹{selectedLead.monthly_telecom_spend_inr?.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Employees & Sites</span>
                      <span className="font-semibold text-slate-800">{selectedLead.employee_count} emp &bull; {selectedLead.num_sites} site</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Current ISP</span>
                      <span className="font-semibold text-slate-800">{selectedLead.current_provider || 'None'}</span>
                    </div>
                  </div>

                  {/* Part 6 Sales Action Logging Form */}
                  <div className="border-t border-slate-200 pt-4 space-y-3">
                    <h4 className="font-bold text-xs text-slate-900 flex items-center space-x-1.5">
                      <PhoneCall className="w-4 h-4 text-red-600" />
                      <span>Log Sales Interaction Note (In-Memory Audit Log)</span>
                    </h4>

                    {actionSuccess && (
                      <div className="p-2 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-lg text-xs font-semibold">
                        Action note recorded successfully in audit log!
                      </div>
                    )}

                    <form onSubmit={handleLogAction} className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-[11px] font-semibold text-slate-600 mb-1">Action Type</label>
                          <select
                            value={actionType}
                            onChange={(e) => setActionType(e.target.value)}
                            className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs"
                          >
                            <option value="Phone Call">Phone Call</option>
                            <option value="Consultative Meeting">Consultative Meeting</option>
                            <option value="Product Demo">Product Demo</option>
                            <option value="Quote Adjustment">Quote Adjustment</option>
                            <option value="KYC Assistance">KYC Assistance</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-[11px] font-semibold text-slate-600 mb-1">Sales Rep</label>
                          <input
                            type="text"
                            value={repName}
                            onChange={(e) => setRepName(e.target.value)}
                            className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-[11px] font-semibold text-slate-600 mb-1">Interaction Notes</label>
                        <textarea
                          rows={2}
                          placeholder="Summarize customer feedback, objections, or agreed next steps..."
                          value={actionNotes}
                          onChange={(e) => setActionNotes(e.target.value)}
                          className="w-full p-2.5 border border-slate-200 rounded-lg text-xs focus:ring-2 focus:ring-red-500"
                          required
                        />
                      </div>

                      <button
                        type="submit"
                        disabled={actionSubmitting || !actionNotes.trim()}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold text-xs rounded-lg transition-colors flex items-center space-x-1.5"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>{actionSubmitting ? 'Recording...' : 'Save Interaction Note'}</span>
                      </button>
                    </form>

                    {/* Historical Log */}
                    {selectedLead.sales_action_history && selectedLead.sales_action_history.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-slate-100 space-y-2">
                        <div className="text-[11px] font-bold text-slate-700">Interaction History:</div>
                        <div className="space-y-2 max-h-36 overflow-y-auto">
                          {selectedLead.sales_action_history.map((act, idx) => (
                            <div key={idx} className="p-2 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                              <div className="flex items-center justify-between font-semibold text-slate-800 text-[11px]">
                                <span>{act.action_type} &bull; {act.rep_name}</span>
                                <span className="text-slate-400 font-normal">{new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                              </div>
                              <p className="text-slate-600 text-[11px] mt-0.5">{act.notes}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};

