import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Login from '../pages/Login'

const mockAuth = { user: null, login: vi.fn() }
vi.mock('../context/AuthContext', () => ({ useAuth: () => mockAuth }))

async function fillAndSubmit() {
  render(<MemoryRouter><Login /></MemoryRouter>)
  await userEvent.type(screen.getByLabelText('Email'), 'a@b.co')
  await userEvent.type(screen.getByLabelText('Password'), 'secret-password')
  await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
}

describe('Login', () => {
  beforeEach(() => mockAuth.login.mockReset())

  it('shows the server error message on failure', async () => {
    mockAuth.login.mockRejectedValue(new Error('Invalid email or password.'))
    await fillAndSubmit()
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.')
  })

  it('submits the entered credentials', async () => {
    mockAuth.login.mockResolvedValue({})
    await fillAndSubmit()
    await waitFor(() => expect(mockAuth.login).toHaveBeenCalledWith('a@b.co', 'secret-password'))
  })
})
