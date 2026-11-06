import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useOnboarding } from '../context/OnboardingContext';
import { advisorApi } from '../api/advisor';
import { recommendationApi } from '../api/recommendations';
import { ChatMessage } from '../types/advisor';
import {
  Sparkles,
  Send,
  RotateCcw,
  Bot,
  User,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Building,
  Users,
  MapPin,
  IndianRupee,
  FileSpreadsheet,
  Check,
  ShieldAlert,
  Loader2,
} from 'lucide-react';

export const AdvisorPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    conversationId,
    setConversationId,
    profile,
    setProfile,
    setRecommendations,
    selectBundle,
  } = useOnboarding();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [recommendationsReady, setRecommendationsReady] = useState<boolean>(false);
  const [isFallbackMode, setIsFallbackMode] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Initialize or resume conversation
  useEffect(() => {
    const initConversation = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const urlConvId = urlParams.get('conv');
      const activeConvId = urlConvId || conversationId;

      if (activeConvId) {
        try {
          const state = await advisorApi.getConversation(activeConvId);
          setConversationId(activeConvId);
          setMessages(state.history);
          setProfile(state.profile);
          setMissingFields(state.missing_fields || []);
          setRecommendationsReady(state.recommendations_available);
          return;
        } catch (err) {
          console.warn('Failed to recover previous conversation session. Starting fresh.');
        }
      }

      // Start fresh session
      setIsLoading(true);
      try {
        const initData = await advisorApi.start();
        setConversationId(initData.conversation_id);
        setSuggestedPrompts(initData.suggested_prompts || []);
        setMessages([
          {
            role: 'assistant',
            content: initData.welcome_message,
            timestamp: new Date().toISOString(),
          },
        ]);
      } catch (err: any) {
        setErrorMessage(err.message || 'Could not connect to Advisor backend.');
      } finally {
        setIsLoading(false);
      }
    };

    initConversation();
  }, []);

  const handleSendMessage = async (textToSend?: string) => {
    const message = (textToSend || inputText).trim();
    if (!message || !conversationId || isLoading) return;

    // Optimistically push user message
    const userMsg: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await advisorApi.sendMessage(conversationId, message);

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: response.assistant_message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (response.extracted_profile) {
        setProfile(response.extracted_profile);
      }
      setMissingFields(response.missing_fields || []);
      setRecommendationsReady(response.recommendations_available);
      setIsFallbackMode(response.processing_status === 'FALLBACK');

      if (response.recommendations) {
        setRecommendations(response.recommendations);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Error communicating with GenAI Advisor.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    if (!conversationId) return;
    setIsLoading(true);
    try {
      await advisorApi.reset(conversationId);
      const initData = await advisorApi.start();
      setConversationId(initData.conversation_id);
      setSuggestedPrompts(initData.suggested_prompts || []);
      setMessages([
        {
          role: 'assistant',
          content: initData.welcome_message,
          timestamp: new Date().toISOString(),
        },
      ]);
      setRecommendationsReady(false);
      setMissingFields([]);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to reset session.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleProceedToRecommendations = async () => {
    setIsLoading(true);
    try {
      const recs = await recommendationApi.getRecommendations(profile);
      setRecommendations(recs);
      if (recs.growth_bundle) {
        await selectBundle(recs.growth_bundle);
      }
      navigate('/recommendations');
    } catch (err: any) {
      setErrorMessage('Could not generate recommendations: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              AI Business Advisor
            </h1>
            <span className="px-2 py-0.5 rounded bg-red-100 text-red-700 font-bold text-xs">
              Gemini Powered
            </span>
            {isFallbackMode && (
              <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-semibold text-xs flex items-center space-x-1">
                <ShieldAlert className="w-3 h-3 text-amber-600" />
                <span>Deterministic Fallback Active</span>
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Describe your business in plain words. The advisor will configure suitable connectivity, software, and bundles.
          </p>
        </div>

        <button
          onClick={handleReset}
          className="self-start sm:self-auto inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-red-600 bg-white hover:bg-red-50 border border-slate-200 hover:border-red-200 rounded-lg shadow-2xs transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* Main 2-Panel Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Panel: Conversational Chat (7 cols) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[700px]">
          {/* Chat Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
            {messages.map((msg, idx) => {
              const isAssistant = msg.role === 'assistant';
              return (
                <div
                  key={idx}
                  className={`flex items-start space-x-3 ${
                    isAssistant ? '' : 'flex-row-reverse space-x-reverse'
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                      isAssistant
                        ? 'bg-red-600 text-white shadow-xs'
                        : 'bg-slate-800 text-white'
                    }`}
                  >
                    {isAssistant ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                  </div>

                  <div
                    className={`max-w-[85%] sm:max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      isAssistant
                        ? 'bg-slate-100/90 text-slate-800 rounded-tl-xs'
                        : 'bg-red-600 text-white rounded-tr-xs shadow-xs'
                    }`}
                  >
                    <p className="whitespace-pre-line">{msg.content}</p>
                    <span
                      className={`text-[10px] block mt-1.5 font-medium ${
                        isAssistant ? 'text-slate-400' : 'text-red-200'
                      }`}
                    >
                      {new Date(msg.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                </div>
              );
            })}

            {/* Typing Loader */}
            {isLoading && (
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-xl bg-red-600 text-white flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-slate-100 rounded-2xl rounded-tl-xs px-4 py-3 text-sm text-slate-600 flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 text-red-600 animate-spin" />
                  <span className="text-xs font-medium">Advisor is analyzing your requirements...</span>
                </div>
              </div>
            )}

            {/* Error Message */}
            {errorMessage && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
                <span>{errorMessage}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompt Suggestions */}
          {suggestedPrompts.length > 0 && (
            <div className="px-4 py-2 border-t border-slate-100 bg-slate-50/70 overflow-x-auto flex items-center space-x-2">
              <span className="text-[11px] font-bold text-slate-400 shrink-0">Suggested:</span>
              {suggestedPrompts.map((prompt, i) => (
                <button
                  key={i}
                  disabled={isLoading}
                  onClick={() => handleSendMessage(prompt)}
                  className="shrink-0 text-xs px-3 py-1 bg-white hover:bg-slate-100 border border-slate-200 rounded-full text-slate-700 font-medium transition-colors hover:border-slate-300 shadow-2xs"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}

          {/* Chat Input Bar */}
          <div className="p-4 border-t border-slate-200 bg-white rounded-b-2xl">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center space-x-2"
            >
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="e.g. I run a 4-person dental clinic in Pune with ₹5,000 monthly budget..."
                disabled={isLoading}
                className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-red-500 focus:bg-white transition-all disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={isLoading || !inputText.trim()}
                className="px-4 py-2.5 bg-red-600 hover:bg-red-700 disabled:bg-slate-300 text-white font-semibold rounded-xl transition-all shadow-sm flex items-center space-x-1.5"
              >
                <span>Send</span>
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>

        {/* Right Panel: Live Extracted Profile Summary (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-lg bg-red-100 text-red-600 flex items-center justify-center">
                  <Building className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Extracted Profile</h3>
                  <p className="text-[11px] text-slate-500">Live backend understanding</p>
                </div>
              </div>

              <span
                className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                  recommendationsReady
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-amber-100 text-amber-800'
                }`}
              >
                {recommendationsReady ? 'Ready for Bundles' : 'Gathering Info'}
              </span>
            </div>

            {/* Profile Attributes Grid */}
            <div className="space-y-3.5 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-medium flex items-center space-x-1.5">
                  <Building className="w-3.5 h-3.5 text-slate-400" />
                  <span>Business Name</span>
                </span>
                <span className="font-bold text-slate-900">
                  {profile.business_name || <span className="text-slate-400 italic">Not specified</span>}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-medium flex items-center space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-slate-400" />
                  <span>Type / Category</span>
                </span>
                <span className="font-bold text-slate-900">
                  {profile.business_type || <span className="text-slate-400 italic">e.g. Pharmacy / Clinic</span>}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-medium flex items-center space-x-1.5">
                  <Users className="w-3.5 h-3.5 text-slate-400" />
                  <span>Employees</span>
                </span>
                <span className="font-bold text-slate-900">
                  {profile.num_employees ? `${profile.num_employees} staff` : <span className="text-slate-400 italic">Not set</span>}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-medium flex items-center space-x-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  <span>Location</span>
                </span>
                <span className="font-bold text-slate-900">
                  {profile.city ? `${profile.city} (Tier ${profile.city_tier || 1})` : 'Bengaluru (Tier 1)'}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-medium flex items-center space-x-1.5">
                  <FileSpreadsheet className="w-3.5 h-3.5 text-slate-400" />
                  <span>GSTIN Status</span>
                </span>
                <span className={`font-bold ${profile.gstin_available ? 'text-emerald-600' : 'text-slate-600'}`}>
                  {profile.gstin_available ? 'Available (GST Registered)' : 'Not available / Exempt'}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-medium flex items-center space-x-1.5">
                  <IndianRupee className="w-3.5 h-3.5 text-slate-400" />
                  <span>Monthly Budget</span>
                </span>
                <span className="font-extrabold text-slate-900 text-sm">
                  {profile.budget_monthly ? `₹${profile.budget_monthly.toLocaleString()}` : '₹3,000 (Default)'}
                </span>
              </div>

              {/* Requested Services Badges */}
              <div className="pt-2">
                <span className="text-slate-500 font-medium block mb-2">Requested Services:</span>
                {profile.requested_services && profile.requested_services.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {profile.requested_services.map((srv, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded font-semibold text-[11px]"
                      >
                        {srv}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 italic">Broadband connectivity, calling, POS backup</p>
                )}
              </div>
            </div>

            {/* Missing Fields Checklist */}
            {missingFields.length > 0 && (
              <div className="mt-5 p-3 rounded-xl bg-amber-50/80 border border-amber-200">
                <p className="text-[11px] font-bold text-amber-800 mb-1.5 flex items-center space-x-1">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                  <span>To refine recommendations, provide:</span>
                </p>
                <div className="flex flex-wrap gap-1">
                  {missingFields.map((f, idx) => (
                    <span key={idx} className="text-[10px] bg-white border border-amber-300 text-amber-800 px-1.5 py-0.5 rounded font-medium">
                      {f.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Proceed CTA Button */}
            <div className="mt-6 pt-4 border-t border-slate-100">
              <button
                onClick={handleProceedToRecommendations}
                disabled={isLoading}
                className="w-full py-3 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold rounded-xl shadow-md shadow-red-600/20 hover:shadow-lg transition-all flex items-center justify-center space-x-2 text-sm"
              >
                <span>View Recommendations</span>
                <ArrowRight className="w-4 h-4" />
              </button>
              <p className="text-center text-[11px] text-slate-400 mt-2">
                Generates Essential, Growth & Premium catalogue bundles
              </p>
            </div>
          </div>

          {/* Segment Guide Note */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600">
            <p className="font-semibold text-slate-800 mb-1 flex items-center space-x-1.5">
              <Check className="w-3.5 h-3.5 text-emerald-600" />
              <span>Deterministic Backend Guarantee</span>
            </p>
            <p className="text-slate-500 leading-relaxed">
              Gemini assists only with conversation and requirement extraction. All product bundles, prices, and eligibility rules are strictly computed by deterministic backend engines.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

