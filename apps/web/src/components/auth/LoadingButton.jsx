import { motion } from 'framer-motion'

/* Text-based loading button — never a boring spinner. */

export default function LoadingButton({
  loading,
  loadingText = 'Working…',
  children,
  className = '',
  ...rest
}) {
  return (
    <motion.button
      type="submit"
      whileHover={!loading ? { scale: 1.015 } : undefined}
      whileTap={!loading ? { scale: 0.985 } : undefined}
      className={`auth-submit ${className} ${loading ? 'loading' : ''}`}
      disabled={loading || rest.disabled}
      aria-busy={loading}
      {...rest}
    >
      {loading ? (
        <span className="btn-loading">
          <span className="dots" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          {loadingText}
        </span>
      ) : (
        children
      )}
    </motion.button>
  )
}
