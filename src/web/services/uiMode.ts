export type UiMode = 'gear1' | 'gear2'

export function getModeLabel(mode: UiMode): string {
  switch (mode) {
    case 'gear1':
      return 'Gear 1'
    case 'gear2':
      return 'Gear 2'
    default:
      return 'Gear 1'
  }
}

export function shouldUseDeterministicMode(mode: UiMode, input: string): boolean {
  const trimmed = input.trim()
  if (!trimmed) return mode === 'gear1'

  if (trimmed.startsWith('/')) {
    return true
  }

  return mode === 'gear1'
}
