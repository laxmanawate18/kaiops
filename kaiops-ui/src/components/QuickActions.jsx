function QuickActions({ onSendMessage }) {
  const actions = [
    {
      title: 'Application Health',
      prompt: 'Get my Application health',
      description: 'Live readiness across all clusters.',
      gradient: 'from-emerald-500/30 via-transparent to-cyan-500/10',
      iconWrap: 'border-emerald-400/40 shadow-[0_0_30px_rgba(16,185,129,0.35)]',
      icon: (
        <svg className="w-6 h-6 text-emerald-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
      )
    },
    {
      title: 'Github Status',
      prompt: 'Get latest Commit',
      description: 'Surface recent merges & authors instantly.',
      gradient: 'from-indigo-500/20 via-transparent to-purple-500/20',
      iconWrap: 'border-indigo-400/40 shadow-[0_0_30px_rgba(99,102,241,0.35)]',
      icon: (
        <svg className="w-6 h-6 text-indigo-200" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.47.087.683-.207.683-.455 0-.224-.007-.975-.011-1.702-2.782.602-3.369-1.34-3.369-1.34-.454-1.158-1.11-1.465-1.11-1.465-.908-.618.069-.606.069-.606 1.003.07 1.531 1.032 1.531 1.032.892 1.529 2.341 1.089 2.91.832.092-.647.35-1.089.636-1.338-2.22-.253-4.555-1.113-4.555-4.956 0-1.091.39-1.984 1.029-2.682-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.7.114 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.099 2.651.64.698 1.028 1.591 1.028 2.682 0 3.853-2.339 4.69-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .247.214.543.688.453C21.137 20.28 24 16.525 24 12.017 24 6.484 19.522 2 12 2Z" clipRule="evenodd"></path>
        </svg>
      )
    },
    {
      title: 'ArgoCD',
      prompt: 'Can I get my deployment status from Argocd?',
      description: 'Check rollout waves & sync drift.',
      gradient: 'from-sky-500/30 via-transparent to-blue-500/10',
      iconWrap: 'border-sky-400/40 shadow-[0_0_30px_rgba(56,189,248,0.35)]',
      icon: (
        <svg className="w-6 h-6 text-sky-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
        </svg>
      )
    },
    {
      title: 'Grafana Status',
      prompt: 'Get Grafana Status',
      description: 'Pulse dashboards & alert streams.',
      gradient: 'from-amber-500/25 via-transparent to-orange-500/10',
      iconWrap: 'border-amber-400/40 shadow-[0_0_30px_rgba(245,158,11,0.35)]',
      icon: (
        <svg className="w-6 h-6 text-amber-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
        </svg>
      )
    },
    {
      title: 'Health Report for Application',
      prompt: 'Could you please provide a health status report for the application?',
      description: 'Comprehensive application health diagnostics & status.',
      gradient: 'from-teal-500/30 via-transparent to-cyan-500/15',
      iconWrap: 'border-teal-400/40 shadow-[0_0_30px_rgba(20,184,166,0.35)]',
      icon: (
        <svg className="w-6 h-6 text-teal-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
        </svg>
      )
    },
    {
      title: 'RCA for Application',
      prompt: 'Could you please provide a RCA for the application?',
      description: 'Root cause analysis & incident investigation.',
      gradient: 'from-orange-500/25 via-transparent to-red-500/15',
      iconWrap: 'border-orange-400/40 shadow-[0_0_30px_rgba(234,88,12,0.35)]',
      icon: (
        <svg className="w-6 h-6 text-orange-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7"></path>
        </svg>
      )
    }
  ]

  return (
    <div className="w-full max-w-3xl text-white">
      <div className="text-center mb-8">
        <p className="text-[11px] uppercase tracking-[0.5em] text-kaiops-primary/80 mb-2">Mission Brief</p>
        <h2 className="text-2xl font-semibold text-white">How can KaiOPS assist?</h2>
        <p className="text-gray-400 text-sm">Trigger curated playbooks and telemetry sweeps in one tap.</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {actions.map((action, index) => (
          <button
            key={action.title}
            onClick={() => onSendMessage(action.prompt)}
            aria-label={`Ask about ${action.title}`}
            className={`relative overflow-hidden rounded-2xl border border-white/10 bg-black/50 p-5 text-left transition-all duration-300 hover:-translate-y-1 hover:border-kaiops-primary/40 hover:shadow-[0_25px_70px_rgba(0,240,255,0.25)] focus:outline-none focus:ring-2 focus:ring-kaiops-primary/40`}
          >
            <div className={`absolute inset-0 bg-gradient-to-r ${action.gradient} blur-3xl opacity-40`}></div>
            <div className="relative flex items-start gap-4">
              <div className={`h-12 w-12 rounded-2xl border ${action.iconWrap} bg-white/5 flex items-center justify-center`}> 
                {action.icon}
              </div>
              <div>
                <p className="text-base font-semibold text-white mb-1">{action.title}</p>
                <p className="text-xs text-gray-400 leading-relaxed">{action.description}</p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

export default QuickActions
