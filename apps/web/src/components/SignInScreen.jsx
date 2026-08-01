import { LogoMark } from './icons'

export default function SignInScreen({ onSignIn }) {
  return (
    <div className="signin">
      <div className="signin-card">
        <LogoMark size={34} />
        <p className="signin-eyebrow mono">You\u2019ve been signed out</p>
        <h1 className="signin-title">The desk is clear.</h1>
        <p className="signin-sub">
          Your projects and threads stay on this machine. Sign back in to pick up where you left off.
        </p>
        <button type="button" className="signin-btn" onClick={onSignIn}>
          Sign back in
        </button>
      </div>
    </div>
  )
}
