import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { LandingPage } from '../pages/LandingPage';
import { OnboardingProvider } from '../context/OnboardingContext';

// Mock catalogueApi and advisorApi
vi.mock('../api/catalogue', () => ({
  catalogueApi: {
    getSummary: vi.fn().mockResolvedValue({
      total_products: 25,
      categories: { Connectivity: 7, Communication: 4 },
      pricing_units: { connection: 8 },
      monthly_price_overall_min: 699,
      monthly_price_overall_max: 12500,
      gstin_required_count: 14,
    }),
  },
}));

vi.mock('../api/advisor', () => ({
  advisorApi: {
    getHealth: vi.fn().mockResolvedValue({
      status: 'HEALTHY',
      llm_provider: 'gemini',
      configured_model: 'gemini-3.1-flash-lite',
    }),
  },
}));

describe('LandingPage Component', () => {
  it('renders hero title and primary value proposition correctly', () => {
    render(
      <OnboardingProvider>
        <BrowserRouter>
          <LandingPage />
        </BrowserRouter>
      </OnboardingProvider>
    );

    expect(screen.getByText(/Your Entire Business, Connected in/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Get business connectivity, communication, cloud and security services/i)
    ).toBeInTheDocument();
  });

  it('renders primary CTAs Get Started and Track My Order', () => {
    render(
      <OnboardingProvider>
        <BrowserRouter>
          <LandingPage />
        </BrowserRouter>
      </OnboardingProvider>
    );

    const getStartedBtn = screen.getByRole('link', { name: /Get Started/i });
    const trackOrderBtn = screen.getByRole('link', { name: /Track My Order/i });

    expect(getStartedBtn).toHaveAttribute('href', '/advisor');
    expect(trackOrderBtn).toHaveAttribute('href', '/track-order');
  });

  it('renders all four customer onboarding journey steps', () => {
    render(
      <OnboardingProvider>
        <BrowserRouter>
          <LandingPage />
        </BrowserRouter>
      </OnboardingProvider>
    );

    expect(screen.getByText('Understand your business')).toBeInTheDocument();
    expect(screen.getByText('Personalized recommendations')).toBeInTheDocument();
    expect(screen.getByText('Complete digital onboarding')).toBeInTheDocument();
    expect(screen.getByText('Track your activation')).toBeInTheDocument();
  });

  it('displays target MSME customer archetypes (Micro Retail and Professional Offices)', () => {
    render(
      <OnboardingProvider>
        <BrowserRouter>
          <LandingPage />
        </BrowserRouter>
      </OnboardingProvider>
    );

    expect(screen.getByText('Micro Retail')).toBeInTheDocument();
    expect(screen.getByText('Professional Offices')).toBeInTheDocument();
  });
});

