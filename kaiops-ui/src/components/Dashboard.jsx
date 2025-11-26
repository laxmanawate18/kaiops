import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { apiService } from '../services/api'
import { chatService } from '../services/chatService'
import { feedbackService } from '../services/feedback'
import { applicationService } from '../services/applicationService'
import { useAuth } from '../contexts/AuthContext'

function Dashboard() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const isTeamLead = user?.role === 'team_lead'
  const isAdminOrTeamLead = isAdmin || isTeamLead

  // Data State
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [data, setData] = useState({
    sessions: [],
    health: null,
    chatStats: null,
    feedbackStats: null,
    appStats: null,
    myFeedback: null
  })

  const loadDashboard = useCallback(async () => {
    if (!user?.username) return
    setLoading(true)
    setError(null)

    try {
      // Parallel data fetching
      const [
        sessions,
        myFeedback,
        chatStats,
        health,
        appStats,
        feedbackStats
      ] = await Promise.all([
        chatService.getSessions().catch(() => []),
        feedbackService.getMyStats().catch(() => null),
        apiService.getChatStats().catch(() => null),
        apiService.healthCheck().catch(() => null),
        isAdminOrTeamLead ? applicationService.getStatistics().catch(() => null) : Promise.resolve(null),
        isAdminOrTeamLead ? feedbackService.stats().catch(() => null) : Promise.resolve(null)
      ])

      setData({
        sessions: sessions || [],
        myFeedback,
        chatStats,
        health,
        appStats,
        feedbackStats
      })
    } catch (err) {
      console.error('Dashboard load error:', err)
      setError('Failed to establish telemetry link.')
    } finally {
      setLoading(false)
    }
  }, [user?.username, isAdminOrTeamLead])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  // Quick Actions Configuration
  const quickActions = [
    {
      title: 'Start Mission',
      desc: 'Launch a new reliability thread',
      icon: '🚀',
      color: 'from-cyan-500/20 to-blue-500/20',
      border: 'border-cyan-500/30',
      action: () => navigate('/', { state: { initialMessage: 'Hello KaiOPS' } })
    },
    {
      title: 'List Services',
      desc: 'View monitored applications',
      icon: '📦',
      color: 'from-purple-500/20 to-indigo-500/20',
      border: 'border-purple-500/30',
      action: () => navigate('/', { state: { initialMessage: 'List all applications' } })
    },
    {
      title: 'Health Check',
      desc: 'Run system diagnostics',
      icon: '🩺',
      color: 'from-emerald-500/20 to-teal-500/20',
      border: 'border-emerald-500/30',
      action: () => navigate('/', { state: { initialMessage: 'Check system health' } })
    }
  ]

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-4">
        <div className="w-16 h-16 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
        <p className="text-cyan-400 font-mono text-sm tracking-widest animate-pulse">ESTABLISHING UPLINK...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="glass-panel border-red-500/30 bg-red-500/10 p-8 text-center max-w-md">
          <h2 className="text-2xl font-bold text-red-400 mb-2">Telemetry Lost</h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <button 
            onClick={loadDashboard}
            className="px-6 py-2 rounded-full bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/40 transition"
          >
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full w-full overflow-y-auto custom-scrollbar pr-2">
      <div className="mx-auto max-w-7xl flex flex-col gap-8 pb-10">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <p className="text-xs font-bold tracking-[0.3em] text-cyan-400 mb-1">MISSION CONTROL</p>
            <h1 className="text-4xl font-black text-white tracking-tight">
              Welcome back, <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">{user?.username}</span>
            </h1>
          </motion.div>
          
          <div className="flex items-center gap-3">
            <div className={`px-3 py-1 rounded-full border text-xs font-bold tracking-wider ${
              data.health?.status === 'healthy' 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
            }`}>
              SYSTEM {data.health?.status === 'healthy' ? 'ONLINE' : 'DEGRADED'}
            </div>
            <button 
              onClick={loadDashboard}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition"
            >
              🔄
            </button>
          </div>
        </header>

        {/* Top Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard 
            label="Active Sessions"
            value={data.sessions.length}
            subtext="Conversations"
            icon="💬"
            color="text-blue-400"
            bg="bg-blue-500/10"
            border="border-blue-500/20"
            delay={0.1}
          />
          <StatCard 
            label="Feedback Score"
            value={data.myFeedback?.avg_rating?.toFixed(1) || '-'}
            subtext="Your Contribution"
            icon="⭐"
            color="text-purple-400"
            bg="bg-purple-500/10"
            border="border-purple-500/20"
            delay={0.2}
          />
          <StatCard 
            label="System Load"
            value="OPTIMAL"
            subtext="All systems go"
            icon="⚡"
            color="text-emerald-400"
            bg="bg-emerald-500/10"
            border="border-emerald-500/20"
            delay={0.3}
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column: Quick Actions & Recent Sessions */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Quick Actions */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <h2 className="text-sm font-bold text-slate-400 tracking-wider mb-4">QUICK ACTIONS</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {quickActions.map((action, idx) => (
                  <motion.button
                    key={idx}
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={action.action}
                    className={`glass-card text-left p-4 rounded-2xl border ${action.border} bg-gradient-to-br ${action.color} hover:shadow-lg transition-all`}
                  >
                    <div className="text-2xl mb-2">{action.icon}</div>
                    <div className="font-bold text-white mb-1">{action.title}</div>
                    <div className="text-xs text-slate-300 opacity-80">{action.desc}</div>
                  </motion.button>
                ))}
              </div>
            </motion.section>

            {/* Recent Sessions */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="glass-panel rounded-3xl border border-white/10 p-6"
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-bold text-white">Recent Missions</h2>
                <button 
                  onClick={() => navigate('/')}
                  className="text-xs font-bold text-cyan-400 hover:text-cyan-300"
                >
                  VIEW ALL
                </button>
              </div>
              
              <div className="space-y-3">
                {data.sessions.slice(0, 4).map((session, idx) => (
                  <motion.div
                    key={session.id || idx}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 + idx * 0.05 }}
                    onClick={() => navigate('/', { state: { sessionId: session.id } })}
                    className="group cursor-pointer flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-cyan-500/30 transition-all"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center text-lg group-hover:scale-110 transition-transform">
                        💬
                      </div>
                      <div>
                        <p className="font-semibold text-white group-hover:text-cyan-300 transition-colors">
                          {session.name || 'Untitled Mission'}
                        </p>
                        <p className="text-xs text-slate-400 font-mono">
                          ID: {session.id?.substring(0, 8)}...
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-bold text-slate-300">{session.message_count || 0} msgs</p>
                      <p className="text-[10px] text-slate-500">
                        {new Date(session.updated_at || Date.now()).toLocaleDateString()}
                      </p>
                    </div>
                  </motion.div>
                ))}
                {data.sessions.length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    <p>No active missions found.</p>
                  </div>
                )}
              </div>
            </motion.section>
          </div>

          {/* Right Column: Admin Stats / System Health */}
          <div className="space-y-6">
            {isAdminOrTeamLead && (
              <motion.section
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 }}
                className="glass-panel rounded-3xl border border-white/10 p-6 bg-gradient-to-b from-white/5 to-transparent"
              >
                <h2 className="text-sm font-bold text-slate-400 tracking-wider mb-6">COMMAND OVERVIEW</h2>
                
                <div className="space-y-6">
                  {/* App Stats */}
                  <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-semibold text-white">Applications</span>
                      <span className="text-xs font-bold text-cyan-400">{data.appStats?.total_applications || 0} Total</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-2 mb-2 overflow-hidden">
                      <div 
                        className="bg-cyan-500 h-full rounded-full" 
                        style={{ width: `${(data.appStats?.active_applications / data.appStats?.total_applications) * 100 || 0}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>{data.appStats?.active_applications || 0} Active</span>
                      <span>{data.appStats?.inactive_applications || 0} Inactive</span>
                    </div>
                  </div>

                  {/* Feedback Stats */}
                  <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-semibold text-white">Feedback Queue</span>
                      <span className="text-xs font-bold text-amber-400">{data.feedbackStats?.pending_review || 0} Pending</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 mt-3">
                      <div className="text-center p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                        <p className="text-lg font-bold text-emerald-400">{data.feedbackStats?.approved || 0}</p>
                        <p className="text-[10px] text-emerald-300/70 uppercase">Approved</p>
                      </div>
                      <div className="text-center p-2 rounded-lg bg-rose-500/10 border border-rose-500/20">
                        <p className="text-lg font-bold text-rose-400">{data.feedbackStats?.denied || 0}</p>
                        <p className="text-[10px] text-rose-300/70 uppercase">Denied</p>
                      </div>
                    </div>
                  </div>

                  {/* Dataset Stats */}
                  <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-semibold text-white">AI Training Data</span>
                      <span className="text-xs font-bold text-purple-400">{data.appStats?.total_applications ? 'Active' : 'Ready'}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex-1">
                        <p className="text-2xl font-black text-white">{data.feedbackStats?.total_feedback || 0}</p>
                        <p className="text-xs text-slate-400">Total Samples</p>
                      </div>
                      <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400">
                        🧠
                      </div>
                    </div>
                  </div>
                </div>
              </motion.section>
            )}

            {/* System Pulse */}
            <motion.section
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.7 }}
              className="glass-panel rounded-3xl border border-white/10 p-6 relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent" />
              <h2 className="text-sm font-bold text-slate-400 tracking-wider mb-4 relative z-10">SYSTEM PULSE</h2>
              
              <div className="space-y-3 relative z-10">
                {['API Gateway', 'Database', 'AI Engine', 'Auth Service'].map((service, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-sm text-slate-300">{service}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-emerald-400 font-mono">OPERATIONAL</span>
                      <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)] animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            </motion.section>
          </div>
        </div>
      </div>
    </div>
  )
}

// Helper Component
const StatCard = ({ label, value, subtext, icon, color, bg, border, delay }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay }}
    className={`glass-card rounded-2xl border ${bg} ${border} p-6 flex items-center justify-between hover:scale-[1.02] transition-transform`}
  >
    <div>
      <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">{label}</p>
      <p className={`text-3xl font-black ${color} mb-1`}>{value}</p>
      <p className="text-xs text-slate-400 opacity-80">{subtext}</p>
    </div>
    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-3xl bg-white/5 shadow-inner`}>
      {icon}
    </div>
  </motion.div>
)

export default Dashboard
