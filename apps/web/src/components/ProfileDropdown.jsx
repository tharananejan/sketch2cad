import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { IconChevron, IconSettings, IconLogout } from './icons'
import initials from '../lib/initials'

export default function ProfileDropdown({ user, onOpenSettings, onLogout }) {
  const [open, setOpen] = useState(false)
  const wrapRef = useRef(null)

  useEffect(() => {
    function onDown(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false)
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onDown)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onDown)
    }
  }, [])

  if (!user) return null

  return (
    <div
      className="profile-drop-wrap"
      ref={wrapRef}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className="profile-drop-btn"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Account menu for ${user.displayName}`}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="avatar">{initials(user.displayName)}</span>
        <IconChevron className={`chev ${open ? 'open' : ''}`} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            className="profile-drop"
            role="menu"
            aria-label="Account"
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.98 }}
            transition={{ duration: 0.14, ease: 'easeOut' }}
          >
            <div className="profile-drop-head">
              <span className="avatar avatar-lg">{initials(user.displayName)}</span>
              <div>
                <p className="profile-name">{user.displayName}</p>
                <p className="profile-mail mono">{user.email}</p>
              </div>
            </div>
            <div className="menu-rule" />
            <button
              type="button"
              role="menuitem"
              className="menu-item"
              onClick={() => {
                setOpen(false)
                onOpenSettings()
              }}
            >
              <IconSettings size={16} />
              Settings
            </button>
            <button
              type="button"
              role="menuitem"
              className="menu-item danger"
              onClick={() => {
                setOpen(false)
                onLogout()
              }}
            >
              <IconLogout size={16} />
              Logout
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
