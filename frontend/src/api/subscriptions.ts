import api from './client'

export interface SubscriptionObject {
  id: number
  name: string
  object_id: string
  expires_at: string | null
  active: boolean
  days_left: number | null
}

export interface PayResult {
  payment_url: string
  payment_id: string
}

export interface PaymentStatus {
  status: string
  paid: boolean
}

export function listSubscriptions() {
  return api.get<SubscriptionObject[]>('/subscriptions')
}

export function createPayment(object_db_id: number, plan: string) {
  return api.post<PayResult>('/subscriptions/pay', { object_db_id, plan })
}

export function checkPaymentStatus(paymentId: string) {
  return api.get<PaymentStatus>(`/subscriptions/payment-status/${paymentId}`)
}
