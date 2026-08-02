import { motion } from 'framer-motion'
import { IconGoogle } from '../icons'

/* Official Google branding for the OAuth button. */

export default function GoogleButton({ onClick, loading, label = 'Continue with Google' }) {
  return (
    <motion.button
      type="button"
      whileHover={!loading ? { scale: 1.015 } : undefined}
      whileTap={!loading ? { scale: 0.985 } : undefined}
      className="google-btn"
      onClick={onClick}
      disabled={loading}
      aria-busy={loading}
    >
      <IconGoogle size={18} />
      {loading ? (
        <span className="btn-loading">
          <span className="dots" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          Connecting…
        </span>
      ) : (
        label
      )}
    </motion.button>
  )
}
