import { useCallback, useEffect, useMemo, useState } from 'react'
import { AnimatePresence } from 'framer-motion'
import TopBar from './components/TopBar'
import Sidebar from './components/Sidebar'
import ChatPane from './components/ChatPane'
import SettingsModal from './components/SettingsModal'
import AuthModal from './components/auth/AuthModal'
import { useAuth } from './auth/AuthProvider'

const uid = () => Math.random().toString(36).slice(2, 10)

const seed = [
  {
    id: 'p1',
    name: 'Chassis Rev.3',
    chats: [
      {
        id: 'c1',
        name: 'Mounting bracket',
        messages: [
          {
            id: 'm1',
            role: 'user',
            text: 'Design a mounting bracket for an M8 sensor — a base plate, two slots, and a lip at the back.',
            time: '13:58',
          },
          {
            id: 'm2',
            role: 'assistant',
            text: 'Here’s the parametric pass: a 120×80 plate, two 30mm slots on the top face, and a 12mm lip on the rear. The slot length is driven by a single `slot` variable, so you can tune it without breaking the sketch. Drop a hand sketch in and I’ll trace the outline into the model.',
            time: '13:58',
          },
          {
            id: 'm3',
            role: 'user',
            text: 'Let’s make the lip 16mm and add 4mm corner fillets.',
            time: '14:02',
          },
          {
            id: 'm4',
            role: 'assistant',
            text: 'Updated — lip is now 16mm and all four corners carry R4 fillets. The radius lives in one parameter (`filletR`), so swapping to chamfers is a single edit. Want the STEP export next?',
            time: '14:02',
          },
        ],
      },
      {
        id: 'c2',
        name: 'Cooling duct',
        messages: [
          {
            id: 'm1',
            role: 'user',
            text: 'A 60mm diameter duct that bends 90° to a square flange.',
            time: '12:10',
          },
          {
            id: 'm2',
            role: 'assistant',
            text: 'Laid out: 60mm tube, 90° bend with R35 centreline, flanged to a 90×90 plate with four corner holes. The bend radius is the one knob to turn — everything downstream recomputes from it.',
            time: '12:11',
          },
        ],
      },
      {
        id: 'c3',
        name: 'Base plate fix',
        messages: [
          {
            id: 'm1',
            role: 'user',
            text: 'The M6 holes on the base plate are 0.5mm too close together.',
            time: '11:42',
          },
          {
            id: 'm2',
            role: 'assistant',
            text: 'Fixed — centre distance is back to 40mm and the sketch is fully constrained again. Re-exporting FCStd now.',
            time: '11:42',
          },
        ],
      },
    ],
  },
  {
    id: 'p2',
    name: 'Gearbox housing',
    chats: [
      {
        id: 'c4',
        name: 'Housing shell',
        messages: [
          {
            id: 'm1',
            role: 'user',
            text: 'Start a 2-part housing with a 10mm wall and a split along the shaft axis.',
            time: '10:05',
          },
        ],
      },
      {
        id: 'c5',
        name: 'Bearing seats',
        messages: [
          {
            id: 'm1',
            role: 'user',
            text: 'Seat two 6204 bearings with a 12mm shoulder between them.',
            time: '09:31',
          },
        ],
      },
    ],
  },
]

const REPLIES = [
  'Done — I’ve sketched the first parametric pass. The critical dimensions are exposed as named parameters, so change one value and the whole part recomputes. Want me to lock in tolerances next?',
  'That’s in the model now. I’ve constrained the sketch so the profile won’t break when you edit the overall height. I can also hand you the STEP / FCStd export when you’re ready.',
  'Noted. I’ve added it to the model and re-checked the sketch for under-constraint. The solver is happy. Anything else you want driven by parameters rather than fixed numbers?',
]

function pickReply(text) {
  const t = text.toLowerCase()
  if (t.includes('fillet') || t.includes('radius') || t.includes('chamfer')) {
    return 'Added. The fillet radius is one parameter (`filletR`), so if you want to swap to chamfers it’s a single edit. I kept every other constraint intact so nothing else shifts.'
  }
  if (t.includes('hole') || t.includes('screw') || t.includes('bolt') || t.includes('m8') || t.includes('m6')) {
    return 'The hole pattern is in — spacing, depth, and clearance are all driven by named parameters. Change `holeØ` once and every instance updates together. Want countersinks?'
  }
  return REPLIES[Math.floor(Math.random() * REPLIES.length)]
}

const nowTime = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

export default function App() {
  const { user, recoveryPending, clearRecovery, showToast, signOut, updateProfile, changePassword } = useAuth()
  const [projects, setProjects] = useState(seed)
  const [activeProjectId, setActiveProjectId] = useState(null)
  const [activeChatId, setActiveChatId] = useState(null)
  const [query, setQuery] = useState('')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [authOpen, setAuthOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== 'undefined' ? window.matchMedia('(max-width: 900px)').matches : false,
  )
  const [draftingChatId, setDraftingChatId] = useState(null)

  // Profile — from the auth user when signed in, else the local guest profile.
  const [guestProfile, setGuestProfile] = useState(() => {
    try {
      const stored = window.localStorage.getItem('s2c-profile')
      if (stored) {
        const parsed = JSON.parse(stored)
        if (parsed.name && parsed.email) return parsed
      }
    } catch {
      /* storage unavailable */
    }
    return { name: 'Guest drafter', email: 'guest@sketch2cad.local' }
  })

  const profile = user
    ? { name: user.displayName, email: user.email }
    : guestProfile

  const DEFAULT_PREFS = {
    units: 'Millimetres',
    solver: 'Local Qwen · 4-bit',
    export: 'FreeCAD (.FCStd)',
    alsoStep: true,
    alsoStl: false,
  }
  const [prefs, setPrefs] = useState(() => {
    try {
      const stored = window.localStorage.getItem('s2c-prefs')
      if (stored) return { ...DEFAULT_PREFS, ...JSON.parse(stored) }
    } catch {
      /* storage unavailable */
    }
    return DEFAULT_PREFS
  })
  const [theme, setTheme] = useState(() => {
    let stored = null
    try {
      stored = window.localStorage.getItem('s2c-theme')
    } catch {
      stored = null
    }
    const initial =
      stored === 'dark' || stored === 'light'
        ? stored
        : window.matchMedia('(prefers-color-scheme: dark)').matches
          ? 'dark'
          : 'light'
    document.documentElement.setAttribute('data-theme', initial)
    return initial
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try {
      window.localStorage.setItem('s2c-theme', theme)
    } catch {
      /* storage unavailable */
    }
  }, [theme])

  useEffect(() => {
    try {
      window.localStorage.setItem('s2c-profile', JSON.stringify(guestProfile))
    } catch {
      /* storage unavailable */
    }
  }, [guestProfile])

  useEffect(() => {
    try {
      window.localStorage.setItem('s2c-prefs', JSON.stringify(prefs))
    } catch {
      /* storage unavailable */
    }
  }, [prefs])

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 900px)')
    function sync() {
      setIsMobile(mq.matches)
    }
    sync()
    mq.addEventListener?.('change', sync)
    return () => mq.removeEventListener?.('change', sync)
  }, [])

  const closeSettings = useCallback(() => setSettingsOpen(false), [])

  // A real recovery link opens the auth modal straight into the reset view.
  useEffect(() => {
    if (recoveryPending) {
      setAuthOpen(true)
    }
  }, [recoveryPending])

  // Shared links (#/share/...) resolve to a lightweight confirmable page later;
  // for now keep the app fully usable.

  const activeProject = projects.find((p) => p.id === activeProjectId) ?? null
  const activeChat =
    activeProject?.chats.find((c) => c.id === activeChatId) ?? null

  const filteredProjects = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return projects
    return projects.filter((p) => p.name.toLowerCase().includes(q))
  }, [query, projects])

  const filteredChats = useMemo(() => {
    if (!activeProject) return []
    const q = query.trim().toLowerCase()
    if (!q) return activeProject.chats
    return activeProject.chats.filter((c) => c.name.toLowerCase().includes(q))
  }, [query, activeProject])

  function patchChat(pid, cid, fn) {
    setProjects((prev) =>
      prev.map((p) =>
        p.id === pid
          ? { ...p, chats: p.chats.map((c) => (c.id === cid ? fn(c) : c)) }
          : p,
      ),
    )
  }

  function ensureChat() {
    let pid = activeProjectId
    if (!pid) pid = projects[0]?.id
    if (!pid) {
      const project = { id: uid(), name: 'New project 1', chats: [] }
      pid = project.id
      setProjects((prev) => (prev.length ? prev : [project]))
      setActiveProjectId(pid)
    }
    let cid = activeChatId
    if (!cid || !projects.find((p) => p.id === pid)?.chats.some((c) => c.id === cid)) {
      const chat = { id: uid(), name: 'New chat', messages: [] }
      cid = chat.id
      setProjects((prev) =>
        prev.map((p) => (p.id === pid ? { ...p, chats: [chat, ...p.chats] } : p)),
      )
      setActiveProjectId(pid)
      setActiveChatId(cid)
    }
    return { pid, cid }
  }

  function sendMessage(raw, attachments = []) {
    const text = raw.trim()
    if (!text && attachments.length === 0) return false
    const pair = ensureChat()
    if (!pair) return false
    const { pid, cid } = pair
    patchChat(pid, cid, (c) => ({
      ...c,
      name:
        c.name === 'New chat'
          ? (text || 'Sketch').split(/\s+/).slice(0, 5).join(' ') +
            ((text || 'Sketch').split(/\s+/).length > 5 ? '…' : '')
          : c.name,
      messages: [...c.messages, { id: uid(), role: 'user', text, attachments, time: nowTime() }],
    }))
    setDraftingChatId(cid)
    window.setTimeout(() => {
      patchChat(pid, cid, (c) => ({
        ...c,
        messages: [...c.messages, { id: uid(), role: 'assistant', text: pickReply(text), time: nowTime() }],
      }))
      setDraftingChatId((cur) => (cur === cid ? null : cur))
    }, 1000 + Math.random() * 700)
    return true
  }

  function newChat() {
    const pid = activeProjectId ?? projects[0]?.id
    if (!pid) return
    const chat = { id: uid(), name: 'New chat', messages: [] }
    setProjects((prev) =>
      prev.map((p) => (p.id === pid ? { ...p, chats: [chat, ...p.chats] } : p)),
    )
    setActiveProjectId(pid)
    setActiveChatId(chat.id)
    setQuery('')
  }

  function newProject() {
    const count = projects.filter((p) => /^New project \d+$/.test(p.name)).length
    const project = {
      id: uid(),
      name: `New project ${count + 1}`,
      chats: [],
    }
    setProjects((prev) => [project, ...prev])
    setActiveProjectId(project.id)
    setActiveChatId(null)
    setQuery('')
    setSidebarCollapsed(false)
  }

  function renameProject(id, name) {
    const n = name.trim()
    if (!n) return
    setProjects((prev) => prev.map((p) => (p.id === id ? { ...p, name: n } : p)))
  }

  function deleteProject(id) {
    setProjects((prev) => prev.filter((p) => p.id !== id))
    if (activeProjectId === id) {
      setActiveProjectId(null)
      setActiveChatId(null)
    }
  }

  function renameChat(id, name) {
    const n = name.trim()
    if (!n) return
    setProjects((prev) =>
      prev.map((p) =>
        p.id === activeProjectId
          ? { ...p, chats: p.chats.map((c) => (c.id === id ? { ...c, name: n } : c)) }
          : p,
      ),
    )
  }

  function deleteChat(id) {
    setProjects((prev) =>
      prev.map((p) =>
        p.id === activeProjectId
          ? { ...p, chats: p.chats.filter((c) => c.id !== id) }
          : p,
      ),
    )
    if (activeChatId === id) setActiveChatId(null)
  }

  function selectProjectAndExpand(id) {
    selectProject(id)
    setSidebarCollapsed(false)
  }

  function expandSidebar() {
    if (isMobile) {
      setSidebarOpen(true)
    } else {
      setSidebarCollapsed(false)
    }
  }

  function selectChat(id) {
    setActiveChatId(id)
    setQuery('')
    setSidebarOpen(false)
  }

  function selectProject(id) {
    if (id === activeProjectId) return
    setActiveProjectId(id)
    setActiveChatId(null)
    setQuery('')
  }

  function toggleSidebar() {
    if (isMobile) {
      setSidebarOpen((v) => !v)
    } else {
      setSidebarCollapsed((v) => !v)
    }
  }

  async function handleLogout() {
    setSettingsOpen(false)
    await signOut()
    showToast('Signed out — the desk is still here.')
  }

  function handleProfileChange(patch) {
    if (user && patch.name && patch.name !== user.displayName) {
      updateProfile({ displayName: patch.name }).catch(() => {
        showToast('Could not update profile', { tone: 'err' })
      })
    }
    setGuestProfile((prev) => ({ ...prev, ...patch }))
  }

  async function copyLink(link) {
    try {
      await navigator.clipboard.writeText(link)
      return true
    } catch {
      try {
        const ta = document.createElement('textarea')
        ta.value = link
        ta.style.position = 'fixed'
        ta.style.opacity = '0'
        document.body.appendChild(ta)
        ta.select()
        const ok = document.execCommand('copy')
        document.body.removeChild(ta)
        return ok
      } catch {
        return false
      }
    }
  }

  function shareUrl(kind, id, name) {
    const base = typeof window !== 'undefined' ? window.location.origin : 'https://sketch2cad.local'
    const slug = name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40) || 'item'
    return `${base}/#/share/${kind}/${id}/${slug}`
  }

  async function shareProject(id, name) {
    const ok = await copyLink(shareUrl('project', id, name))
    showToast(ok ? 'Project link copied — paste it anywhere' : 'Could not copy link — try again', { tone: ok ? 'ok' : 'err' })
  }

  async function shareChat(id, name) {
    const ok = await copyLink(shareUrl('chat', id, name))
    showToast(ok ? 'Chat link copied — paste it anywhere' : 'Could not copy link — try again', { tone: ok ? 'ok' : 'err' })
  }

  return (
    <>
      <div className="app-shell" inert={settingsOpen || authOpen ? '' : undefined}>
        <TopBar
          onToggleSidebar={toggleSidebar}
          theme={theme}
          onToggleTheme={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
          sidebarVisible={isMobile ? sidebarOpen : !sidebarCollapsed}
          user={user}
          onOpenAuth={() => setAuthOpen(true)}
          onOpenSettings={() => setSettingsOpen(true)}
          onLogout={handleLogout}
        />

        <div className={`main-row ${sidebarCollapsed && !isMobile ? 'collapsed' : ''}`}>
          <Sidebar
            projects={projects}
            filteredProjects={filteredProjects}
            activeProject={activeProject}
            activeProjectId={activeProjectId}
            activeChatId={activeChatId}
            filteredChats={filteredChats}
            query={query}
            onQuery={setQuery}
            profile={profile}
            signedIn={Boolean(user)}
            totalChats={activeProject?.chats.length ?? 0}
            onSelectProject={selectProject}
            onSelectChat={selectChat}
            onNewChat={newChat}
            onNewProject={newProject}
            onRenameProject={renameProject}
            onDeleteProject={deleteProject}
            onShareProject={shareProject}
            onRenameChat={renameChat}
            onDeleteChat={deleteChat}
            onShareChat={shareChat}
            onOpenSettings={() => setSettingsOpen(true)}
            onOpenAuth={() => setAuthOpen(true)}
            onLogout={handleLogout}
            open={sidebarOpen}
            collapsed={isMobile ? false : sidebarCollapsed}
            isMobile={isMobile}
            onClose={() => setSidebarOpen(false)}
            onExpand={expandSidebar}
            onSelectProjectRail={selectProjectAndExpand}
          />

          <main className="pane">
            <ChatPane
              chat={activeChat}
              drafting={draftingChatId === activeChatId}
              onSend={sendMessage}
            />
          </main>
        </div>
      </div>

      {settingsOpen && (
        <SettingsModal
          theme={theme}
          onToggleTheme={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
          profile={profile}
          signedIn={Boolean(user)}
          onProfileChange={handleProfileChange}
          onChangePassword={async (current, next) => {
            await changePassword(current, next)
            showToast('Password updated.')
          }}
          onLogout={handleLogout}
          prefs={prefs}
          onPrefsChange={setPrefs}
          onClose={closeSettings}
        />
      )}

      <AnimatePresence>
        {authOpen && (
          <AuthModal
            initialView={recoveryPending ? 'reset' : 'login'}
            onClose={() => {
              setAuthOpen(false)
              clearRecovery()
            }}
          />
        )}
      </AnimatePresence>
    </>
  )
}
