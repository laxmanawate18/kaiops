import { useEffect, useState, useMemo } from 'react'
import { authService } from '../services/auth'
import { motion, AnimatePresence } from 'framer-motion'

function UserManagement() {
  // Core State
  const [users, setUsers] = useState([])
  const [selectedUserDetail, setSelectedUserDetail] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showAccessModal, setShowAccessModal] = useState(false)
  
  // Form State
  const [createData, setCreateData] = useState({ username: '', email: '', password: '', full_name: '' })
  const [editAccessData, setEditAccessData] = useState({ role: 'user', is_active: true })
  
  // Filter & Search State
  const [searchQuery, setSearchQuery] = useState('')
  const [accessFilter, setAccessFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortBy, setSortBy] = useState('username')
  
  // UI State
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState('detailed')

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      const usersData = await authService.getAllUsers()
      setUsers(usersData)
    } catch (error) {
      console.error('Error loading users:', error)
      showNotification('Failed to load users', 'error')
    }
  }

  const showNotification = (text, type = 'success', duration = 3000) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), duration)
  }

  const handleCreateUser = async () => {
    if (!createData.username || !createData.email || !createData.password) {
      showNotification('All fields are required', 'error')
      return
    }
    
    setLoading(true)
    try {
      await authService.createUser({
        username: createData.username,
        email: createData.email,
        password: createData.password,
        full_name: createData.full_name || createData.username
      })
      showNotification(`✨ User "${createData.username}" added successfully`)
      setShowCreateModal(false)
      setCreateData({ username: '', email: '', password: '', full_name: '' })
      loadUsers()
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Failed to create user', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateAccess = async () => {
    if (!selectedUserDetail) return
    
    setLoading(true)
    try {
      await authService.updateUser(selectedUserDetail.username, {
        role: editAccessData.role,
        is_active: editAccessData.is_active
      })
      showNotification('✓ Access updated successfully')
      setShowAccessModal(false)
      loadUsers()
      const updated = users.find(u => u.username === selectedUserDetail.username)
      if (updated) setSelectedUserDetail(updated)
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Failed to update access', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Get access level info
  const getAccessInfo = (role, is_active) => {
    if (!is_active) {
      return { level: 'Revoked', color: 'text-red-400', bgColor: 'bg-red-500/20', icon: '🔴', badge: 'border-red-400/40 bg-red-500/20' }
    }
    switch(role) {
      case 'admin':
        return { level: 'Full Access', color: 'text-amber-400', bgColor: 'bg-amber-500/20', icon: '🔑', badge: 'border-amber-400/40 bg-amber-500/20' }
      default:
        return { level: 'Limited Access', color: 'text-emerald-400', bgColor: 'bg-emerald-500/20', icon: '🔓', badge: 'border-emerald-400/40 bg-emerald-500/20' }
    }
  }

  const getAccessPermissions = (role, is_active) => {
    if (!is_active) {
      return { permissions: [] }
    }
    
    if (role === 'admin') {
      return {
        permissions: [
          '📊 View all data & analytics',
          '⚙️ Manage system configuration',
          '👥 Manage users & permissions',
          '📈 Access detailed reports',
          '🔧 System administration',
          '📋 Audit logs access'
        ]
      }
    }
    
    return {
      permissions: [
        '📊 View assigned data',
        '📈 View operational reports',
        '💬 Team collaboration',
        '🔍 View own profile'
      ]
    }
  }

  // Filtered and sorted users
  const filteredUsers = useMemo(() => {
    let result = users.filter(user => {
      if (accessFilter !== 'all') {
        if (accessFilter === 'admin' && user.role !== 'admin') return false
        if (accessFilter === 'member' && user.role !== 'user') return false
      }
      
      if (statusFilter === 'active' && !user.is_active) return false
      if (statusFilter === 'inactive' && user.is_active) return false
      
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        return (
          user.username?.toLowerCase().includes(query) ||
          user.email?.toLowerCase().includes(query) ||
          user.full_name?.toLowerCase().includes(query)
        )
      }
      
      return true
    })

    result.sort((a, b) => {
      switch(sortBy) {
        case 'access':
          const aAccess = a.role === 'admin' ? 1 : 0
          const bAccess = b.role === 'admin' ? 1 : 0
          return bAccess - aAccess
        case 'status':
          return (b.is_active ? 1 : 0) - (a.is_active ? 1 : 0)
        default:
          return a.username.localeCompare(b.username)
      }
    })

    return result
  }, [users, accessFilter, statusFilter, searchQuery, sortBy])

  // Statistics
  const stats = useMemo(() => ({
    total: users.length,
    active: users.filter(u => u.is_active).length,
    inactive: users.filter(u => !u.is_active).length,
    admins: users.filter(u => u.role === 'admin' && u.is_active).length,
    members: users.filter(u => u.role === 'user' && u.is_active).length,
    fullAccessCount: users.filter(u => u.role === 'admin' && u.is_active).length,
    limitedAccessCount: users.filter(u => u.role === 'user' && u.is_active).length,
    revokedCount: users.filter(u => !u.is_active).length
  }), [users])

  return (
    <div className="h-full w-full overflow-y-auto custom-scrollbar pr-2">
      <div className="mx-auto max-w-7xl flex flex-col gap-6">
        {/* Header Section */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel relative overflow-hidden rounded-3xl border border-white/10 px-8 py-12"
        >
          <div className="absolute inset-0 opacity-40">
            <div className="absolute top-0 left-0 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl" />
            <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
          </div>

          <div className="relative z-10 flex items-start justify-between gap-8">
            <div className="flex-1">
              <motion.p 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="text-xs font-semibold tracking-[0.4em] text-amber-400 mb-2"
              >
                ACCESS CONTROL
              </motion.p>
              <motion.h1 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.15 }}
                className="text-5xl font-black tracking-tight mb-3 text-white"
              >
                User Access & Information
              </motion.h1>
              <motion.p 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="max-w-2xl text-base text-slate-300 leading-relaxed"
              >
                Manage system access levels, permissions, and user information. Monitor active sessions and control who has access to KaiOPS.
              </motion.p>
            </div>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500/30 to-green-500/30 border border-emerald-400/50 px-6 py-3 font-semibold text-emerald-300 transition hover:from-emerald-500/40 hover:to-green-500/40 shrink-0 whitespace-nowrap"
            >
              <span>➕</span>
              Add User
            </motion.button>
          </div>
        </motion.div>

        {/* Access Level Statistics */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4"
        >
          {[
            { 
              label: 'Total Users', 
              value: stats.total, 
              icon: '👥',
              color: 'from-blue-500/20 to-blue-600/30 border-blue-400/40',
              subtext: 'all accounts'
            },
            { 
              label: 'Full Access', 
              value: stats.fullAccessCount,
              icon: '🔑',
              color: 'from-amber-500/20 to-amber-600/30 border-amber-400/40',
              subtext: 'admin privilege'
            },
            { 
              label: 'Limited Access', 
              value: stats.limitedAccessCount,
              icon: '🔓',
              color: 'from-emerald-500/20 to-emerald-600/30 border-emerald-400/40',
              subtext: 'standard users'
            },
            { 
              label: 'Access Revoked', 
              value: stats.revokedCount,
              icon: '🔴',
              color: 'from-red-500/20 to-red-600/30 border-red-400/40',
              subtext: 'inactive'
            }
          ].map((stat, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + idx * 0.05 }}
              whileHover={{ y: -4 }}
              className={`glass-card rounded-2xl border bg-gradient-to-br ${stat.color} p-6 shadow-lg hover:shadow-xl transition-all`}
            >
              <div className="flex items-center justify-between mb-3">
                <p className="text-3xl">{stat.icon}</p>
              </div>
              <p className="text-xs text-slate-400 tracking-[0.2em] font-semibold mb-2">{stat.label.toUpperCase()}</p>
              <p className="text-4xl font-black text-white mb-1">{stat.value}</p>
              <p className="text-xs text-slate-400">{stat.subtext}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Notification Alert */}
        <AnimatePresence>
          {message && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`glass-panel rounded-2xl border p-4 flex items-center justify-between text-sm shadow-2xl ${
                message.type === 'success'
                  ? 'border-emerald-400/40 bg-emerald-500/20'
                  : 'border-red-400/40 bg-red-500/20'
              }`}
            >
              <div className="flex items-center gap-3 text-white">
                <span className="text-lg">{message.type === 'success' ? '✅' : '❌'}</span>
                <span className="font-medium">{message.text}</span>
              </div>
              <button 
                onClick={() => setMessage(null)} 
                className="ml-4 text-white hover:bg-white/10 rounded-lg px-2 py-1 transition"
              >
                ✕
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Controls & Filters */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.25 }}
          className="glass-panel rounded-2xl border border-white/10 p-5 space-y-4"
        >
          <div className="flex flex-col lg:flex-row gap-3">
            {/* Search */}
            <div className="relative flex-1">
              <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search by username, email, or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 pl-10 text-sm text-white placeholder-slate-400 focus:border-amber-500/50 focus:outline-none focus:ring-2 focus:ring-amber-500/20 transition"
              />
            </div>

            {/* Filters */}
            <div className="flex gap-2 flex-wrap">
              <select
                value={accessFilter}
                onChange={(e) => setAccessFilter(e.target.value)}
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:border-amber-500/50 focus:outline-none focus:ring-2 focus:ring-amber-500/20 transition"
              >
                <option value="all">All Access Levels</option>
                <option value="admin">🔑 Full Access</option>
                <option value="member">🔓 Limited Access</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:border-amber-500/50 focus:outline-none focus:ring-2 focus:ring-amber-500/20 transition"
              >
                <option value="all">All Status</option>
                <option value="active">🟢 Active</option>
                <option value="inactive">⚫ Inactive</option>
              </select>

              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:border-amber-500/50 focus:outline-none focus:ring-2 focus:ring-amber-500/20 transition"
              >
                <option value="username">Sort: Name</option>
                <option value="access">Sort: Access Level</option>
                <option value="status">Sort: Status</option>
              </select>

              {(searchQuery || accessFilter !== 'all' || statusFilter !== 'all') && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  onClick={() => {
                    setSearchQuery('')
                    setAccessFilter('all')
                    setStatusFilter('all')
                  }}
                  className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-slate-300 transition hover:bg-white/10"
                >
                  Clear
                </motion.button>
              )}

              <div className="flex gap-1 border border-white/10 rounded-xl p-1 bg-white/5">
                <button
                  onClick={() => setViewMode('detailed')}
                  className={`px-3 py-2 rounded-lg text-sm font-semibold transition ${
                    viewMode === 'detailed' 
                      ? 'bg-amber-500/30 text-amber-300 border border-amber-500/40' 
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  📋 Detailed
                </button>
                <button
                  onClick={() => setViewMode('compact')}
                  className={`px-3 py-2 rounded-lg text-sm font-semibold transition ${
                    viewMode === 'compact' 
                      ? 'bg-amber-500/30 text-amber-300 border border-amber-500/40' 
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  📊 Compact
                </button>
              </div>
            </div>
          </div>

          {(searchQuery || accessFilter !== 'all' || statusFilter !== 'all') && (
            <motion.p 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-xs text-slate-400"
            >
              Showing <span className="font-semibold text-white">{filteredUsers.length}</span> of <span className="font-semibold text-white">{users.length}</span> users
            </motion.p>
          )}
        </motion.div>

        {/* Main Content - Empty State */}
        {filteredUsers.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-panel rounded-3xl border border-white/10 flex h-96 items-center justify-center"
          >
            <div className="text-center">
              <motion.div 
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="text-7xl mb-4"
              >
                🔐
              </motion.div>
              <p className="text-xl font-bold text-white mb-2">No users found</p>
              <p className="text-slate-400">
                {searchQuery || accessFilter !== 'all' || statusFilter !== 'all' 
                  ? 'Try adjusting your search or filters' 
                  : 'Create your first user to get started'}
              </p>
            </div>
          </motion.div>
        ) : viewMode === 'detailed' ? (
          // Detailed View - Access Info Cards
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.25 }}
            className="grid grid-cols-1 gap-4"
          >
            <AnimatePresence>
              {filteredUsers.map((user, idx) => {
                const accessInfo = getAccessInfo(user.role, user.is_active)
                const permissions = getAccessPermissions(user.role, user.is_active)
                
                return (
                  <motion.div
                    key={user.username}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.03 }}
                    className="glass-card rounded-2xl border border-white/10 bg-gradient-to-r from-white/5 to-white/2 p-6 hover:border-white/20 transition-all"
                  >
                    <div className="flex items-start justify-between gap-6">
                      {/* User Info */}
                      <div className="flex-1">
                        <div className="flex items-center gap-4 mb-4">
                          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-amber-500/20 to-amber-600/30 border border-amber-400/40 flex items-center justify-center text-2xl">
                            👤
                          </div>
                          <div>
                            <h3 className="text-lg font-bold text-white">{user.username}</h3>
                            {user.full_name && (
                              <p className="text-sm text-slate-400">{user.full_name}</p>
                            )}
                          </div>
                        </div>
                        
                        <div className="space-y-2 mb-4">
                          <p className="text-xs text-slate-500">EMAIL</p>
                          <p className="text-sm text-slate-300 break-all">{user.email}</p>
                        </div>
                      </div>

                      {/* Access Level Badge */}
                      <div className="text-center">
                        <div className={`inline-flex flex-col items-center rounded-xl border ${accessInfo.badge} p-4 mb-3`}>
                          <p className="text-4xl mb-2">{accessInfo.icon}</p>
                          <p className={`text-sm font-bold ${accessInfo.color}`}>{accessInfo.level}</p>
                        </div>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => {
                            setSelectedUserDetail(user)
                            setEditAccessData({ role: user.role, is_active: user.is_active })
                            setShowAccessModal(true)
                          }}
                          className="text-xs font-semibold text-amber-300 hover:text-amber-200 transition"
                        >
                          Change Access
                        </motion.button>
                      </div>
                    </div>

                    {/* Permissions List */}
                    <div className="mt-6 pt-6 border-t border-white/10">
                      <p className="text-xs font-semibold text-slate-400 tracking-[0.2em] mb-3">PERMISSIONS</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {permissions.permissions.length > 0 ? (
                          permissions.permissions.map((perm, idx) => (
                            <motion.div
                              key={idx}
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ delay: idx * 0.05 }}
                              className="flex items-center gap-2 text-xs text-slate-300"
                            >
                              <span className="text-emerald-400">✓</span>
                              <span>{perm}</span>
                            </motion.div>
                          ))
                        ) : (
                          <p className="text-xs text-slate-500 italic col-span-2">No permissions granted</p>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </motion.div>
        ) : (
          // Compact Table View
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.25 }}
            className="glass-panel rounded-3xl border border-white/10 overflow-hidden shadow-2xl"
          >
            <div className="overflow-auto max-h-[700px]">
              <table className="w-full text-white">
                <thead className="sticky top-0 bg-white/5 border-b border-white/10">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-[0.2em] text-slate-300">User</th>
                    <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-[0.2em] text-slate-300">Access Level</th>
                    <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-[0.2em] text-slate-300">Status</th>
                    <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-[0.2em] text-slate-300">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  <AnimatePresence>
                    {filteredUsers.map((user, idx) => {
                      const accessInfo = getAccessInfo(user.role, user.is_active)
                      
                      return (
                        <motion.tr
                          key={user.username}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: idx * 0.02 }}
                          className="hover:bg-white/5 transition"
                        >
                          <td className="px-6 py-4">
                            <div>
                              <p className="font-semibold text-white">{user.username}</p>
                              <p className="text-xs text-slate-500">{user.email}</p>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <motion.span 
                              whileHover={{ scale: 1.05 }}
                              className={`inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-bold ${accessInfo.badge}`}
                            >
                              {accessInfo.icon} {accessInfo.level}
                            </motion.span>
                          </td>
                          <td className="px-6 py-4 text-center">
                            <motion.span 
                              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold border ${
                                user.is_active
                                  ? 'border-emerald-400/40 bg-emerald-500/20 text-emerald-300'
                                  : 'border-red-400/40 bg-red-500/20 text-red-300'
                              }`}
                            >
                              {user.is_active ? '🟢 Active' : '🔴 Inactive'}
                            </motion.span>
                          </td>
                          <td className="px-6 py-4 text-center">
                            <motion.button
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                              onClick={() => {
                                setSelectedUserDetail(user)
                                setEditAccessData({ role: user.role, is_active: user.is_active })
                                setShowAccessModal(true)
                              }}
                              className="rounded-lg bg-amber-500/20 border border-amber-500/40 px-3 py-1.5 text-xs font-semibold text-amber-300 transition hover:bg-amber-500/30"
                            >
                              Manage
                            </motion.button>
                          </td>
                        </motion.tr>
                      )
                    })}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </div>

      {/* Create User Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            onClick={() => setShowCreateModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="glass-panel w-full max-w-md rounded-3xl border border-white/10 p-8 shadow-2xl text-white"
            >
              <h3 className="text-2xl font-black tracking-tight mb-6">➕ Add User Account</h3>
              
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">Username *</label>
                  <input
                    type="text"
                    value={createData.username}
                    onChange={(e) => setCreateData({ ...createData, username: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder-slate-400 focus:border-amber-500/50 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
                    placeholder="john_doe"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">Email *</label>
                  <input
                    type="email"
                    value={createData.email}
                    onChange={(e) => setCreateData({ ...createData, email: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder-slate-400 focus:border-amber-500/50 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
                    placeholder="john@company.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">Password *</label>
                  <input
                    type="password"
                    value={createData.password}
                    onChange={(e) => setCreateData({ ...createData, password: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder-slate-400 focus:border-amber-500/50 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
                    placeholder="••••••••"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">Full Name</label>
                  <input
                    type="text"
                    value={createData.full_name}
                    onChange={(e) => setCreateData({ ...createData, full_name: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder-slate-400 focus:border-amber-500/50 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
                    placeholder="John Doe"
                  />
                </div>
              </div>

              <div className="glass-card rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 mb-6">
                <p className="text-xs text-amber-300 font-semibold mb-1">ℹ️ Info</p>
                <p className="text-xs text-slate-300">New users start with Limited Access. Promote to Full Access in the access panel.</p>
              </div>

              <div className="flex gap-3">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleCreateUser}
                  disabled={loading || !createData.username || !createData.email || !createData.password}
                  className="flex-1 rounded-lg bg-gradient-to-r from-emerald-500/40 to-green-500/40 px-4 py-3 font-semibold text-white transition hover:from-emerald-500/50 hover:to-green-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Creating...' : 'Create User'}
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-semibold text-white transition hover:bg-white/10"
                >
                  Cancel
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Access Control Modal */}
      <AnimatePresence>
        {showAccessModal && selectedUserDetail && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            onClick={() => setShowAccessModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="glass-panel w-full max-w-md rounded-3xl border border-white/10 p-8 shadow-2xl text-white"
            >
              <h3 className="text-2xl font-black tracking-tight mb-2">🔐 Access Control</h3>
              <p className="text-xs text-slate-400 mb-6">{selectedUserDetail.username}</p>

              <div className="space-y-6 mb-8">
                {/* Access Level */}
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-4">Access Level</label>
                  <div className="grid grid-cols-2 gap-3">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setEditAccessData({ ...editAccessData, role: 'user', is_active: true })}
                      className={`rounded-xl border-2 p-4 text-center transition ${
                        editAccessData.role === 'user' && editAccessData.is_active
                          ? 'border-emerald-500/60 bg-emerald-500/20'
                          : 'border-white/10 bg-white/5 hover:border-white/20'
                      }`}
                    >
                      <p className="text-3xl mb-2">🔓</p>
                      <p className="text-sm font-bold">Limited Access</p>
                      <p className="text-xs text-slate-400 mt-1">Standard permissions</p>
                    </motion.button>

                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setEditAccessData({ ...editAccessData, role: 'admin', is_active: true })}
                      className={`rounded-xl border-2 p-4 text-center transition ${
                        editAccessData.role === 'admin'
                          ? 'border-amber-500/60 bg-amber-500/20'
                          : 'border-white/10 bg-white/5 hover:border-white/20'
                      }`}
                    >
                      <p className="text-3xl mb-2">🔑</p>
                      <p className="text-sm font-bold">Full Access</p>
                      <p className="text-xs text-slate-400 mt-1">Admin privileges</p>
                    </motion.button>
                  </div>
                </div>

                {/* Account Status */}
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-4">Account Status</label>
                  <div className="grid grid-cols-2 gap-3">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setEditAccessData({ ...editAccessData, is_active: true })}
                      className={`rounded-xl border-2 p-4 text-center transition ${
                        editAccessData.is_active
                          ? 'border-emerald-500/60 bg-emerald-500/20'
                          : 'border-white/10 bg-white/5 hover:border-white/20'
                      }`}
                    >
                      <p className="text-2xl mb-2">🟢</p>
                      <p className="text-sm font-bold">Active</p>
                    </motion.button>

                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setEditAccessData({ ...editAccessData, is_active: false })}
                      className={`rounded-xl border-2 p-4 text-center transition ${
                        !editAccessData.is_active
                          ? 'border-red-500/60 bg-red-500/20'
                          : 'border-white/10 bg-white/5 hover:border-white/20'
                      }`}
                    >
                      <p className="text-2xl mb-2">🔴</p>
                      <p className="text-sm font-bold">Revoked</p>
                    </motion.button>
                  </div>
                </div>
              </div>

              {/* Preview Permissions */}
              {editAccessData.is_active && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass-card rounded-xl border border-white/10 bg-white/5 p-4 mb-6"
                >
                  <p className="text-xs font-semibold text-slate-400 tracking-[0.2em] mb-3">PERMISSIONS</p>
                  {getAccessPermissions(editAccessData.role, true).permissions.map((perm, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs text-slate-300 mb-1">
                      <span className="text-emerald-400">✓</span> {perm}
                    </div>
                  ))}
                </motion.div>
              )}

              <div className="flex gap-3">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleUpdateAccess}
                  disabled={loading}
                  className="flex-1 rounded-lg bg-gradient-to-r from-amber-500/40 to-amber-600/40 px-4 py-3 font-semibold text-white transition hover:from-amber-500/50 hover:to-amber-600/50 disabled:opacity-50"
                >
                  {loading ? 'Updating...' : 'Update Access'}
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setShowAccessModal(false)}
                  className="flex-1 rounded-lg border border-white/10 bg-white/5 px-4 py-3 font-semibold text-white transition hover:bg-white/10"
                >
                  Cancel
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default UserManagement
