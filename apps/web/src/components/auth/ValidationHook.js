import { useEffect, useRef, useState } from 'react'

/* Debounced email validation while typing.
   status: 'idle' | 'invalid' | 'checking' | 'exists' | 'available' */

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

export function useEmailValidation(checkEmail) {
  const [value, setValue] = useState('')
  const [status, setStatus] = useState('idle')
  const timer = useRef(null)
  const latest = useRef('')

  useEffect(() => {
    return () => window.clearTimeout(timer.current)
  }, [])

  function onChange(next) {
    setValue(next)
    window.clearTimeout(timer.current)
    latest.current = next
    const trimmed = next.trim()

    if (!trimmed) {
      setStatus('idle')
      return
    }
    if (!EMAIL_RE.test(trimmed)) {
      setStatus('invalid')
      return
    }
    setStatus('checking')
    timer.current = window.setTimeout(async () => {
      try {
        const res = await checkEmail(trimmed)
        if (latest.current === next) setStatus(res?.status === 'exists' ? 'exists' : 'available')
      } catch {
        if (latest.current === next) setStatus('available')
      }
    }, 450)
  }

  return {
    value,
    onChange,
    status,
    isValid: status === 'available',
    hasValidFormat: status === 'available' || status === 'exists' || status === 'checking',
  }
}
