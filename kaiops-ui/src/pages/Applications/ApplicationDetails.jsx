import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import applicationService from '../../services/applicationService';
import ConfirmDialog from '../../components/ConfirmDialog';

const cleanBase = (value = '') => value.replace(/\/$/, '');

const buildUrl = (base, suffix) => {
  if (!suffix) return null;
  if (suffix.startsWith('http')) return suffix;
  if (!base) return null;
  return `${cleanBase(base)}/${suffix.replace(/^\//, '')}`;
};

const getGithubUrl = (repo) => buildUrl(import.meta.env.VITE_GITHUB_BASE_URL || 'https://github.com', repo);
const getGrafanaUrl = (dashboard) => buildUrl(import.meta.env.VITE_GRAFANA_URL, dashboard);
const getArgoCDUrl = (appName) => {
  if (!appName && !import.meta.env.VITE_ARGOCD_BASE_URL) return null;
  if (!appName) return cleanBase(import.meta.env.VITE_ARGOCD_BASE_URL);
  const base = cleanBase(import.meta.env.VITE_ARGOCD_BASE_URL || '');
  if (!base) return null;
  return `${base}/applications/${encodeURIComponent(appName)}`;
};

const formatDate = (value) => {
  if (!value) return '—';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
};

const ApplicationDetails = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const { isAdmin, isTeamLead } = useAuth();

  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const loadApplication = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await applicationService.getApplication(id);
      setApplication(data);
    } catch (err) {
      console.error('Error loading application:', err);
      setError('Failed to load application details. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadApplication();
  }, [loadApplication]);

  const handleToggleStatus = async () => {
    if (!isAdmin && !isTeamLead) {
      alert('You do not have permission to toggle application status.');
      return;
    }

    try {
      await applicationService.toggleStatus(id);
      await loadApplication();
    } catch (err) {
      console.error('Error toggling status:', err);
      alert('Failed to toggle status. Please try again.');
    }
  };

  const handleDelete = () => {
    if (!isAdmin) return;
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    try {
      setDeleting(true);
      await applicationService.deleteApplication(id);
      navigate('/applications');
    } catch (err) {
      console.error('Error deleting application:', err);
      alert('Failed to delete application.');
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const openLink = (url) => {
    if (!url) return;
    if (typeof window !== 'undefined') {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  if (loading) {
    return (
      <div className="glass-panel h-[90vh] overflow-auto">
        <div className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-10">
          <div className="rounded-3xl border border-white/5 bg-black/30 p-8">
            <div className="h-3 w-24 rounded-full bg-white/10" />
            <div className="mt-6 space-y-4">
              {[...Array(4)].map((_, idx) => (
                <div key={idx} className="h-4 rounded-full bg-white/10" />
              ))}
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {[...Array(4)].map((_, idx) => (
              <div key={idx} className="h-32 rounded-2xl border border-white/5 bg-black/20" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel h-[90vh] overflow-auto">
        <div className="mx-auto flex max-w-3xl flex-col items-center gap-4 px-6 py-16 text-center">
          <div className="rounded-3xl border border-rose-500/20 bg-rose-500/10 px-6 py-5 text-rose-100">
            <p className="text-sm tracking-[0.3em]">ERROR</p>
            <p className="mt-2 text-xl font-semibold text-white">{error}</p>
          </div>
          <button
            onClick={loadApplication}
            className="rounded-2xl border border-white/10 px-6 py-2 text-sm font-semibold text-gray-200 transition-colors hover:border-kaiops-primary hover:text-white"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!application) {
    return (
      <div className="glass-panel h-[90vh] overflow-auto">
        <div className="mx-auto max-w-3xl px-6 py-16 text-center text-white">
          <p className="text-lg font-semibold">Application not found.</p>
          <button
            onClick={() => navigate('/applications')}
            className="mt-6 rounded-2xl border border-white/10 px-6 py-2 text-sm font-semibold text-gray-200 transition-colors hover:border-kaiops-primary hover:text-white"
          >
            Back to applications
          </button>
        </div>
      </div>
    );
  }

  const statusTheme = application.status === 'active'
    ? {
        label: 'ACTIVE',
        pill: 'border border-emerald-400/40 bg-emerald-500/15 text-emerald-200',
        dot: 'bg-emerald-300'
      }
    : {
        label: 'INACTIVE',
        pill: 'border border-slate-500/40 bg-slate-600/20 text-slate-200',
        dot: 'bg-slate-300'
      };

  const githubUrl = getGithubUrl(application.github_repo);
  const grafanaUrl = getGrafanaUrl(application.grafana_dashboard);
  const argoUrl = getArgoCDUrl(application.argocd_app_name);

  const quickInfo = [
    {
      label: 'STATUS',
      value: statusTheme.label,
      icon: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    {
      label: 'CLUSTER',
      value: application.gke_cluster_name || '—',
      icon: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
      )
    },
    {
      label: 'NAMESPACE',
      value: application.namespace || 'default',
      icon: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
        </svg>
      )
    },
    {
      label: 'OWNER',
      value: application.application_owner || 'Unassigned',
      icon: (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    }
  ];

  const infoSections = [
    {
      title: 'Deployment Surface',
      accent: 'from-kaiops-secondary to-kaiops-primary',
      icon: (
        <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2m-2 0a2 2 0 00-2 2v4a2 2 0 002 2h2a2 2 0 002-2v-4" />
        </svg>
      ),
      items: [
        {
          label: 'Namespace',
          value: application.namespace || 'default',
          monospace: true
        },
        {
          label: 'Cluster',
          value: application.gke_cluster_name || '—'
        },
        {
          label: 'ArgoCD Application',
          value: application.argocd_app_name || '—',
          action: argoUrl ? () => openLink(argoUrl) : null
        }
      ]
    },
    {
      title: 'Observability & Ownership',
      accent: 'from-orange-500 to-pink-500',
      icon: (
        <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19V6h13M9 10H4a2 2 0 00-2 2v7h7" />
        </svg>
      ),
      items: [
        {
          label: 'Grafana Dashboard',
          value: application.grafana_dashboard || '—',
          action: grafanaUrl ? () => openLink(grafanaUrl) : null
        },
        {
          label: 'GitHub Repository',
          value: application.github_repo || '—',
          action: githubUrl ? () => openLink(githubUrl) : null
        },
        {
          label: 'Application Owner',
          value: application.application_owner || 'Unassigned'
        }
      ]
    }
  ];

  const metadata = [
    { label: 'Application ID', value: application.id, monospace: true },
    { label: 'Created By', value: application.created_by || '—' },
    { label: 'Created At', value: formatDate(application.created_at) },
    { label: 'Last Updated By', value: application.updated_by || '—' },
    { label: 'Last Updated At', value: formatDate(application.updated_at) }
  ];

  return (
    <div className="h-full w-full overflow-y-auto custom-scrollbar">
      <div className="mx-auto max-w-6xl space-y-8 px-6 py-6">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <button
            onClick={() => navigate('/applications')}
            className="inline-flex items-center gap-2 text-gray-400 transition-colors hover:text-white"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7 7-7" />
            </svg>
            All applications
          </button>
          <span>/</span>
          <span className="text-white font-semibold">{application.application_name}</span>
        </div>

        <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-white/10 to-black/20 p-6 shadow-2xl">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="flex-1 space-y-4">
              <div>
                <p className="text-[11px] uppercase tracking-[0.4em] text-kaiops-secondary/80">KaiOPS Asset</p>
                <div className="mt-2 flex flex-wrap items-center gap-3">
                  <h1 className="text-3xl font-semibold text-white">{application.application_name}</h1>
                  <span className={`inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-[11px] font-semibold tracking-[0.3em] ${statusTheme.pill}`}>
                    <span className={`h-2.5 w-2.5 rounded-full shadow-[0_0_12px] ${statusTheme.dot}`} />
                    {statusTheme.label}
                  </span>
                </div>
              </div>

              {application.namespace && (
                <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1 text-[11px] text-gray-300">
                  <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                  Namespace • {application.namespace}
                </span>
              )}

              {application.description && (
                <p className="text-gray-300">{application.description}</p>
              )}

              {application.tags && application.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {application.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-kaiops-primary/40 bg-kaiops-primary/15 px-3 py-1 text-[11px] uppercase tracking-[0.35em] text-kaiops-primary"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="flex flex-col gap-3 lg:min-w-[240px]">
              {(isAdmin || isTeamLead) && (
                <>
                  <button
                    onClick={() => navigate(`/applications/${id}/edit`)}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-kaiops-secondary to-kaiops-primary px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-kaiops-primary/40 transition-all hover:-translate-y-0.5"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Edit application
                  </button>

                  <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-2">
                    <span className="text-xs text-gray-400">
                      {application.status === 'active' ? 'Active' : 'Inactive'}
                    </span>
                    <button
                      onClick={handleToggleStatus}
                      className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-kaiops-primary/40 ${
                        application.status === 'active' ? 'bg-emerald-400/60' : 'bg-slate-600'
                      }`}
                    >
                      <span
                        className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
                          application.status === 'active' ? 'translate-x-5' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </>
              )}

              {isAdmin && (
                <button
                  onClick={handleDelete}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl border border-rose-500/40 bg-rose-500/15 px-4 py-2 text-sm font-semibold text-rose-100 transition-colors hover:bg-rose-500/25"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Delete application
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickInfo.map((info) => (
            <div key={info.label} className="rounded-2xl border border-white/10 bg-black/30 p-4 shadow-lg">
              <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.3em] text-gray-500">
                {info.icon}
                {info.label}
              </div>
              <p className="mt-2 truncate text-lg font-semibold text-white" title={info.value}>
                {info.value}
              </p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {infoSections.map((section) => (
            <div key={section.title} className="rounded-3xl border border-white/10 bg-black/30 p-6 shadow-lg">
              <div className="mb-5 flex items-center gap-3 border-b border-white/5 pb-4">
                <div className={`flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${section.accent} shadow-lg`}>
                  {section.icon}
                </div>
                <h3 className="text-lg font-semibold text-white">{section.title}</h3>
              </div>
              <div className="space-y-4">
                {section.items.map((item) => (
                  <div key={`${section.title}-${item.label}`} className="rounded-2xl border border-white/5 bg-white/5 p-4">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="text-[11px] uppercase tracking-[0.3em] text-gray-500">{item.label}</p>
                        <p className={`text-white font-semibold ${item.monospace ? 'font-mono text-sm' : 'text-base'}`} title={item.value}>
                          {item.value}
                        </p>
                      </div>
                      {item.action && (
                        <button
                          onClick={item.action}
                          className="inline-flex items-center gap-1 rounded-xl border border-white/15 px-3 py-1.5 text-xs font-semibold text-gray-200 transition-colors hover:border-kaiops-primary hover:text-white"
                        >
                          <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                          {item.actionLabel || 'Open'}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="rounded-3xl border border-white/10 bg-black/30 p-6 shadow-lg">
          <h3 className="text-lg font-semibold text-white">Metadata</h3>
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {metadata.map((item) => (
              <div key={item.label} className="rounded-2xl border border-white/5 bg-white/5 p-4">
                <p className="text-[11px] uppercase tracking-[0.3em] text-gray-500">{item.label}</p>
                <p className={`mt-2 break-words text-white ${item.monospace ? 'font-mono text-sm' : 'font-semibold'}`}>
                  {item.value}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              onClick={() => {
                if (navigator?.clipboard) {
                  navigator.clipboard.writeText(application.id);
                  alert('Application ID copied to clipboard!');
                }
              }}
              className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-gray-200 transition-colors hover:border-kaiops-primary hover:text-white"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy ID
            </button>
          </div>
        </div>
      </div>

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={confirmDelete}
        title="Delete Application"
        message={
          <div>
            <p className="mb-2">
              Are you sure you want to delete <strong>"{application?.application_name}"</strong>?
            </p>
            <p className="text-sm text-gray-400">
              This action cannot be undone. The application and all associated data will be permanently removed.
            </p>
          </div>
        }
        confirmText={deleting ? 'Deleting...' : 'Delete Application'}
        cancelText="Cancel"
        type="danger"
      />
    </div>
  );
};

export default ApplicationDetails;
