import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { DataUnavailable, ErrorState } from '../components/StateViews'
import TrustLegend from '../components/TrustLegend'

describe('state views', () => {
  it('distinguishes offline errors from other failures', () => {
    render(<ErrorState error={{ code: 'network', message: 'down' }} />)
    expect(screen.getByRole('alert')).toHaveTextContent('You appear to be offline')
  })
  it('data-unavailable never claims safety', () => {
    render(<DataUnavailable>Nothing imported.</DataUnavailable>)
    expect(screen.getByText('No data available yet')).toBeInTheDocument()
  })
  it('legend states that no report does not mean safe', () => {
    render(<TrustLegend />)
    expect(screen.getByText(/does not mean the road is safe/i)).toBeInTheDocument()
  })
})
