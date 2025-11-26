import { useEffect, useState } from 'react'
import { teamService } from '../services/team'
import { authService } from '../services/auth'
import { AgentType, AgentPriority } from '../constants/apiConstants'

function TeamManagement() {
  const [teams, setTeams] = useState([])
  const [selectedTeam, setSelectedTeam] = useState(null)
  const [members, setMembers] = useState([])
  const [permissions, setPermissions] = useState([])
  const [primaryAgents, setPrimaryAgents] = useState([])
  const [secondaryAgents, setSecondaryAgents] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [newTeam, setNewTeam] = useState({ name: '', description: '' })
  const [editMode, setEditMode] = useState(false)
  const [editData, setEditData] = useState({})
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(false)

  // Modal states
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showPermissionModal, setShowPermissionModal] = useState(false)
  const [showPromoteModal, setShowPromoteModal] = useState(false)
  const [allUsers, setAllUsers] = useState([])
  const [assignData, setAssignData] = useState({ userId: '', isTeamLead: false })
  const [agentData, setAgentData] = useState({ agent_type: AgentType.OBSERVABILITY_AGENT, priority: AgentPriority.PRIMARY })
  const [selectedMember, setSelectedMember] = useState(null)

  useEffect(() => {
    loadTeams()
    loadAllUsers()
  }, [])

  const loadAllUsers = async () => {
    try {
      const users = await authService.getAllUsers()
      setAllUsers(users)
    } catch (error) {
      console.error('Failed to load users:', error)
    }
  }

  const loadTeams = async () => {
    try {
      const data = await teamService.getAllTeams()
      setTeams(data)
    } catch (error) {
      console.error('Failed to load teams:', error)
    }
  }

  const selectTeam = async (team) => {
    try {
      setSelectedTeam(team)
      const mem = await teamService.getTeamMembers(team.id)
      setMembers(mem)
      setPermissions([])
      const [prim, sec] = await Promise.all([
        teamService.getTeamAgents(team.id, AgentPriority.PRIMARY),
        teamService.getTeamAgents(team.id, AgentPriority.SECONDARY)
      ])
      setPrimaryAgents(prim)
      setSecondaryAgents(sec)
      setShowCreate(false)
      setEditMode(false)
      setEditData({})
      setMessage(null)
    } catch (error) {
      console.error('Failed to select team:', error)
    }
  }

  const handleCreate = async () => {
    if (!newTeam.name.trim()) return
    setLoading(true)
    try {
      await teamService.createTeam(newTeam)
      setMessage({ type: 'success', text: `Team "${newTeam.name}" created successfully.` })
      setNewTeam({ name: '', description: '' })
      setShowCreate(false)
      loadTeams()
    } catch (e) {
      setMessage({ type: 'error', text: e.response?.data?.detail || 'Failed to create team' })
    } finally {
      setLoading(false)
    }
  }

  const handleUpdate = async () => {
    if (!selectedTeam) return
    setLoading(true)
    try {
      const updated = await teamService.updateTeam(selectedTeam.id, editData)
      setMessage({ type: 'success', text: 'Team updated successfully.' })
      setEditMode(false)
      selectTeam(updated)
      loadTeams()
    } catch (e) {
      setMessage({ type: 'error', text: e.response?.data?.detail || 'Failed to update team' })
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedTeam) return
    if (!window.confirm(`Are you sure you want to delete team "${selectedTeam.name}"?`)) return
    setLoading(true)
    try {
      await teamService.deleteTeam(selectedTeam.id)
      setMessage({ type: 'success', text: 'Team deleted successfully.' })
      setSelectedTeam(null)
      setMembers([])
      setPermissions([])
      loadTeams()
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to delete team' })
    } finally {
      setLoading(false)
    }
  }

  const handleAssign = async () => {
    if (!selectedTeam || !assignData.userId) return
    setLoading(true)
    try {
      await teamService.assignUserToTeam(selectedTeam.id, { 
        user_id: assignData.userId, 
        team_id: selectedTeam.id,
        is_team_lead: assignData.isTeamLead 
      })
      setMessage({ type: 'success', text: `User assigned ${assignData.isTeamLead ? 'as Team Lead' : 'to team'} successfully.` })
      setShowAssignModal(false)
      setAssignData({ userId: '', isTeamLead: false })
      selectTeam(selectedTeam)
    } catch (e) {
      setMessage({ type: 'error', text: e.response?.data?.detail || 'Failed to assign user' })
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = async (userId) => {
    if (!selectedTeam) return
    if (!window.confirm('Are you sure you want to remove this user from the team?')) return
    setLoading(true)
    try {
      await teamService.removeUserFromTeam(selectedTeam.id, userId)
      setMessage({ type: 'success', text: 'User removed successfully.' })
      selectTeam(selectedTeam)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to remove user' })
    } finally {
      setLoading(false)
    }
  }

  const handleAssignAgent = async () => {
    if (!selectedTeam) return
    setLoading(true)
    try {
      await teamService.assignTeamAgent(selectedTeam.id, {
        team_id: selectedTeam.id,
        agent_type: agentData.agent_type,
        priority: agentData.priority
      })
      setMessage({ type: 'success', text: 'Agent assigned successfully.' })
      setShowPermissionModal(false)
      setAgentData({ agent_type: AgentType.OBSERVABILITY_AGENT, priority: AgentPriority.PRIMARY })
      selectTeam(selectedTeam)
    } catch (e) {
      setMessage({ type: 'error', text: e.response?.data?.detail || 'Failed to assign agent' })
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveAgent = async (agentId) => {
    if (!selectedTeam) return
    if (!window.confirm('Are you sure you want to remove this agent assignment?')) return
    setLoading(true)
    try {
      await teamService.removeTeamAgent(selectedTeam.id, agentId)
      setMessage({ type: 'success', text: 'Agent removed successfully.' })
      selectTeam(selectedTeam)
    } catch (e) {
      setMessage({ type: 'error', text: e.response?.data?.detail || 'Failed to remove agent' })
    } finally {
      setLoading(false)
    }
  }

  const handlePromoteToLead = async () => {
    if (!selectedTeam || !selectedMember) return
    setLoading(true)
    try {
      await teamService.promoteToTeamLead(selectedTeam.id, selectedMember.user_id)
      setMessage({ type: 'success', text: `${selectedMember.username} promoted to Team Lead successfully.` })
      setShowPromoteModal(false)
      setSelectedMember(null)
      selectTeam(selectedTeam)
    } catch (e) {
      setMessage({ type: 'error', text: e.response?.data?.detail || 'Failed to promote user' })
    } finally {
      setLoading(false)
    }
  }

  // Helper function to get button classes
  const getTeamButtonClass = (isSelected) => {
    const baseClass = "w-full rounded-lg border p-4 text-left transition-all"
    const selectedClass = isSelected 
      ? "border-blue-500 bg-blue-900/50 shadow-sm dark:border-blue-400 dark:bg-blue-50"
      : "border-gray-700 bg-gray-800 hover:border-gray-600 hover:bg-gray-700 dark:border-gray-200 dark:bg-white dark:hover:border-gray-300 dark:hover:bg-gray-50"
    return `${baseClass} ${selectedClass}`
  }

  const getTeamNameClass = (isSelected) => {
    return isSelected 
      ? "font-semibold text-blue-100 dark:text-blue-900"
      : "font-semibold text-white dark:text-gray-900"
  }

  const getMemberCountClass = (isSelected) => {
    const baseClass = "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium"
    const selectedClass = isSelected
      ? "border-blue-500 bg-blue-800 text-blue-200 dark:border-blue-300 dark:bg-blue-100 dark:text-blue-800"
      : "border-gray-600 bg-gray-700 text-gray-300 dark:border-gray-300 dark:bg-gray-100 dark:text-gray-700"
    return `${baseClass} ${selectedClass}`
  }

  const getMessageClass = (type) => {
    const baseClass = "mb-4 flex items-center justify-between rounded-lg border p-4"
    const typeClass = type === 'success'
      ? "border-green-200 bg-green-50 text-green-800 dark:border-green-700 dark:bg-green-900/30 dark:text-green-300"
      : "border-red-200 bg-red-50 text-red-800 dark:border-red-700 dark:bg-red-900/30 dark:text-red-300"
    return `${baseClass} ${typeClass}`
  }

  const getPriorityButtonClass = (isSelected) => {
    const baseClass = "cursor-pointer rounded-lg border p-3 transition-all"
    const selectedClass = isSelected
      ? "border-yellow-400 bg-yellow-50 dark:border-yellow-600 dark:bg-yellow-900/30"
      : "border-gray-300 bg-white hover:border-gray-400 dark:border-gray-600 dark:bg-gray-700 dark:hover:border-gray-500"
    return `${baseClass} ${selectedClass}`
  }

  const getSecondaryPriorityClass = (isSelected) => {
    const baseClass = "cursor-pointer rounded-lg border p-3 transition-all"
    const selectedClass = isSelected
      ? "border-blue-400 bg-blue-50 dark:border-blue-600 dark:bg-blue-900/30"
      : "border-gray-300 bg-white hover:border-gray-400 dark:border-gray-600 dark:bg-gray-700 dark:hover:border-gray-500"
    return `${baseClass} ${selectedClass}`
  }

  return (
    <div className="h-full w-full overflow-y-auto custom-scrollbar pr-2">
      <div className="mx-auto max-w-7xl flex flex-col gap-6">
        <header className="glass-panel relative overflow-hidden rounded-3xl border border-white/10 px-8 py-10 text-white">
          <div className="relative z-10 flex flex-col gap-3">
            <p className="text-xs font-semibold tracking-[0.4em] text-kaiops-primary">TEAM MANAGEMENT</p>
            <h1 className="text-4xl font-black tracking-tight">Manage Teams & Resources</h1>
            <p className="max-w-2xl text-sm text-slate-300">
              Create teams, assign members, configure agents, and manage permissions across your operational groups.
            </p>
          </div>
          <div className="pointer-events-none absolute right-0 top-0 h-full w-1/2 opacity-40" style={{ background: 'radial-gradient(circle at top, rgba(112,0,255,0.35), transparent 55%)' }} />
        </header>

        <div className="flex gap-6 flex-1">
          {/* Sidebar - Team List */}
          <div className="hidden xl:flex w-80 flex-shrink-0 flex-col glass-panel rounded-3xl border border-white/10 p-6 shadow-xl">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-black text-white">Teams</h2>
                <p className="text-xs text-slate-400 mt-1">{teams.length} team{teams.length !== 1 ? 's' : ''}</p>
              </div>
              <button
                onClick={() => setShowCreate(!showCreate)}
                className="rounded-lg bg-gradient-to-r from-kaiops-primary/40 to-kaiops-secondary/40 px-4 py-2 text-sm font-semibold text-white transition hover:from-kaiops-primary/50 hover:to-kaiops-secondary/50"
              >
                {showCreate ? '✕' : '+ New'}
              </button>
            </div>

            {showCreate && (
              <div className="mb-6 glass-card rounded-xl border border-kaiops-primary/30 bg-kaiops-primary/10 p-4 space-y-4">
                <h3 className="text-sm font-semibold text-kaiops-primary">Create New Team</h3>
                <input
                  placeholder="Team name *"
                  value={newTeam.name}
                  onChange={e => setNewTeam({ ...newTeam, name: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white placeholder-slate-400 focus:border-kaiops-primary/50 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
                />
                <textarea
                  placeholder="Description (optional)"
                  value={newTeam.description || ''}
                  onChange={e => setNewTeam({ ...newTeam, description: e.target.value })}
                  rows={3}
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white placeholder-slate-400 focus:border-kaiops-primary/50 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
                />
                <button
                  onClick={handleCreate}
                  disabled={loading || !newTeam.name.trim()}
                  className="w-full rounded-lg bg-gradient-to-r from-kaiops-primary/40 to-kaiops-secondary/40 px-4 py-2.5 text-sm font-semibold text-white transition hover:from-kaiops-primary/50 hover:to-kaiops-secondary/50 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Team'}
                </button>
              </div>
            )}

            <div className="flex-1 space-y-2 overflow-auto">
              {teams.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="mb-3 text-4xl">📦</div>
                  <p className="text-sm font-medium text-slate-300">No teams yet</p>
                  <p className="text-xs text-slate-500 mt-1">Create your first team to get started</p>
                </div>
              ) : (
                teams.map((t, idx) => (
                  <button
                    key={t.id || `team-${idx}`}
                    onClick={() => selectTeam(t)}
                    className={`w-full text-left rounded-xl border p-4 transition-all ${
                      selectedTeam?.id === t.id
                        ? 'border-kaiops-primary/50 bg-kaiops-primary/20 shadow-lg'
                        : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className={`font-semibold ${selectedTeam?.id === t.id ? 'text-kaiops-primary' : 'text-white'}`}>
                          {t.name}
                        </p>
                        {t.description && (
                          <p className="mt-1 line-clamp-2 text-xs text-slate-400">
                            {t.description}
                          </p>
                        )}
                        <p className={`mt-2 text-xs ${selectedTeam?.id === t.id ? 'text-kaiops-primary/80' : 'text-slate-500'}`}>
                          👥 {t.member_count}
                        </p>
                      </div>
                      {selectedTeam?.id === t.id && <div className="text-kaiops-primary ml-2">✓</div>}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 glass-panel rounded-3xl border border-white/10 p-8 shadow-xl overflow-hidden flex flex-col">
            {message && (
              <div className={`glass-card rounded-xl border p-4 mb-6 flex items-center justify-between text-sm ${
                message.type === 'success'
                  ? 'border-emerald-400/40 bg-emerald-500/20'
                  : 'border-rose-400/40 bg-rose-500/20'
              }`}>
                <div className="flex items-center gap-2 text-white">
                  <span>{message.type === 'success' ? '✅' : '❌'}</span>
                  <span className="font-medium">{message.text}</span>
                </div>
                <button 
                  onClick={() => setMessage(null)} 
                  className="ml-4 rounded-lg px-2 py-1 font-bold transition hover:bg-white/10 text-white"
                >
                  ✕
                </button>
              </div>
            )}

            {!selectedTeam ? (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <div className="mb-4 text-6xl">🎯</div>
                <p className="mb-2 text-xl font-black text-white">Select a Team</p>
                <p className="text-sm text-slate-400">Choose a team from the sidebar to view and manage its details</p>
              </div>
            ) : (
              <div className="flex flex-col gap-6 overflow-auto">
                {/* Team Header */}
                <div className="glass-card rounded-2xl border border-white/10 p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4">
                        <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-kaiops-primary/40 to-kaiops-secondary/40 text-2xl">
                          👥
                        </div>
                        <div>
                          <h2 className="text-2xl font-black text-white">{selectedTeam.name}</h2>
                          <p className="mt-1 text-sm text-slate-300">
                            {selectedTeam.description || 'No description provided'}
                          </p>
                        </div>
                      </div>
                      <div className="mt-4 flex flex-wrap items-center gap-3">
                        <span className="inline-flex items-center rounded-lg border border-emerald-400/40 bg-emerald-500/20 px-3 py-1.5 text-sm font-semibold text-emerald-300">
                          👥 {members.length} Member{members.length !== 1 ? 's' : ''}
                        </span>
                        <span className="inline-flex items-center rounded-lg border border-indigo-400/40 bg-indigo-500/20 px-3 py-1.5 text-sm font-semibold text-indigo-300">
                          🎛️ {primaryAgents.length} Primary · {secondaryAgents.length} Secondary
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => { 
                          setEditMode(!editMode); 
                          setEditData({ name: selectedTeam.name, description: selectedTeam.description }) 
                        }}
                        className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-300 transition hover:bg-white/10"
                      >
                        {editMode ? '✕' : '✏️ Edit'}
                      </button>
                      <button
                        onClick={handleDelete}
                        disabled={loading}
                        className="rounded-lg border border-rose-400/40 bg-rose-500/20 px-4 py-2 text-sm font-semibold text-rose-300 transition hover:bg-rose-500/30 disabled:opacity-50"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                </div>

                {editMode && (
                  <div className="glass-card rounded-xl border border-kaiops-primary/30 bg-kaiops-primary/10 p-5 space-y-4">
                    <h3 className="text-sm font-semibold text-kaiops-primary">Edit Team Details</h3>
                    <div>
                      <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-slate-300">
                        Team Name *
                      </label>
                      <input
                        placeholder="Enter team name"
                        value={editData.name || ''}
                        onChange={e => setEditData({ ...editData, name: e.target.value })}
                        className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white placeholder-slate-400 focus:border-kaiops-primary/50 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
                      />
                    </div>
                    <div>
                      <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-slate-300">
                        Description
                      </label>
                      <textarea
                        placeholder="Enter team description"
                        value={editData.description || ''}
                        onChange={e => setEditData({ ...editData, description: e.target.value })}
                        rows={3}
                        className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white placeholder-slate-400 focus:border-kaiops-primary/50 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
                      />
                    </div>
                    <button
                      onClick={handleUpdate}
                      disabled={loading || !editData.name?.trim()}
                      className="w-full rounded-lg bg-gradient-to-r from-kaiops-primary/40 to-kaiops-secondary/40 px-4 py-2.5 text-sm font-semibold text-white transition hover:from-kaiops-primary/50 hover:to-kaiops-secondary/50 disabled:opacity-50"
                    >
                      {loading ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                )}

                {/* Members Section */}
                <div className="glass-card rounded-2xl border border-white/10 p-6">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-white">Team Members</h3>
                      <p className="text-xs text-slate-400 mt-1">
                        {members.length} member{members.length !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <button
                      onClick={() => setShowAssignModal(true)}
                      disabled={loading}
                      className="rounded-lg bg-gradient-to-r from-emerald-500/30 to-emerald-600/40 border border-emerald-400/40 px-4 py-2 text-sm font-semibold text-emerald-300 transition hover:from-emerald-500/40 hover:to-emerald-600/50 disabled:opacity-50"
                    >
                      + Add Member
                    </button>
                  </div>
                  <div className="space-y-2">
                    {members.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-12 text-center">
                        <div className="mb-3 text-4xl">👥</div>
                        <p className="text-sm font-medium text-slate-300">No members yet</p>
                        <p className="text-xs text-slate-500 mt-1">Add team members to get started</p>
                      </div>
                    ) : (
                      members.map(m => (
                        <div 
                          key={m.user_id} 
                          className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10"
                        >
                          <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-kaiops-primary/40 to-kaiops-secondary/40 text-lg">
                              {m.is_team_lead ? '👑' : '👤'}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <p className="font-semibold text-white">{m.username}</p>
                                {m.is_team_lead && (
                                  <span className="rounded-lg border border-amber-400/40 bg-amber-500/20 px-2 py-0.5 text-xs font-semibold text-amber-300">
                                    Team Lead
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-slate-400">
                                {m.full_name || m.email || m.role}
                              </p>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            {!m.is_team_lead && (
                              <button
                                onClick={() => { setSelectedMember(m); setShowPromoteModal(true) }}
                                disabled={loading}
                                className="rounded-lg border border-indigo-400/40 bg-indigo-500/20 px-3 py-1.5 text-xs font-semibold text-indigo-300 transition hover:bg-indigo-500/30 disabled:opacity-50"
                              >
                                Promote
                              </button>
                            )}
                            <button
                              onClick={() => handleRemove(m.user_id)}
                              disabled={loading}
                              className="rounded-lg border border-rose-400/40 bg-rose-500/20 px-3 py-1.5 text-xs font-semibold text-rose-300 transition hover:bg-rose-500/30 disabled:opacity-50"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Agents Section */}
                <div className="glass-card rounded-2xl border border-white/10 p-6">
                  <div className="mb-4">
                    <h3 className="text-lg font-semibold text-white">Agents</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Primary: {primaryAgents.length} · Secondary: {secondaryAgents.length}
                    </p>
                  </div>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    {/* Primary Agents */}
                    <div className="rounded-xl border border-amber-400/40 bg-amber-500/10 p-4">
                      <div className="mb-3 flex items-center justify-between">
                        <h4 className="text-sm font-semibold text-amber-300">🎯 Primary Agents</h4>
                        <button 
                          onClick={() => { 
                            setShowPermissionModal(true); 
                            setAgentData(prev => ({ ...prev, priority: AgentPriority.PRIMARY })) 
                          }} 
                          className="text-xs font-semibold text-amber-300/80 hover:text-amber-300"
                        >
                          + Assign
                        </button>
                      </div>
                      {primaryAgents.length === 0 ? (
                        <p className="text-xs text-slate-400">No primary agents</p>
                      ) : (
                        <ul className="space-y-2">
                          {primaryAgents.map((a, appIdx) => (
                            <li 
                              key={a.id || `agent-${appIdx}`} 
                              className="flex items-center justify-between rounded-lg border border-amber-400/30 bg-white/5 p-3"
                            >
                              <span className="text-sm font-medium text-white">{a.agent_type}</span>
                              <button 
                                onClick={() => handleRemoveAgent(a.id)} 
                                className="text-xs font-semibold text-rose-300 hover:text-rose-200"
                              >
                                Remove
                              </button>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {/* Secondary Agents */}
                    <div className="rounded-xl border border-blue-400/40 bg-blue-500/10 p-4">
                      <div className="mb-3 flex items-center justify-between">
                        <h4 className="text-sm font-semibold text-blue-300">🛡️ Secondary Agents</h4>
                        <button 
                          onClick={() => { 
                            setShowPermissionModal(true); 
                            setAgentData(prev => ({ ...prev, priority: AgentPriority.SECONDARY })) 
                          }} 
                          className="text-xs font-semibold text-blue-300/80 hover:text-blue-300"
                        >
                          + Assign
                        </button>
                      </div>
                      {secondaryAgents.length === 0 ? (
                        <p className="text-xs text-slate-400">No secondary agents</p>
                      ) : (
                        <ul className="space-y-2">
                          {secondaryAgents.map((a, appIdx) => (
                            <li 
                              key={a.id || `agent-${appIdx}`} 
                              className="flex items-center justify-between rounded-lg border border-blue-400/30 bg-white/5 p-3"
                            >
                              <span className="text-sm font-medium text-white">{a.agent_type}</span>
                              <button 
                                onClick={() => handleRemoveAgent(a.id)} 
                                className="text-xs font-semibold text-rose-300 hover:text-rose-200"
                              >
                                Remove
                              </button>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Assign Member Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="glass-panel w-full max-w-lg rounded-3xl border border-white/10 p-8 shadow-2xl text-white">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-kaiops-primary/40 to-kaiops-secondary/40 text-2xl">
                👥
              </div>
              <div>
                <h3 className="text-xl font-black tracking-tight">Add Team Member</h3>
                <p className="text-sm text-slate-400 mt-1">to {selectedTeam?.name}</p>
              </div>
            </div>
            <div className="space-y-4 mb-6">
              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-slate-300">
                  Select User *
                </label>
                <select
                  value={assignData.userId}
                  onChange={(e) => setAssignData({ ...assignData, userId: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-white/5 p-3 text-white focus:border-kaiops-primary/50 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
                >
                  <option value="">Choose a user...</option>
                  {allUsers.map((user) => (
                    <option key={user.username} value={user.username}>
                      {user.username} - {user.email} ({user.role})
                    </option>
                  ))}
                </select>
              </div>
              <div className="glass-card rounded-lg border border-kaiops-primary/30 bg-kaiops-primary/10 p-4">
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    id="assignAsLead"
                    checked={assignData.isTeamLead}
                    onChange={(e) => setAssignData({ ...assignData, isTeamLead: e.target.checked })}
                    className="mt-1 h-4 w-4 rounded border-white/20 bg-white/5 text-kaiops-primary focus:ring-2 focus:ring-kaiops-primary"
                  />
                  <div>
                    <label htmlFor="assignAsLead" className="cursor-pointer text-sm font-semibold text-white">
                      Assign as Team Lead
                    </label>
                    <p className="mt-1 text-xs text-slate-400">
                      Team leads can manage members and permissions
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleAssign}
                disabled={loading || !assignData.userId}
                className="flex-1 rounded-lg bg-gradient-to-r from-kaiops-primary/40 to-kaiops-secondary/40 px-4 py-3 font-semibold text-white transition hover:from-kaiops-primary/50 hover:to-kaiops-secondary/50 disabled:opacity-50"
              >
                {loading ? 'Assigning...' : 'Assign Member'}
              </button>
              <button
                onClick={() => {
                  setShowAssignModal(false)
                  setAssignData({ userId: '', isTeamLead: false })
                }}
                className="flex-1 rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-semibold text-white transition hover:bg-white/10"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Assign Agent Modal */}
      {showPermissionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="glass-panel w-full max-w-lg rounded-3xl border border-white/10 p-8 shadow-2xl text-white">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-kaiops-primary/40 to-kaiops-secondary/40 text-2xl">
                🎛️
              </div>
              <div>
                <h3 className="text-xl font-black tracking-tight">Assign Agent</h3>
                <p className="text-sm text-slate-400 mt-1">to {selectedTeam?.name}</p>
              </div>
            </div>
            <div className="space-y-4 mb-6">
              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-slate-300">
                  Agent Type *
                </label>
                <select
                  value={agentData.agent_type}
                  onChange={(e) => setAgentData({ ...agentData, agent_type: e.target.value })}
                  className="w-full rounded-lg border border-white/10 bg-white/5 p-3 text-white focus:border-kaiops-primary/50 focus:outline-none focus:ring-2 focus:ring-kaiops-primary/20"
                >
                  {Object.values(AgentType).map((a) => (
                    <option key={a} value={a}>{a}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-slate-300">
                  Priority
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <label className={`rounded-lg border p-4 cursor-pointer transition ${
                    agentData.priority === AgentPriority.PRIMARY
                      ? 'border-amber-400/40 bg-amber-500/20'
                      : 'border-white/10 bg-white/5 hover:bg-white/10'
                  }`}>
                    <input 
                      type="radio" 
                      name="priority" 
                      value={AgentPriority.PRIMARY} 
                      checked={agentData.priority === AgentPriority.PRIMARY} 
                      onChange={() => setAgentData({ ...agentData, priority: AgentPriority.PRIMARY })} 
                      className="sr-only" 
                    />
                    <div className={`text-sm font-semibold ${agentData.priority === AgentPriority.PRIMARY ? 'text-amber-300' : 'text-white'}`}>Primary</div>
                    <div className="text-xs text-slate-400 mt-1">Main owner</div>
                  </label>
                  <label className={`rounded-lg border p-4 cursor-pointer transition ${
                    agentData.priority === AgentPriority.SECONDARY
                      ? 'border-blue-400/40 bg-blue-500/20'
                      : 'border-white/10 bg-white/5 hover:bg-white/10'
                  }`}>
                    <input 
                      type="radio" 
                      name="priority" 
                      value={AgentPriority.SECONDARY} 
                      checked={agentData.priority === AgentPriority.SECONDARY} 
                      onChange={() => setAgentData({ ...agentData, priority: AgentPriority.SECONDARY })} 
                      className="sr-only" 
                    />
                    <div className={`text-sm font-semibold ${agentData.priority === AgentPriority.SECONDARY ? 'text-blue-300' : 'text-white'}`}>Secondary</div>
                    <div className="text-xs text-slate-400 mt-1">Backup/support</div>
                  </label>
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleAssignAgent}
                disabled={loading}
                className="flex-1 rounded-lg bg-gradient-to-r from-kaiops-primary/40 to-kaiops-secondary/40 px-4 py-3 font-semibold text-white transition hover:from-kaiops-primary/50 hover:to-kaiops-secondary/50 disabled:opacity-50"
              >
                {loading ? 'Assigning...' : 'Assign Agent'}
              </button>
              <button
                onClick={() => {
                  setShowPermissionModal(false)
                  setAgentData({ agent_type: AgentType.OBSERVABILITY_AGENT, priority: AgentPriority.PRIMARY })
                }}
                className="flex-1 rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-semibold text-white transition hover:bg-white/10"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Promote to Team Lead Modal */}
      {showPromoteModal && selectedMember && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="glass-panel w-full max-w-lg rounded-3xl border border-white/10 p-8 shadow-2xl text-white">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500/40 to-amber-600/40 text-2xl">
                👑
              </div>
              <div>
                <h3 className="text-xl font-black tracking-tight">Promote to Team Lead</h3>
                <p className="text-sm text-slate-400 mt-1">Grant leadership permissions</p>
              </div>
            </div>
            <div className="mb-4 glass-card rounded-lg border border-amber-400/40 bg-amber-500/10 p-5">
              <p className="mb-3 text-sm text-slate-300">
                You are about to promote:
              </p>
              <div className="mb-3 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-kaiops-primary/40 to-kaiops-secondary/40 text-xl">
                  👤
                </div>
                <div>
                  <div className="font-bold text-white">{selectedMember.username}</div>
                  <div className="text-xs text-slate-400">{selectedMember.email}</div>
                </div>
              </div>
              <p className="text-sm text-slate-300">
                to Team Lead of <span className="font-bold text-amber-300">{selectedTeam?.name}</span>
              </p>
            </div>
            <div className="mb-4 glass-card rounded-lg border border-blue-400/40 bg-blue-500/10 p-4">
              <div className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-blue-300">
                Team Lead Privileges
              </div>
              <ul className="space-y-1 text-xs text-slate-300">
                <li>• Manage team members</li>
                <li>• Assign and revoke permissions</li>
                <li>• View team analytics</li>
              </ul>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handlePromoteToLead}
                disabled={loading}
                className="flex-1 rounded-lg bg-gradient-to-r from-amber-500/40 to-amber-600/40 px-4 py-3 font-semibold text-amber-300 transition hover:from-amber-500/50 hover:to-amber-600/50 disabled:opacity-50 border border-amber-400/40"
              >
                {loading ? 'Promoting...' : 'Promote Now'}
              </button>
              <button
                onClick={() => {
                  setShowPromoteModal(false)
                  setSelectedMember(null)
                }}
                className="flex-1 rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-semibold text-white transition hover:bg-white/10"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TeamManagement