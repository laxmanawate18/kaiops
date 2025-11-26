import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

function Profile() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('info')

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-600/20 text-purple-400 border-purple-500/50'
      case 'team_lead':
        return 'bg-blue-600/20 text-blue-400 border-blue-500/50'
      case 'user':
      default:
        return 'bg-green-600/20 text-green-400 border-green-500/50'
    }
  }

  const getRoleDisplayName = (role) => {
    switch (role) {
      case 'admin':
        return 'Admin'
      case 'team_lead':
        return 'Team Lead'
      case 'user':
      default:
        return 'User'
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="h-full w-full overflow-y-auto custom-scrollbar pr-2">
      <div className="mx-auto max-w-5xl flex flex-col">
        <header className="glass-panel relative overflow-hidden rounded-3xl border border-white/10 px-8 py-10 mb-6 text-white">
          <div className="relative z-10 flex flex-col gap-3">
            <p className="text-xs font-semibold tracking-[0.4em] text-kaiops-primary">OPERATOR PROFILE</p>
            <h1 className="text-4xl font-black tracking-tight">Your Account</h1>
            <p className="max-w-2xl text-sm text-slate-300">
              Manage credentials, permissions, and team assignments.
            </p>
          </div>
          <div className="pointer-events-none absolute right-0 top-0 h-full w-1/2 opacity-40" style={{ background: 'radial-gradient(circle at top, rgba(112,0,255,0.35), transparent 55%)' }} />
        </header>

        {/* Profile Hero Card */}
        <section className="glass-panel relative overflow-hidden rounded-3xl border border-white/10 p-8 mb-6 shadow-2xl">
          <div className="relative z-10 flex items-start gap-6">
            <div className="flex-shrink-0">
              <div className="flex h-28 w-28 items-center justify-center rounded-2xl bg-gradient-to-br from-kaiops-primary/40 to-kaiops-secondary/30 text-4xl font-black text-white shadow-xl">
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </div>
            </div>

            <div className="flex-1">
              <div className="mb-2 flex items-center gap-4">
                <h2 className="text-3xl font-black text-white">
                  {user?.username || 'Unknown Operator'}
                </h2>
                <span className={`rounded-full border px-4 py-1.5 text-xs font-bold tracking-wider uppercase ${
                  user?.role === 'admin' 
                    ? 'border-rose-400/40 bg-rose-500/20 text-rose-300'
                    : user?.role === 'team_lead'
                    ? 'border-indigo-400/40 bg-indigo-500/20 text-indigo-300'
                    : 'border-emerald-400/40 bg-emerald-500/20 text-emerald-300'
                }`}>
                  {getRoleDisplayName(user?.role)}
                </span>
              </div>
              <p className="text-sm text-slate-300">{user?.email || 'No email on file'}</p>
              <div className="mt-4 grid grid-cols-3 gap-4">
                <div className="glass-card rounded-2xl border border-white/5 p-4">
                  <p className="text-xs tracking-[0.3em] text-slate-400">OPERATOR ID</p>
                  <p className="mt-2 text-sm font-mono text-white">{user?.id || '—'}</p>
                </div>
                <div className="glass-card rounded-2xl border border-white/5 p-4">
                  <p className="text-xs tracking-[0.3em] text-slate-400">JOINED</p>
                  <p className="mt-2 text-sm text-white">{formatDate(user?.createdAt)}</p>
                </div>
                <div className="glass-card rounded-2xl border border-white/5 p-4">
                  <p className="text-xs tracking-[0.3em] text-slate-400">STATUS</p>
                  <p className="mt-2 flex items-center gap-2 text-sm text-emerald-300">
                    <span className="h-2 w-2 rounded-full bg-emerald-400" />
                    Active
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Tab Navigation */}
        <div className="mb-6 flex gap-2 border-b border-white/10">
          {[
            { id: 'info', label: 'Information' },
            { id: 'permissions', label: 'Permissions' },
            { id: 'activity', label: 'Activity' }
          ].map((tab, tabIndex) => (
            <button
              key={tab.id || `tab-${tabIndex}`}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-semibold tracking-wide transition-all ${
                activeTab === tab.id
                  ? 'border-b-2 border-kaiops-primary text-kaiops-primary'
                  : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="glass-panel rounded-3xl border border-white/10 p-8 shadow-2xl text-white">
          {activeTab === 'info' && (
            <div className="space-y-6">
              <h3 className="text-xl font-black tracking-tight">Account Information</h3>
              <div className="grid gap-4 sm:grid-cols-2">
                {[
                  { label: 'Username', value: user?.username || 'N/A' },
                  { label: 'Email Address', value: user?.email || 'Not provided' },
                  { label: 'Access Level', value: getRoleDisplayName(user?.role) },
                  { label: 'Account Status', value: 'Active' },
                  { label: 'Last Login', value: formatDate(user?.lastLogin) }
                ].map((item) => (
                  <div key={item.label} className="glass-card rounded-2xl border border-white/5 p-4">
                    <p className="text-xs tracking-[0.3em] text-slate-400">{item.label.toUpperCase()}</p>
                    <p className="mt-2 font-semibold text-white">{item.value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'permissions' && (
            <div className="space-y-6">
              <h3 className="text-xl font-black tracking-tight">Access Permissions</h3>
              <div className="space-y-3">
                {[
                  { icon: '💬', title: 'Chat Access', desc: 'Interact with KaiOPS AI agent', enabled: true },
                  { icon: '📊', title: 'Dashboard View', desc: 'View metrics and system stats', enabled: true },
                  { icon: '⭐', title: 'Feedback Review', desc: 'Review and approve user feedback', enabled: true }
                ].map((perm) => (
                  <div key={perm.title} className="glass-card flex items-center gap-4 rounded-2xl border border-white/5 p-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/30 text-lg flex-shrink-0">
                      {perm.icon}
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-white">{perm.title}</p>
                      <p className="text-xs text-slate-400">{perm.desc}</p>
                    </div>
                    {perm.enabled && <span className="text-xs font-bold text-emerald-300">ENABLED</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'activity' && (
            <div className="space-y-6">
              <h3 className="text-xl font-black tracking-tight">Recent Activity</h3>
              <div className="space-y-3">
                {[
                  { action: 'Logged In', time: formatDate(user?.lastLogin) || 'Just now', icon: '🔑' },
                  { action: 'Account Created', time: formatDate(user?.createdAt), icon: '✨' }
                ].map((event) => (
                  <div key={event.action} className="glass-card flex items-start gap-4 rounded-2xl border border-white/5 p-4">
                    <div className="mt-1 text-xl">{event.icon}</div>
                    <div className="flex-1">
                      <p className="font-semibold text-white">{event.action}</p>
                      <p className="text-xs text-slate-400">{event.time}</p>
                    </div>
                  </div>
                ))}
                <div className="glass-card rounded-2xl border border-slate-400/20 bg-slate-500/5 p-4 text-sm text-slate-300">
                  Full activity log coming soon.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Profile
