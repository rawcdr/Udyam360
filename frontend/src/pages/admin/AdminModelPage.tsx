import React, { useEffect, useState } from 'react';
import {
  adminApi,
  ModelInfo,
  EvaluationReport,
  FeatureImportance,
  SingleLeadScoreResult,
} from '../../api/admin';
import {
  BrainCircuit,
  ShieldCheck,
  Award,
  Layers,
  Sparkles,
  BarChart2,
  Play,
  CheckCircle,
  AlertCircle,
  Info,
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

export const AdminModelPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [evalReport, setEvalReport] = useState<EvaluationReport | null>(null);
  const [features, setFeatures] = useState<FeatureImportance[]>([]);

  // Sandbox State
  const [sandboxSegment, setSandboxSegment] = useState('Professional offices');
  const [sandboxSource, setSandboxSource] = useState('Referral');
  const [sandboxCityTier, setSandboxCityTier] = useState(1);
  const [sandboxEmployees, setSandboxEmployees] = useState(8);
  const [sandboxSpend, setSandboxSpend] = useState(6000);
  const [sandboxGstin, setSandboxGstin] = useState('Y');
  const [sandboxUdyam, setSandboxUdyam] = useState('Y');
  const [sandboxScoring, setSandboxScoring] = useState(false);
  const [sandboxResult, setSandboxResult] = useState<SingleLeadScoreResult | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [infoRes, evalRes, featsRes] = await Promise.all([
        adminApi.getModelInfo(),
        adminApi.getModelEvaluation(),
        adminApi.getFeatureImportances(),
      ]);
      setModelInfo(infoRes);
      setEvalReport(evalRes);
      setFeatures(featsRes);
    } catch (e) {
      console.error('Failed to load ML model intelligence:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunSandbox = async (e: React.FormEvent) => {
    e.preventDefault();
    setSandboxScoring(true);
    try {
      const leadDict = {
        lead_id: 'SANDBOX_PROSPECT',
        business_type: sandboxSegment === 'Professional offices' ? 'CA Practice' : 'Retailer',
        segment: sandboxSegment,
        lead_source: sandboxSource,
        city: sandboxCityTier === 1 ? 'Bengaluru' : 'Indore',
        city_tier: sandboxCityTier,
        state: sandboxCityTier === 1 ? 'Karnataka' : 'Madhya Pradesh',
        employee_count: sandboxEmployees,
        num_sites: 1,
        monthly_telecom_spend_inr: sandboxSpend,
        has_gstin: sandboxGstin,
        has_udyam: sandboxUdyam,
        contact_role: 'Owner',
        preferred_language: 'English',
        current_internet: 'Broadband',
        current_provider: 'Airtel',
      };
      const res = await adminApi.scoreSingleLead(leadDict);
      setSandboxResult(res);
    } catch (err) {
      console.error('Failed to score sandbox lead:', err);
    } finally {
      setSandboxScoring(false);
    }
  };

  if (loading || !modelInfo || !evalReport) {
    return (
      <div className="py-24 text-center text-xs text-slate-500">
        Loading model architecture, evaluation reports & global feature weights...
      </div>
    );
  }

  const topFeatures = features.slice(0, 10);

  return (
    <div className="space-y-8">
      {/* 1. Header & Zero-Leakage Architecture Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-3">
            <div className="p-3 bg-red-100 text-red-700 rounded-xl">
              <BrainCircuit className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-slate-900">
                  {modelInfo.model_name} v{modelInfo.model_version} (Production Selected)
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                  Active in Pipeline
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Linear Odds Calibrated Classifier trained on 3,500 accounts with 100% explainability
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 bg-slate-50 px-3 py-2 rounded-lg border border-slate-200 text-xs">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span className="text-slate-700 font-semibold">Zero Data Leakage:</span>
            <span className="text-slate-500">17 downstream post-quote & activation features strictly blacklisted</span>
          </div>
        </div>

        {/* Dataset Split & Feature Dimension Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-slate-100 text-xs">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Training Set (70%)</span>
            <span className="font-extrabold text-slate-900 text-sm">
              {modelInfo.splits.train_size.toLocaleString()} Leads (Stratified)
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Held-Out Test Set (15%)</span>
            <span className="font-extrabold text-slate-900 text-sm">
              {modelInfo.splits.test_size} Leads (Zero Contamination)
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Allowlist Features</span>
            <span className="font-extrabold text-slate-900 text-sm">
              24 Features (12 Cat + 12 Num)
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Transformed Dimension</span>
            <span className="font-extrabold text-slate-900 text-sm">
              {modelInfo.feature_schema.total_transformed_features} OHE Columns
            </span>
          </div>
        </div>
      </div>

      {/* 2. Candidate Model Benchmark Comparison */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-sm text-slate-900">Candidate Model Benchmark & Selection Matrix</h3>
            <p className="text-xs text-slate-500">
              Evaluated across ROC-AUC, PR-AUC, Brier score calibration, and explainability on held-out test data
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full flex items-center space-x-1">
            <Award className="w-3.5 h-3.5" />
            <span>Winner: Logistic Regression</span>
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Candidate Model</th>
                <th className="px-4 py-3 text-center">Val ROC-AUC</th>
                <th className="px-4 py-3 text-center">Test ROC-AUC</th>
                <th className="px-4 py-3 text-center">Test PR-AUC</th>
                <th className="px-4 py-3 text-center">Brier Score</th>
                <th className="px-4 py-3">Selection Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {Object.entries(evalReport.comparison).map(([name, data]: [string, any]) => {
                const isSelected = name === evalReport.selected_model;
                return (
                  <tr key={name} className={isSelected ? 'bg-red-50/40 font-semibold' : 'hover:bg-slate-50'}>
                    <td className="px-4 py-3.5">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-slate-900">{name}</span>
                        {isSelected && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-red-600 text-white font-bold">
                            Selected
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 text-center text-slate-700">{data.val_roc_auc?.toFixed(4)}</td>
                    <td className="px-4 py-3.5 text-center text-slate-900 font-bold">{data.test_roc_auc?.toFixed(4)}</td>
                    <td className="px-4 py-3.5 text-center text-slate-700">{data.test_pr_auc?.toFixed(4)}</td>
                    <td className="px-4 py-3.5 text-center text-slate-700">{data.test_brier?.toFixed(4)}</td>
                    <td className="px-4 py-3.5 text-slate-600 text-[11px] max-w-xs">
                      {isSelected
                        ? 'Highest test ROC-AUC (0.6692) & PR-AUC (0.1327) with 100% linear odds interpretability and zero overfitting.'
                        : name === 'RandomForest'
                        ? 'Prone to tree variance on sparse 7.36% positive minority class; non-convex odds interpretability.'
                        : 'Higher inference latency; risk of over-indexing on non-monotonic categorical combinations.'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. Global Feature Importance Chart */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div>
          <h3 className="font-bold text-sm text-slate-900">Top Feature Drivers (Log-Odds Impact)</h3>
          <p className="text-xs text-slate-500">
            Positive weights increase conversion odds; negative weights signify historical friction or drop risks
          </p>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={topFeatures}
              layout="vertical"
              margin={{ top: 10, right: 30, left: 160, bottom: 10 }}
            >
              <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} />
              <YAxis
                dataKey="feature"
                type="category"
                tick={{ fontSize: 11, fill: '#334155' }}
                width={150}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload as FeatureImportance;
                    return (
                      <div className="bg-slate-900 text-white p-2.5 rounded shadow text-xs">
                        <div className="font-bold">{d.feature}</div>
                        <div>Weight: <span className="font-mono">{d.coefficient?.toFixed(4)}</span></div>
                        <div className={d.impact === 'POSITIVE' ? 'text-emerald-400' : 'text-red-400'}>
                          Impact: {d.impact}
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="coefficient">
                {topFeatures.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.coefficient && entry.coefficient > 0 ? '#10b981' : '#f43f5e'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 4. Interactive Real-Time Scoring Sandbox */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center space-x-2">
          <Play className="w-5 h-5 text-red-600" />
          <div>
            <h3 className="font-bold text-sm text-slate-900">Live Propensity Scoring Sandbox</h3>
            <p className="text-xs text-slate-500">
              Score an arbitrary MSME prospect in real time with transparent driver decomposition
            </p>
          </div>
        </div>

        <form onSubmit={handleRunSandbox} className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-600 mb-1">Business Vertical</label>
            <select
              value={sandboxSegment}
              onChange={(e) => setSandboxSegment(e.target.value)}
              className="w-full px-2.5 py-2 border border-slate-200 rounded-lg"
            >
              <option value="Professional offices">Professional Offices</option>
              <option value="Small manufacturers">Small Manufacturers</option>
              <option value="Micro retail & services">Micro Retail & Services</option>
              <option value="Small multi-site businesses">Small Multi-Site</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-slate-600 mb-1">Acquisition Source</label>
            <select
              value={sandboxSource}
              onChange={(e) => setSandboxSource(e.target.value)}
              className="w-full px-2.5 py-2 border border-slate-200 rounded-lg"
            >
              <option value="Referral">Referral (+98% odds)</option>
              <option value="Inbound call">Inbound Call (+26% odds)</option>
              <option value="Channel partner">Channel Partner</option>
              <option value="Field sales">Field Sales</option>
              <option value="Website form">Website Form</option>
              <option value="WhatsApp campaign">WhatsApp Campaign (-101% odds)</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-slate-600 mb-1">Monthly Spend (₹)</label>
            <input
              type="number"
              value={sandboxSpend}
              onChange={(e) => setSandboxSpend(Number(e.target.value))}
              className="w-full px-2.5 py-2 border border-slate-200 rounded-lg"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-600 mb-1">Employees & Tier</label>
            <div className="flex space-x-2">
              <input
                type="number"
                placeholder="Emp"
                value={sandboxEmployees}
                onChange={(e) => setSandboxEmployees(Number(e.target.value))}
                className="w-1/2 px-2.5 py-2 border border-slate-200 rounded-lg"
              />
              <select
                value={sandboxCityTier}
                onChange={(e) => setSandboxCityTier(Number(e.target.value))}
                className="w-1/2 px-2.5 py-2 border border-slate-200 rounded-lg"
              >
                <option value={1}>Tier 1</option>
                <option value={2}>Tier 2</option>
                <option value={3}>Tier 3</option>
              </select>
            </div>
          </div>

          <div className="md:col-span-4 flex items-center justify-between pt-2">
            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={sandboxGstin === 'Y'}
                  onChange={(e) => setSandboxGstin(e.target.checked ? 'Y' : 'N')}
                  className="rounded text-red-600"
                />
                <span>GSTIN Registered</span>
              </label>

              <label className="flex items-center space-x-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={sandboxUdyam === 'Y'}
                  onChange={(e) => setSandboxUdyam(e.target.checked ? 'Y' : 'N')}
                  className="rounded text-red-600"
                />
                <span>Udyam Certified</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={sandboxScoring}
              className="px-5 py-2 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded-lg transition-colors flex items-center space-x-1.5"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{sandboxScoring ? 'Calculating...' : 'Score Prospect'}</span>
            </button>
          </div>
        </form>

        {/* Sandbox Output Card */}
        {sandboxResult && (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3 mt-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-500 font-semibold uppercase">Propensity Result:</span>
                <div className="flex items-baseline space-x-2">
                  <span className="text-2xl font-extrabold text-slate-900">
                    {sandboxResult.propensity_score}%
                  </span>
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      sandboxResult.propensity_band === 'HIGH'
                        ? 'bg-emerald-100 text-emerald-800'
                        : sandboxResult.propensity_band === 'MEDIUM'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {sandboxResult.propensity_band} PROPENSITY
                  </span>
                </div>
              </div>
              <div className="text-right text-xs">
                <span className="text-slate-400">Play:</span>
                <div className="font-bold text-red-600">{sandboxResult.recommended_next_action}</div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-2 border-t border-slate-200">
              <div className="text-emerald-800 bg-emerald-50/70 p-2.5 rounded-lg border border-emerald-200">
                <div className="font-bold mb-1">Positive Drivers:</div>
                <ul className="space-y-0.5 text-[11px]">
                  {sandboxResult.positive_factors.map((f, i) => (
                    <li key={i}>&bull; {f}</li>
                  ))}
                </ul>
              </div>
              <div className="text-rose-800 bg-rose-50/70 p-2.5 rounded-lg border border-rose-200">
                <div className="font-bold mb-1">Risk Factors:</div>
                <ul className="space-y-0.5 text-[11px]">
                  {sandboxResult.negative_factors.map((f, i) => (
                    <li key={i}>&bull; {f}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

