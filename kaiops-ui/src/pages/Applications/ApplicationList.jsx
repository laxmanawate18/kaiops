import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../../contexts/AuthContext'
import applicationService from '../../services/applicationService'
import ConfirmDialog from '../../components/ConfirmDialog'

function ApplicationList() {
  const navigate = useNavigate()
  const { isAdmin, isTeamLead } = useAuth()
  
  // Data State
  const [applications, setApplications] = useState([])
  const [stats, setStats] = useState({ total: 0, active: 0, inactive: 0, clusters: 0 })
  const [loading, setLoading] = useState(true)
  
  // Filter State
  const [viewMode, setViewMode] = useState('grid') // 'grid' | 'list'
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [clusterFilter, setClusterFilter] = useState('all')
  
  // Action State
  const [deleteId, setDeleteId] = useState(null)
  const [notification, setNotification] = useState(null)

  // Helper to extract status from enum format (e.g., "ApplicationStatusEnum.ACTIVE" -> "ACTIVE")
  const getStatusValue = (status) => {
    if (!status) return ''
    const statusStr = status.toString()
    return statusStr.includes('.') ? statusStr.split('.').pop() : statusStr
  }

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      // Load all apps for client-side filtering (better UX for small datasets)
      // In a real large-scale app, we'd use server-side filtering
      const data = await applicationService.getApplications({ page: 1, page_size: 1000 })
      const apps = data.applications || []
      setApplications(apps)
      
      // Calculate stats
      const uniqueClusters = new Set(apps.map(a => a.gke_cluster_name).filter(Boolean)).size
      setStats({
        total: apps.length,
        active: apps.filter(a => getStatusValue(a.status).toUpperCase() === 'ACTIVE').length,
        inactive: apps.filter(a => getStatusValue(a.status).toUpperCase() === 'INACTIVE').length,
        clusters: uniqueClusters
      })
    } catch (error) {
      showNotification('Failed to load applications', 'error')
    } finally {
      setLoading(false)
    }
  }

  const showNotification = (text, type = 'success') => {
    setNotification({ text, type })
    setTimeout(() => setNotification(null), 3000)
  }

  const handleDelete = async () => {
    if (!deleteId) return
    try {
      await applicationService.deleteApplication(deleteId)
      showNotification('Application deleted successfully')
      loadData()
    } catch (error) {
      showNotification('Failed to delete application', 'error')
    } finally {
      setDeleteId(null)
    }
  }

  const handleToggleStatus = async (id, currentStatus) => {
    try {
      await applicationService.toggleStatus(id)
      // Optimistic update
      setApplications(prev => prev.map(app => 
        app.id === id ? { ...app, status: getStatusValue(currentStatus).toUpperCase() === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE' } : app
      ))
      showNotification(`Application ${getStatusValue(currentStatus).toUpperCase() === 'ACTIVE' ? 'deactivated' : 'activated'}`)
    } catch (error) {
      showNotification('Failed to update status', 'error')
      loadData() // Revert on error
    }
  }

  // Derived State
  const uniqueClusters = useMemo(() => 
    [...new Set(applications.map(a => a.gke_cluster_name).filter(Boolean))].sort(),
  [applications])

  const filteredApps = useMemo(() => {
    return applications.filter(app => {
      if (statusFilter !== 'all' && getStatusValue(app.status).toUpperCase() !== statusFilter.toUpperCase()) return false
      if (clusterFilter !== 'all' && app.gke_cluster_name !== clusterFilter) return false
      
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        return (
          app.application_name?.toLowerCase().includes(q) ||
          app.application_owner?.toLowerCase().includes(q) ||
          app.gke_cluster_name?.toLowerCase().includes(q)
        )
      }
      return true
    })
  }, [applications, statusFilter, clusterFilter, searchQuery])

  return (
    <div className="h-full w-full overflow-y-auto custom-scrollbar pr-2">
      <div className="mx-auto max-w-7xl flex flex-col gap-6">
        
        {/* Header Section */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel relative overflow-hidden rounded-3xl border border-white/10 px-8 py-10"
        >
          <div className="absolute inset-0 opacity-30">
            <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
            <div className="absolute bottom-0 left-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
          </div>

          <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <p className="text-xs font-semibold tracking-[0.4em] text-cyan-400 mb-2">SERVICE REGISTRY</p>
              <h1 className="text-4xl font-black tracking-tight text-white mb-2">Applications</h1>
              <p className="text-slate-400 max-w-xl">
                Manage your microservices, monitor deployment status, and configure application settings across all clusters.
              </p>
            </div>

            {(isAdmin || isTeamLead) && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/applications/new')}
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500/30 to-blue-500/30 border border-cyan-400/50 px-6 py-3 font-semibold text-cyan-300 transition hover:from-cyan-500/40 hover:to-blue-500/40 shadow-lg shadow-cyan-500/10"
              >
                <span>🚀</span> Register Service
              </motion.button>
            )}
          </div>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard 
            label="Total Services" 
            value={stats.total} 
            icon="📦" 
            color="text-blue-400" 
            bg="bg-blue-500/10" 
            border="border-blue-500/20" 
          />
          <StatCard 
            label="Active" 
            value={stats.active} 
            icon="🟢" 
            color="text-emerald-400" 
            bg="bg-emerald-500/10" 
            border="border-emerald-500/20" 
          />
          <StatCard 
            label="Inactive" 
            value={stats.inactive} 
            icon="⭕" 
            color="text-slate-400" 
            bg="bg-slate-500/10" 
            border="border-slate-500/20" 
          />
          <StatCard 
            label="Clusters" 
            value={stats.clusters} 
            icon="🌐" 
            color="text-purple-400" 
            bg="bg-purple-500/10" 
            border="border-purple-500/20" 
          />
        </div>

        {/* Controls & Filters */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="glass-panel rounded-2xl border border-white/10 p-4 flex flex-col lg:flex-row gap-4 items-center justify-between"
        >
          <div className="flex-1 w-full lg:w-auto relative">
            <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search services, owners, clusters..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 pl-10 text-sm text-white placeholder-slate-400 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
            />
          </div>

          <div className="flex gap-2 w-full lg:w-auto overflow-x-auto pb-2 lg:pb-0">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
            >
              <option value="all">All Status</option>
              <option value="active">🟢 Active</option>
              <option value="inactive">⭕ Inactive</option>
            </select>

            <select
              value={clusterFilter}
              onChange={(e) => setClusterFilter(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
            >
              <option value="all">All Clusters</option>
              {uniqueClusters.map(c => (
                <option key={c} value={c}>🌐 {c}</option>
              ))}
            </select>

            <div className="flex gap-1 border border-white/10 rounded-xl p-1 bg-white/5">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-lg transition ${viewMode === 'grid' ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-lg transition ${viewMode === 'list' ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
              </button>
            </div>
          </div>
        </motion.div>

        {/* Content Area */}
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="w-12 h-12 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
          </div>
        ) : filteredApps.length === 0 ? (
          <div className="glass-panel rounded-3xl border border-white/10 flex h-64 items-center justify-center flex-col text-slate-400">
            <p className="text-4xl mb-4">🔍</p>
            <p>No applications found matching your filters</p>
          </div>
        ) : viewMode === 'grid' ? (
          // Grid View
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatePresence>
              {filteredApps.map((app, idx) => (
                <motion.div
                  key={app.id || `app-${idx}`}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  className="glass-card group relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-white/0 p-6 hover:border-cyan-500/30 hover:shadow-lg hover:shadow-cyan-500/10 transition-all"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 flex items-center justify-center text-2xl">
                      📦
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-bold border ${
                      getStatusValue(app.status).toUpperCase() === 'ACTIVE' 
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' 
                        : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
                    }`}>
                      {getStatusValue(app.status).toUpperCase() === 'ACTIVE' ? 'ACTIVE' : 'INACTIVE'}
                    </div>
                  </div>

                  <h3 className="text-xl font-bold text-white mb-1 truncate">{app.application_name}</h3>
                  <p className="text-sm text-slate-400 mb-4 line-clamp-2 h-10">
                    {app.description || 'No description provided'}
                  </p>

                  <div className="space-y-2 mb-6">
                    <div className="flex items-center gap-2 text-xs text-slate-300">
                      <span className="text-slate-500">CLUSTER</span>
                      <span className="font-mono bg-white/5 px-2 py-0.5 rounded">{app.gke_cluster_name}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-300">
                      <span className="text-slate-500">OWNER</span>
                      <span>{app.application_owner}</span>
                    </div>
                  </div>

                  <div className="flex gap-2 pt-4 border-t border-white/10">
                    <button
                      onClick={() => navigate(`/applications/${app.id}`)}
                      className="flex-1 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-bold text-white transition"
                    >
                      DETAILS
                    </button>
                    {(isAdmin || isTeamLead) && (
                      <>
                        <button
                          onClick={() => navigate(`/applications/${app.id}/edit`)}
                          className="p-2 rounded-lg bg-white/5 hover:bg-cyan-500/20 text-cyan-300 transition"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => setDeleteId(app.id)}
                          className="p-2 rounded-lg bg-white/5 hover:bg-rose-500/20 text-rose-300 transition"
                        >
                          🗑️
                        </button>
                      </>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        ) : (
          // List View
          <div className="glass-panel rounded-3xl border border-white/10 overflow-hidden">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-white/5 text-xs uppercase font-bold tracking-wider text-slate-400">
                <tr>
                  <th className="px-6 py-4">Application</th>
                  <th className="px-6 py-4">Cluster</th>
                  <th className="px-6 py-4">Owner</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredApps.map((app) => (
                  <tr key={app.id || `app-${filteredApps.indexOf(app)}`} className="hover:bg-white/5 transition">
                    <td className="px-6 py-4">
                      <div className="font-bold text-white">{app.application_name}</div>
                      <div className="text-xs text-slate-500 truncate max-w-[200px]">{app.description}</div>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs">{app.gke_cluster_name}</td>
                    <td className="px-6 py-4">{app.application_owner}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${
                        getStatusValue(app.status).toUpperCase() === 'ACTIVE' 
                          ? 'bg-emerald-400/20 text-emerald-400' 
                          : 'bg-slate-500/20 text-slate-400'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${getStatusValue(app.status).toUpperCase() === 'ACTIVE' ? 'bg-emerald-400' : 'bg-slate-400'}`} />
                        {getStatusValue(app.status).toUpperCase() || 'UNKNOWN'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button 
                        onClick={() => navigate(`/applications/${app.id}`)}
                        className="text-cyan-400 hover:text-cyan-300 font-semibold"
                      >
                        View
                      </button>
                      {(isAdmin || isTeamLead) && (
                        <button 
                          onClick={() => setDeleteId(app.id)}
                          className="text-rose-400 hover:text-rose-300 font-semibold"
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Notifications */}
      <AnimatePresence>
        {notification && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className={`fixed bottom-6 right-6 z-50 px-6 py-4 rounded-2xl shadow-2xl border backdrop-blur-xl flex items-center gap-3 ${
              notification.type === 'success' 
                ? 'bg-emerald-500/20 border-emerald-500/30 text-emerald-200' 
                : 'bg-rose-500/20 border-rose-500/30 text-rose-200'
            }`}
          >
            <span className="text-xl">{notification.type === 'success' ? '✨' : '⚠️'}</span>
            <span className="font-semibold">{notification.text}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDelete}
        title="Delete Application"
        message="Are you sure you want to delete this application? This action cannot be undone."
        confirmText="Delete Service"
        type="danger"
      />
    </div>
  )
}

// Helper Component
const StatCard = ({ label, value, icon, color, bg, border }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className={`glass-card rounded-2xl border ${bg} ${border} p-5 flex items-center justify-between`}
  >
    <div>
      <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">{label}</p>
      <p className={`text-3xl font-black ${color}`}>{value}</p>
    </div>
    <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl bg-white/5`}>
      {icon}
    </div>
  </motion.div>
)

export default ApplicationList
