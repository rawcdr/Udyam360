import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AdvisorPage } from '../pages/AdvisorPage';
import { OnboardingProvider } from '../context/OnboardingContext';
import { advisorApi } from '../api/advisor';

vi.mock('../api/advisor', () => ({
  advisorApi: {
    start: vi.fn(),
    sendMessage: vi.fn(),
    getConversation: vi.fn(),
    reset: vi.fn(),
    getHealth: vi.fn(),
  },
}));

vi.mock('../api/recommendations', () => ({
  recommendationApi: {
    getRecommendations: vi.fn().mockResolvedValue({
      profile_summary: { segment: 'micro', sites_count: 1 },
      essential_bundle: { tier: 'Essential', bundle_name: 'Essential Retail', monthly_price_min: 999, monthly_price_max: 999, included_products: [] },
      growth_bundle: { tier: 'Growth', bundle_name: 'Growth Retail', monthly_price_min: 1999, monthly_price_max: 1999, included_products: [] },
      premium_bundle: { tier: 'Premium', bundle_name: 'Premium Retail', monthly_price_min: 3499, monthly_price_max: 3499, included_products: [] },
    }),
  },
}));

describe('AdvisorPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it('initializes conversation session and renders welcome message', async () => {
    (advisorApi.start as any).mockResolvedValue({
      conversation_id: 'conv-test-001',
      welcome_message: 'Welcome to Udyam360 Advisor! What kind of business do you run?',
      suggested_prompts: ['Pharmacy in Chennai with 4 employees', 'CA practice in Pune'],
    });

    render(
      <OnboardingProvider>
        <BrowserRouter>
          <AdvisorPage />
        </BrowserRouter>
      </OnboardingProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Welcome to Udyam360 Advisor!/i)).toBeInTheDocument();
    });

    expect(screen.getByText('Pharmacy in Chennai with 4 employees')).toBeInTheDocument();
    expect(screen.getByText('CA practice in Pune')).toBeInTheDocument();
  });

  it('sends user message and displays advisor response and updated profile', async () => {
    (advisorApi.start as any).mockResolvedValue({
      conversation_id: 'conv-test-002',
      welcome_message: 'Hello!',
      suggested_prompts: [],
    });

    (advisorApi.sendMessage as any).mockResolvedValue({
      conversation_id: 'conv-test-002',
      assistant_message: 'Understood. A retail pharmacy in Chennai with 4 staff.',
      extracted_profile: {
        business_type: 'Pharmacy',
        num_employees: 4,
        city: 'Chennai',
        budget_monthly: 4000,
        gstin_available: false,
        requested_services: ['Broadband', 'POS Backup'],
      },
      missing_fields: [],
      clarification_required: false,
      recommendations_available: true,
      processing_status: 'SUCCESS',
    });

    render(
      <OnboardingProvider>
        <BrowserRouter>
          <AdvisorPage />
        </BrowserRouter>
      </OnboardingProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Hello!')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/I run a 4-person dental clinic/i);
    const sendBtn = screen.getByRole('button', { name: /Send/i });

    fireEvent.change(input, {
      target: { value: 'I run a pharmacy in Chennai with 4 staff and budget 4000' },
    });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(
        screen.getByText('Understood. A retail pharmacy in Chennai with 4 staff.')
      ).toBeInTheDocument();
    });

    // Profile panel updates
    expect(screen.getByText('Pharmacy')).toBeInTheDocument();
    expect(screen.getByText('4 staff')).toBeInTheDocument();
    expect(screen.getByText(/₹4,000/)).toBeInTheDocument();
  });

  it('displays error notice when advisor API fails', async () => {
    (advisorApi.start as any).mockResolvedValue({
      conversation_id: 'conv-test-003',
      welcome_message: 'Hello!',
      suggested_prompts: [],
    });

    (advisorApi.sendMessage as any).mockRejectedValue(new Error('Gemini API quota exhausted.'));

    render(
      <OnboardingProvider>
        <BrowserRouter>
          <AdvisorPage />
        </BrowserRouter>
      </OnboardingProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Hello!')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/I run a 4-person dental clinic/i);
    const sendBtn = screen.getByRole('button', { name: /Send/i });

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText(/Gemini API quota exhausted./i)).toBeInTheDocument();
    });
  });
});

