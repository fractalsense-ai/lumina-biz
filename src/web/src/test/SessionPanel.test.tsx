import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'

import { SessionPanel, type SessionPanelProps } from '../../components/sidebar/SessionPanel'
import type { TranscriptStore, SessionSummary, StoredSession } from '../../services/transcriptStore'

function makeStore(sessions: SessionSummary[]): TranscriptStore {
  return {
    listSessions: vi.fn().mockResolvedValue(sessions),
    saveSession: vi.fn().mockResolvedValue(undefined),
    loadSession: vi.fn().mockResolvedValue(null),
    deleteSession: vi.fn().mockResolvedValue(undefined),
  }
}

function makeSummary(overrides: Partial<SessionSummary> = {}): SessionSummary {
  return {
    sessionId: `sess-${Date.now()}`,
    turnCount: 3,
    updatedAt: Date.now(),
    domainId: 'domain/bizops/auto-repair/v1',
    ...overrides,
  }
}

describe('SessionPanel delete gating', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('shows delete button for Student Commons sessions', async () => {
    const sessions = [
      makeSummary({
        sessionId: 'commons-1',
        moduleId: 'domain/bizops/auto-repair/v1',
        label: 'Operations Hub',
      }),
    ]
    const store = makeStore(sessions)
    const onDelete = vi.fn()

    render(
      <SessionPanel
        store={store}
        activeSessionId={null}
        onSelect={vi.fn()}
        onNew={vi.fn()}
        onDelete={onDelete}
      />,
    )

    // Wait for session list to render
    const deleteBtn = await screen.findByTitle('Delete conversation')
    expect(deleteBtn).toBeDefined()
  })

  it('shows delete button for sessions with no moduleId', async () => {
    const sessions = [
      makeSummary({
        sessionId: 'legacy-1',
        moduleId: undefined,
        label: 'Legacy chat',
      }),
    ]
    const store = makeStore(sessions)

    render(
      <SessionPanel
        store={store}
        activeSessionId={null}
        onSelect={vi.fn()}
        onNew={vi.fn()}
        onDelete={vi.fn()}
      />,
    )

    const deleteBtn = await screen.findByTitle('Delete conversation')
    expect(deleteBtn).toBeDefined()
  })

  it('shows lock icon instead of delete for learning module sessions', async () => {
    const sessions = [
      makeSummary({
        sessionId: 'prealg-1',
        moduleId: 'domain/bizops/field-audit/v1',
        label: 'Field Audit',
      }),
    ]
    const store = makeStore(sessions)

    render(
      <SessionPanel
        store={store}
        activeSessionId={null}
        onSelect={vi.fn()}
        onNew={vi.fn()}
        onDelete={vi.fn()}
      />,
    )

    const lockIcon = await screen.findByTitle('Learning module — deletion requires teacher approval')
    expect(lockIcon).toBeDefined()

    // Delete button should NOT be present
    expect(screen.queryByTitle('Delete conversation')).toBeNull()
  })

  it('mixed sessions: deletable commons + locked learning module', async () => {
    const sessions = [
      makeSummary({
        sessionId: 'commons-2',
        moduleId: 'domain/bizops/auto-repair/v1',
        label: 'Operations Hub',
      }),
      makeSummary({
        sessionId: 'alg-1',
        moduleId: 'domain/bizops/field-audit/v1',
        label: 'Field Audit',
      }),
    ]
    const store = makeStore(sessions)

    render(
      <SessionPanel
        store={store}
        activeSessionId={null}
        onSelect={vi.fn()}
        onNew={vi.fn()}
        onDelete={vi.fn()}
      />,
    )

    // One delete button (commons) and one lock icon (algebra)
    const deleteBtn = await screen.findByTitle('Delete conversation')
    expect(deleteBtn).toBeDefined()

    const lockIcon = await screen.findByTitle('Learning module — deletion requires teacher approval')
    expect(lockIcon).toBeDefined()
  })
})
