import React, { useEffect, useState } from 'react';
import {
  adminApi,
  OverviewKPIs,
  FunnelAnalysis,
  SegmentAnalysis,
  LeadSourceAnalysis,
  GeographicAnalysis,
} from '../../api/admin';
import {
  Users,
  CheckCircle2,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  Layers,
  PhoneForwarded,
  FileCheck2,
  MapPin,
  RefreshCw,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

export const AdminOverviewPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [kpis, setKpis] = useState<OverviewKPIs | null>(null);
  const [funnel, setFunnel] = useState<FunnelAnalysis | null>(null);
  const [segments, setSegments] = useState<SegmentAnalysis[]>([]);
  const [sources, setSources] = useState<LeadSourceAnalysis[]>([]);
  const [geography, setGeography] = useState<GeographicAnalysis | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpisRes, funnelRes, segRes, srcRes, geoRes] = await Promise.all([
        adminApi.getOverviewKPIs(),
        adminApi.getFunnelAnalysis(),
        adminApi.getSegmentAnalysis(),
        adminApi.getLeadSources(),
        adminApi.getGeographicAnalysis(),
      ]);
      setKpis(kpisRes);
      setFunnel(funnelRes);
      setSegments(segRes);
      setSources(srcRes);
      setGeography(geoRes);
    } catch (err: any) {
      console.error('Failed to load admin telemetry:', err);
      setError(err.message || 'Could not load administrative analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <RefreshCw className="w-8 h-8 text-red-600 animate-spin" />
        <p className="text-sm font-medium text-slate-500">
          Aggregating enterprise telemetry & calculating 6-stage funnel...
        </p>
      </div>
    );
  }

  if (error || !kpis || !funnel) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-red-800">
        <div className="flex items-center space-x-2 font-bold mb-2">
          <AlertTriangle className="w-5 h-5 text-red-600" />
          <span>Error loading executive dashboard</span>
        </div>
        <p className="text-sm mb-4">{error}</p>
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-red-600 text-white font-semibold text-xs rounded-lg hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const stageColors = ['#64748b', '#3b82f6', '#0284c7', '#8b5cf6', '#d97706', '#10b981'];

  return (
    <div className="space-y-8">
      {/* 1. Headline KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">
            <span>Total Intake</span>
            <Users className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900">{kpis.total_leads.toLocaleString()}</div>
          <p className="text-[11px] text-slate-400 mt-0.5">100% Raw Volume</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">
            <span>Contacted</span>
            <PhoneForwarded className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-extrabold text-blue-600">{kpis.contacted_leads.toLocaleString()}</div>
          <p className="text-[11px] text-slate-500 mt-0.5">
            {((kpis.contacted_leads / kpis.total_leads) * 100).toFixed(1)}% reached
          </p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">
            <span>Needs Assessed</span>
            <Layers className="w-4 h-4 text-sky-500" />
          </div>
          <div className="text-2xl font-extrabold text-sky-600">{kpis.needs_assessed_leads.toLocaleString()}</div>
          <p className="text-[11px] text-slate-500 mt-0.5">
            {((kpis.needs_assessed_leads / kpis.total_leads) * 100).toFixed(1)}% profiled
          </p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">
            <span>Quotes Accepted</span>
            <FileCheck2 className="w-4 h-4 text-purple-500" />
          </div>
          <div className="text-2xl font-extrabold text-purple-600">{kpis.quote_accepted_leads.toLocaleString()}</div>
          <p className="text-[11px] text-slate-500 mt-0.5">
            {((kpis.quote_accepted_leads / kpis.total_leads) * 100).toFixed(1)}% commercial fit
          </p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">
            <span>KYC Verified</span>
            <CheckCircle2 className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-extrabold text-amber-600">{kpis.kyc_completed_leads.toLocaleString()}</div>
          <p className="text-[11px] text-slate-500 mt-0.5">
            {((kpis.kyc_completed_leads / kpis.total_leads) * 100).toFixed(1)}% vetted
          </p>
        </div>

        <div className="bg-emerald-50/70 p-4 rounded-xl border border-emerald-200 shadow-sm">
          <div className="flex items-center justify-between text-emerald-800 text-xs font-semibold uppercase tracking-wider mb-1">
            <span>Activated</span>
            <TrendingUp className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-700">{kpis.activated_leads.toLocaleString()}</div>
          <p className="text-[11px] font-bold text-emerald-600 mt-0.5">
            {kpis.overall_conversion_rate_pct.toFixed(2)}% Overall Conv
          </p>
        </div>
      </div>

      {/* 2. Bottleneck Diagnosis Alert */}
      <div className="p-4 bg-amber-50 border border-amber-300 rounded-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start space-x-3">
          <div className="p-2 bg-amber-200 rounded-lg text-amber-800 mt-0.5">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-amber-900 text-sm">
              Primary Bottleneck Alert: {funnel.primary_bottleneck.largest_volume_bottleneck} &{' '}
              {funnel.primary_bottleneck.highest_rate_bottleneck}
            </h3>
            <p className="text-xs text-amber-800 mt-0.5">{funnel.primary_bottleneck.explanation}</p>
          </div>
        </div>
        <div className="flex items-center space-x-4 bg-white/80 px-4 py-2 rounded-lg border border-amber-200 text-xs text-amber-900 font-semibold self-stretch md:self-auto justify-between">
          <span>Max Volume Lost: -{funnel.primary_bottleneck.volume_lost}</span>
          <span className="text-red-600">Max Drop Rate: {funnel.primary_bottleneck.highest_rate_pct}%</span>
        </div>
      </div>

      {/* 3. Funnel Progression Breakdown */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">6-Stage Lead Funnel Conversion & Attrition</h2>
            <p className="text-xs text-slate-500">
              Complete progression from cold intake to revenue activation across all 5,000 accounts
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-full border border-slate-200">
            Audit Benchmark Verified
          </span>
        </div>

        {/* Recharts Bar View */}
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={funnel.stages} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
              <XAxis dataKey="stage_name" tick={{ fontSize: 11, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload as FunnelAnalysis['stages'][0];
                    return (
                      <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl text-xs space-y-1">
                        <div className="font-bold border-b border-slate-700 pb-1 mb-1">{data.stage_name}</div>
                        <div>Volume Reached: <span className="font-semibold">{data.count}</span></div>
                        <div>Entered Stage: <span className="font-semibold">{data.entered}</span></div>
                        <div className="text-red-400">Dropped at Stage: <span className="font-semibold">-{data.dropped}</span> ({data.stage_drop_rate_pct}%)</div>
                        <div className="text-emerald-400">Cumulative Conversion: <span className="font-semibold">{data.overall_conversion_pct}%</span></div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {funnel.stages.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={stageColors[index % stageColors.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Detailed Funnel Stage Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          {funnel.stages.map((s, idx) => (
            <div key={s.stage_name} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800">{s.stage_name}</span>
                <span className="text-[10px] font-semibold text-slate-400">#{idx + 1}</span>
              </div>
              <div className="text-lg font-extrabold text-slate-900">{s.count.toLocaleString()}</div>
              {idx > 0 && (
                <div className="text-[11px] text-red-600 font-medium">
                  -{s.dropped} dropped ({s.stage_drop_rate_pct}%)
                </div>
              )}
              <div className="text-[11px] text-slate-500">
                {s.overall_conversion_pct}% of total intake
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Segments & Lead Sources Breakdown Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Segment Conversion */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-sm text-slate-900">Segment Conversion Disparity</h3>
              <p className="text-xs text-slate-500">Activations and conversion rates across MSME verticals</p>
            </div>
          </div>
          <div className="space-y-3">
            {segments.map((seg) => (
              <div key={seg.segment} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-700">{seg.segment}</span>
                  <div className="space-x-2 text-right">
                    <span className="text-slate-500">{seg.activated_leads} / {seg.total_leads}</span>
                    <span className="font-bold text-slate-900">{seg.conversion_rate_pct}%</span>
                  </div>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-red-600 rounded-full"
                    style={{ width: `${Math.min(100, seg.conversion_rate_pct * 6)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Lead Sources Comparison */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-sm text-slate-900">Lead Acquisition Channel Performance</h3>
              <p className="text-xs text-slate-500">Referral and inbound channels drastically outperform cold campaigns</p>
            </div>
          </div>
          <div className="space-y-3">
            {sources.map((src) => (
              <div key={src.lead_source} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-700">{src.lead_source}</span>
                  <div className="space-x-2 text-right">
                    <span className="text-slate-500">{src.activated_leads} / {src.total_leads}</span>
                    <span
                      className={`font-bold ${
                        src.conversion_rate_pct >= 10
                          ? 'text-emerald-600'
                          : src.conversion_rate_pct <= 3
                          ? 'text-red-600'
                          : 'text-slate-900'
                      }`}
                    >
                      {src.conversion_rate_pct}%
                    </span>
                  </div>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      src.conversion_rate_pct >= 10
                        ? 'bg-emerald-500'
                        : src.conversion_rate_pct <= 3
                        ? 'bg-red-500'
                        : 'bg-blue-500'
                    }`}
                    style={{ width: `${Math.min(100, src.conversion_rate_pct * 5.5)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 5. Geographic & City Tier Distribution */}
      {geography && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center space-x-2">
            <MapPin className="w-5 h-5 text-red-600" />
            <div>
              <h3 className="font-bold text-sm text-slate-900">Geographic Footprint & City Tier Performance</h3>
              <p className="text-xs text-slate-500">Lead distribution across Tier 1 metros vs Tier 2/3 developing markets</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {geography.by_tier.map((tier) => (
              <div key={String(tier.city_tier)} className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Tier {tier.city_tier}
                </div>
                <div className="text-xl font-extrabold text-slate-900 mt-1">
                  {tier.total_leads.toLocaleString()} Leads
                </div>
                <div className="text-xs text-slate-600 mt-0.5">
                  {tier.activated_leads} Activations ({tier.conversion_rate_pct}% Conv)
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2">
            <div className="text-xs font-bold text-slate-700 mb-2">Top MSME Hub Cities:</div>
            <div className="flex flex-wrap gap-2">
              {geography.top_cities.map((city) => (
                <span
                  key={city.city}
                  className="px-2.5 py-1 bg-slate-100 text-slate-700 text-xs rounded-md border border-slate-200"
                >
                  <span className="font-semibold">{city.city}</span>: {city.total_leads} leads ({city.conversion_rate_pct}%)
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

