import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { OrderTrackerPage } from '../pages/OrderTrackerPage';
import { orderApi } from '../api/orders';

vi.mock('../api/orders', () => ({
  orderApi: {
    trackByReference: vi.fn(),
    advance: vi.fn(),
  },
}));

const mockOrderResponse = {
  order_id: 'ord_12345',
  order_reference: 'UDYAM-ORD-2026-9A8B7C6D',
  quote_reference: 'Q-TEST1234',
  kyc_case_id: 'KYC-2026-TEST01',
  advisor_session_id: 'conv-01',
  current_state: 'ORDER_PROCESSING',
  selected_product_ids: ['P01', 'P03'],
  bundle_tier: 'Growth',
  customer_info: {
    business_name: 'Metro Pharmacy',
    city: 'Chennai',
    segment: 'micro',
  },
  pricing: {
    currency: 'INR',
    monthly_recurring_charges: 1999.0,
    one_time_charges: 1000.0,
    estimated_first_month: 2999.0,
  },
  created_at: '2026-11-05T12:00:00Z',
  updated_at: '2026-11-05T12:05:00Z',
  timeline: [
    {
      event_id: 'evt_1',
      from_state: null,
      to_state: 'QUOTE_CONFIRMED',
      title: 'Order Created & Quote Confirmed',
      description: 'Order initialized with quote Q-TEST1234.',
      timestamp: '2026-11-05T12:00:00Z',
      is_simulated: false,
    },
    {
      event_id: 'evt_2',
      from_state: 'KYC_VERIFIED',
      to_state: 'ORDER_PROCESSING',
      title: 'Order Dispatched for Provisioning (Demo / Simulated)',
      description: 'Provisioning order generated. Allocating IP blocks.',
      timestamp: '2026-11-05T12:05:00Z',
      is_simulated: true,
    },
  ],
  is_simulated_stage: true,
  next_action_prompt: 'Provisioning order generated (Simulated). Site readiness check.',
};

describe('OrderTrackerPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.pushState({}, '', '/');
  });

  it('renders order details, tracking reference, and simulated stage notice', async () => {
    (orderApi.trackByReference as any).mockResolvedValue(mockOrderResponse);

    render(
      <BrowserRouter>
        <OrderTrackerPage />
      </BrowserRouter>
    );

    const input = screen.getByPlaceholderText(/UDYAM-ORD-2026-.../i);
    const trackBtn = screen.getByRole('button', { name: /Track/i });

    fireEvent.change(input, { target: { value: 'UDYAM-ORD-2026-9A8B7C6D' } });
    fireEvent.click(trackBtn);

    await waitFor(() => {
      expect(screen.getByText('UDYAM-ORD-2026-9A8B7C6D')).toBeInTheDocument();
      expect(screen.getByText('Metro Pharmacy')).toBeInTheDocument();
      expect(screen.getByText('ORDER PROCESSING')).toBeInTheDocument();
    });

    // Check simulated stage flag
    expect(screen.getAllByText(/Demo Simulated Stage|Simulated/i).length).toBeGreaterThan(0);

    // Check timeline events
    expect(screen.getByText('Order Created & Quote Confirmed')).toBeInTheDocument();
    expect(
      screen.getByText('Order Dispatched for Provisioning (Demo / Simulated)')
    ).toBeInTheDocument();
  });

  it('handles invalid order reference gracefully with 404 message', async () => {
    (orderApi.trackByReference as any).mockRejectedValue(
      new Error("No order found matching reference 'UDYAM-ORD-INVALID'.")
    );

    render(
      <BrowserRouter>
        <OrderTrackerPage />
      </BrowserRouter>
    );

    const input = screen.getByPlaceholderText(/UDYAM-ORD-2026-.../i);
    const trackBtn = screen.getByRole('button', { name: /Track/i });

    fireEvent.change(input, { target: { value: 'UDYAM-ORD-INVALID' } });
    fireEvent.click(trackBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/No order found matching reference 'UDYAM-ORD-INVALID'/i)
      ).toBeInTheDocument();
    });
  });
});
