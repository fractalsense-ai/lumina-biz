import { describe, expect, it } from 'vitest'

import { getModeLabel, shouldUseDeterministicMode } from '@/services/uiMode'

describe('dual mode UI', () => {
  it('labels the deterministic mode as Gear 1', () => {
    expect(getModeLabel('gear1')).toBe('Gear 1')
  })

  it('labels the assistant mode as Gear 2', () => {
    expect(getModeLabel('gear2')).toBe('Gear 2')
  })

  it('forces slash-only deterministic routing in Gear 1', () => {
    expect(shouldUseDeterministicMode('gear1', 'hello world')).toBe(true)
    expect(shouldUseDeterministicMode('gear1', '/help')).toBe(true)
  })

  it('allows normal AI routing in Gear 2', () => {
    expect(shouldUseDeterministicMode('gear2', 'hello world')).toBe(false)
    expect(shouldUseDeterministicMode('gear2', '/help')).toBe(true)
  })
})
