import { useCallback, useEffect, useMemo, useState } from 'react'
import TopBar from './components/TopBar'
import Sidebar from './components/Sidebar'
import ChatPane from './components/ChatPane'
import SettingsModal from './components/SettingsModal'
import SignInScreen from './components/SignInScreen'

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
            text: 'Here\u2019s the parametric pass: a 120\u00d780 plate, two 30mm slots on the top face, and a 12mm lip on the rear. The slot length is driven by a single `slot` variable, so you can tune it without breaking the sketch. Drop a hand sketch in and I\u2019ll trace the outline into the model.',
            time: '13:58',
          },
          {
            id: 'm3',
            role: 'user',
            text: 'Let\u2019s make the lip 16mm and add 4mm corner fillets.',
            time: '14:02',
          },
          {
            id: 'm4',
            role: 'assistant',
            text: 'Updated \u2014 lip is now 16mm and all four corners carry R4 fillets. The radius lives in one parameter (`filletR`), so swapping to chamfers is a single edit. Want the STEP export next?',
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
            text: 'A 60mm diameter duct that bends 90\u00b0 to a square flange.',
            time: '12:10',
          },
          {
            id: 'm2',
            role: 'assistant',
            text: 'Laid out: 60mm tube, 90\u00b0 bend with R35 centreline, flanged to a 90\u00d790 plate with four corner holes. The bend radius is the one knob to turn \u2014 everything downstream recomputes from it.',
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
            text: 'Fixed \u2014 centre distance is back to 40mm and the sketch is fully constrained again. Re-exporting FCStd now.',
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
  'Done \u2014 I\u2019ve sketched the first parametric pass. The critical dimensions are exposed as named parameters, so change one value and the whole part recomputes. Want me to lock in tolerances next?',
  'That\u2019s in the model now. I\u2019ve constrained the sketch so the profile won\u2019t break when you edit the overall height. I can also hand you the STEP / FCStd export when you\u2019re ready.',
  'Noted. I\u2019ve added it to the model and re-checked the sketch for under-constraint. The solver is happy. Anything else you want driven by parameters rather than fixed numbers?',
]

function pickReply(text) {
  const t = text.toLowerCase()
  if (t.includes('fillet') || t.includes('radius') || t.includes('chamfer')) {
    return 'Added. The fillet radius is one parameter (`filletR`), so if you want to swap to chamfers it\u2019s a single edit. I kept every other constraint intact so nothing else shifts.'
  }
  if (t.includes('hole') || t.includes('screw') || t.includes('bolt') || t.includes('m8') || t.includes('m6')) {
    return 'The hole pattern is in \u2014 spacing, depth, and clearance are all driven by named parameters. Change `holeØ` once and every instance updates together. Want countersinks?'
  }
  return REPLIES[Math.floor(Math.random() * REPLIES.length)]
}

const nowTime = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

export default function App() {
  const [projects, setProjects] = useState(seed)
  const [activeProjectId, setActiveProjectId] = useState(null)
  const [activeChatId, setActiveChatId] = useState(null)
  const [query, setQuery] = useState('')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [signedOut, setSignedOut] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== 'undefined' ? window.matchMedia('(max-width: 900px)').matches : false,
  )
  const [draftingChatId, setDraftingChatId] = useState(null)
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
    const mq = window.matchMedia('(max-width: 900px)')
    function sync() {
      setIsMobile(mq.matches)
    }
    sync()
    mq.addEventListener?.('change', sync)
    return () => mq.removeEventListener?.('change', sync)
  }, [])

  const closeSettings = useCallback(() => setSettingsOpen(false), [])

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
    // Returns a working (projectId, chatId) pair, creating a chat if none is open.
    let pid = activeProjectId
    if (!pid) pid = projects[0]?.id
    if (!pid) return null
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

  function sendMessage(raw) {
    const text = raw.trim()
    if (!text) return
    const pair = ensureChat()
    if (!pair) return
    const { pid, cid } = pair
    patchChat(pid, cid, (c) => ({
      ...c,
      name:
        c.name === 'New chat'
          ? text.split(/\s+/).slice(0, 5).join(' ') + (text.split(/\s+/).length > 5 ? '\u2026' : '')
          : c.name,
      messages: [...c.messages, { id: uid(), role: 'user', text, time: nowTime() }],
    }))
    setDraftingChatId(cid)
    window.setTimeout(() => {
      patchChat(pid, cid, (c) => ({
        ...c,
        messages: [...c.messages, { id: uid(), role: 'assistant', text: pickReply(text), time: nowTime() }],
      }))
      setDraftingChatId((cur) => (cur === cid ? null : cur))
    }, 1000 + Math.random() * 700)
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

  function handleLogout() {
    setSignedOut(true)
  }

  if (signedOut) {
    return <SignInScreen onSignIn={() => setSignedOut(false)} />
  }

  return (
    <>
      <div className="app-shell" inert={settingsOpen ? '' : undefined}>
      <TopBar
        onToggleSidebar={toggleSidebar}
        theme={theme}
        onToggleTheme={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
        sidebarVisible={isMobile ? sidebarOpen : !sidebarCollapsed}
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
          totalChats={activeProject?.chats.length ?? 0}
          onSelectProject={selectProject}
          onSelectChat={selectChat}
          onNewChat={newChat}
          onNewProject={newProject}
          onOpenSettings={() => setSettingsOpen(true)}
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

      {settingsOpen && <SettingsModal theme={theme} onClose={closeSettings} />}
    </>
  )
}
