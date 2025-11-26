import { useMemo, useState } from 'react'
import './ApplicationsTable.css'

const ITEMS_PER_PAGE = 10

const STATUS_META = {
  active: { label: 'Active', emoji: '🟢', className: 'status-pill active' },
  inactive: { label: 'Inactive', emoji: '🔴', className: 'status-pill inactive' },
  pending: { label: 'Pending', emoji: '🟡', className: 'status-pill pending' },
  default: { label: 'Unknown', emoji: '⚪', className: 'status-pill unknown' }
}

function ApplicationsTable({ data }) {
  const [page, setPage] = useState(1)

  const normalizedData = useMemo(() => {
    if (!data) return { applications: [], stats: {}, total: 0 }
    if (typeof data === 'string') {
      try {
        return JSON.parse(data)
      } catch (error) {
        console.error('Failed to parse applications data', error)
        return { applications: [], stats: {}, total: 0 }
      }
    }
    return data
  }, [data])

  const applications = normalizedData.applications || []
  const totalPages = Math.max(1, Math.ceil(applications.length / ITEMS_PER_PAGE))
  const offset = (page - 1) * ITEMS_PER_PAGE
  const currentPageApps = applications.slice(offset, offset + ITEMS_PER_PAGE)

  const integrationSummary = useMemo(() => {
    const summary = { github: 0, argocd: 0, grafana: 0 }
    applications.forEach((app) => {
      if (app.github_repo && app.github_repo !== 'N/A') summary.github += 1
      if (app.argocd_app_name && app.argocd_app_name !== 'N/A') summary.argocd += 1
      if (app.grafana_dashboard && app.grafana_dashboard !== 'N/A') summary.grafana += 1
    })
    return summary
  }, [applications])

  if (!applications.length) {
    return (
      <div className="apps-table-container">
        <p className="empty-state">No applications registered yet.</p>
      </div>
    )
  }

  const renderStatus = (statusValue) => {
    const key = (statusValue || '').toLowerCase()
    const meta = STATUS_META[key] || STATUS_META.default
    return <span className={meta.className}>{meta.emoji} {meta.label}</span>
  }

  return (
    <div className="apps-table-container">
      <header className="apps-table-header">
        <h3>📊 Registered Applications</h3>
        <span className="badge">{normalizedData.total || applications.length} total</span>
      </header>

      <div className="table-scroll">
        <table className="apps-table">
          <thead>
            <tr>
              <th>Application</th>
              <th>Owner</th>
              <th>Cluster</th>
              <th>Status</th>
              <th>GitHub</th>
              <th>ArgoCD</th>
              <th>Grafana</th>
            </tr>
          </thead>
          <tbody>
            {currentPageApps.map((app) => (
              <tr key={app.application_name}>
                <td className="app-name">{app.application_name}</td>
                <td>{app.application_owner}</td>
                <td>{app.gke_cluster_name}</td>
                <td>{renderStatus(app.status)}</td>
                <td>{app.github_repo && app.github_repo !== 'N/A' ? '✅' : '⚠️'}</td>
                <td>{app.argocd_app_name && app.argocd_app_name !== 'N/A' ? '✅' : '⚠️'}</td>
                <td>{app.grafana_dashboard && app.grafana_dashboard !== 'N/A' ? '✅' : '⚠️'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="pager"
            onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
            disabled={page === 1}
          >
            ← Prev
          </button>
          <span className="pager-info">Page {page} of {totalPages}</span>
          <button
            className="pager"
            onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))}
            disabled={page === totalPages}
          >
            Next →
          </button>
        </div>
      )}

      <section className="integrations">
        <h4>🔌 Integration Summary</h4>
        <ul>
          <li>📦 GitHub configured: {integrationSummary.github}/{applications.length}</li>
          <li>🚀 ArgoCD configured: {integrationSummary.argocd}/{applications.length}</li>
          <li>📊 Grafana configured: {integrationSummary.grafana}/{applications.length}</li>
        </ul>
      </section>

      <section className="stats">
        <h4>📈 Status Overview</h4>
        <ul>
          <li>Active: {normalizedData?.stats?.active ?? '—'}</li>
          <li>Inactive: {normalizedData?.stats?.inactive ?? '—'}</li>
          <li>Pending: {normalizedData?.stats?.pending ?? '—'}</li>
        </ul>
      </section>
    </div>
  )
}

export default ApplicationsTable
