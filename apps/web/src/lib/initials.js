/* Shared avatar-initials helper. */

export default function initials(name) {
  return (
    (name || '?')
      .trim()
      .split(/\s+/)
      .map((w) => w[0])
      .slice(0, 2)
      .join('')
      .toUpperCase() || '?'
  )
}
