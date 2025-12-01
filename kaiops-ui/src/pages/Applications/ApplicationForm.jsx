import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import applicationService from '../../services/applicationService';

const CLOUD_PROVIDERS = [
  { value: 'gcp', label: 'Google Cloud Platform', icon: '☁️' },
  { value: 'azure', label: 'Microsoft Azure', icon: '⬛' },
  { value: 'aws', label: 'Amazon Web Services', icon: '🟠' },
];

const CRITICALITY_LEVELS = [
  { value: 'critical', label: 'Critical', color: 'text-rose-400 border-rose-500/30 bg-rose-500/10' },
  { value: 'high', label: 'High', color: 'text-amber-400 border-amber-500/30 bg-amber-500/10' },
  { value: 'medium', label: 'Medium', color: 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10' },
  { value: 'low', label: 'Low', color: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' },
];

const ApplicationForm = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const { isAdmin, isTeamLead, user } = useAuth();
  const isEditMode = !!id;

  // Form state
  const [formData, setFormData] = useState({
    cloud_provider: 'gcp',
    application_name: '',
    application_owner: '',
    status: 'active',
    github_repo: '',
    argocd_app_name: '',
    grafana_dashboard: '',
    grafana_alert_name: '',
    description: '',
    application_criticality: 'medium',
    
    // GCP Fields
    gcp_project_id: '',
    gcp_log_resource: '',
    gke_cluster_name: '',
    deployment_name: '',
    pod_name: '',
    namespace: '',
    
    // Azure Fields
    azure_subscription_id: '',
    aks_cluster_name: '',
    azure_deployment_name: '',
    azure_pod_name: '',
    azure_namespace: '',
    azure_criticality: 'medium',
    resource_group: '',
    workspace: '',
    workspace_resource_group: '',
    ingress_name: '',
    ingress_public_ip: '',
    ingress_namespace: '',
    
    // AWS Fields
    aws_account_id: '',
    eks_cluster_name: '',
    cloudwatch_log_group_path: '',
    aws_deployment_name: '',
    aws_pod_name: '',
    aws_namespace: '',
    aws_criticality: 'medium',
    
    // Custom Metadata
    custom_metadata: [],
  });

  const [loading, setLoading] = useState(false);
  const [loadingApp, setLoadingApp] = useState(isEditMode);
  const [error, setError] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});
  const [newMetadata, setNewMetadata] = useState({ key: '', value: '' });

  // Load application data if editing
  useEffect(() => {
    if (isEditMode) {
      loadApplication();
    }
  }, [id]);

  const loadApplication = async () => {
    try {
      setLoadingApp(true);
      const app = await applicationService.getApplication(id);
      setFormData({
        cloud_provider: app.cloud_provider || 'gcp',
        application_name: app.application_name || '',
        application_owner: app.application_owner || '',
        status: app.status || 'active',
        github_repo: app.github_repo || '',
        argocd_app_name: app.argocd_app_name || '',
        grafana_dashboard: app.grafana_dashboard || '',
        grafana_alert_name: app.grafana_alert_name || '',
        description: app.description || '',
        application_criticality: app.application_criticality || 'medium',
        gcp_project_id: app.gcp_project_id || '',
        gcp_log_resource: app.gcp_log_resource || '',
        gke_cluster_name: app.gke_cluster_name || '',
        deployment_name: app.deployment_name || '',
        pod_name: app.pod_name || '',
        namespace: app.namespace || '',
        azure_subscription_id: app.azure_subscription_id || '',
        aks_cluster_name: app.aks_cluster_name || '',
        azure_deployment_name: app.azure_deployment_name || '',
        azure_pod_name: app.azure_pod_name || '',
        azure_namespace: app.azure_namespace || '',
        azure_criticality: app.azure_criticality || 'medium',
        resource_group: app.resource_group || '',
        workspace: app.workspace || '',
        workspace_resource_group: app.workspace_resource_group || '',
        ingress_name: app.ingress_name || '',
        ingress_public_ip: app.ingress_public_ip || '',
        ingress_namespace: app.ingress_namespace || '',
        aws_account_id: app.aws_account_id || '',
        eks_cluster_name: app.eks_cluster_name || '',
        cloudwatch_log_group_path: app.cloudwatch_log_group_path || '',
        aws_deployment_name: app.aws_deployment_name || '',
        aws_pod_name: app.aws_pod_name || '',
        aws_namespace: app.aws_namespace || '',
        aws_criticality: app.aws_criticality || 'medium',
        custom_metadata: app.custom_metadata || [],
      });
    } catch (err) {
      setError('Failed to load application. Please try again.');
    } finally {
      setLoadingApp(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => {
      const updated = { ...prev, [name]: value };
      
      // Auto-populate pod names based on deployment names
      if (name === 'deployment_name' && value) {
        updated.pod_name = value.replace(/-deploy$/, '') + '-xxx';
      }
      if (name === 'azure_deployment_name' && value) {
        updated.azure_pod_name = value.replace(/-deploy$/, '') + '-xxx';
      }
      if (name === 'aws_deployment_name' && value) {
        updated.aws_pod_name = value.replace(/-deploy$/, '') + '-xxx';
      }
      
      return updated;
    });
    
    if (validationErrors[name]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const errors = {};

    // Common required fields
    if (!formData.application_name.trim()) {
      errors.application_name = 'Application name is required';
    }
    if (!formData.application_owner.trim()) {
      errors.application_owner = 'Application owner is required';
    }
    if (!formData.github_repo.trim()) {
      errors.github_repo = 'GitHub repository is required';
    }
    if (!formData.argocd_app_name.trim()) {
      errors.argocd_app_name = 'ArgoCD application name is required';
    }
    if (!formData.grafana_dashboard.trim()) {
      errors.grafana_dashboard = 'Grafana dashboard is required';
    }
    if (!formData.grafana_alert_name.trim()) {
      errors.grafana_alert_name = 'Grafana alert name is required';
    }
    if (!formData.application_criticality) {
      errors.application_criticality = 'Application criticality is required';
    }
    if (!formData.cloud_provider) {
      errors.cloud_provider = 'Cloud provider is required';
    }

    // Cloud-specific validation
    if (formData.cloud_provider === 'gcp') {
      if (!formData.gcp_project_id.trim()) errors.gcp_project_id = 'GCP Project ID is required';
      if (!formData.gcp_log_resource.trim()) errors.gcp_log_resource = 'GCP log resource is required';
      if (!formData.gke_cluster_name.trim()) errors.gke_cluster_name = 'GKE cluster name is required';
      if (!formData.deployment_name.trim()) errors.deployment_name = 'Deployment name is required';
      if (!formData.pod_name.trim()) errors.pod_name = 'Pod name is required';
      if (!formData.namespace.trim()) errors.namespace = 'Namespace is required';
    }

    if (formData.cloud_provider === 'azure') {
      if (!formData.azure_subscription_id.trim()) errors.azure_subscription_id = 'Azure Subscription ID is required';
      if (!formData.aks_cluster_name.trim()) errors.aks_cluster_name = 'AKS cluster name is required';
      if (!formData.azure_deployment_name.trim()) errors.azure_deployment_name = 'Deployment name is required';
      if (!formData.azure_pod_name.trim()) errors.azure_pod_name = 'Pod name is required';
      if (!formData.azure_namespace.trim()) errors.azure_namespace = 'Namespace is required';
      if (!formData.resource_group.trim()) errors.resource_group = 'Resource group is required';
      if (!formData.workspace.trim()) errors.workspace = 'Workspace is required';
      if (!formData.workspace_resource_group.trim()) errors.workspace_resource_group = 'Workspace resource group is required';
      if (!formData.ingress_name.trim()) errors.ingress_name = 'Ingress name is required';
      if (!formData.ingress_public_ip.trim()) errors.ingress_public_ip = 'Ingress public IP is required';
      if (!formData.ingress_namespace.trim()) errors.ingress_namespace = 'Ingress namespace is required';
    }

    if (formData.cloud_provider === 'aws') {
      if (!formData.aws_account_id.trim()) errors.aws_account_id = 'AWS Account ID is required';
      if (!formData.eks_cluster_name.trim()) errors.eks_cluster_name = 'EKS cluster name is required';
      if (!formData.cloudwatch_log_group_path.trim()) errors.cloudwatch_log_group_path = 'CloudWatch log group path is required';
      if (!formData.aws_deployment_name.trim()) errors.aws_deployment_name = 'Deployment name is required';
      if (!formData.aws_pod_name.trim()) errors.aws_pod_name = 'Pod name is required';
      if (!formData.aws_namespace.trim()) errors.aws_namespace = 'Namespace is required';
    }

    return errors;
  };

  const handleAddMetadata = () => {
    if (newMetadata.key.trim() && newMetadata.value.trim()) {
      setFormData(prev => ({
        ...prev,
        custom_metadata: [...prev.custom_metadata, { key: newMetadata.key, value: newMetadata.value }]
      }));
      setNewMetadata({ key: '', value: '' });
    }
  };

  const handleRemoveMetadata = (index) => {
    setFormData(prev => ({
      ...prev,
      custom_metadata: prev.custom_metadata.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      setError('Please fix the validation errors before submitting.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Prepare data for submission
      const submitData = {
        cloud_provider: formData.cloud_provider,
        application_name: formData.application_name.trim(),
        application_owner: formData.application_owner.trim(),
        status: formData.status,
        github_repo: formData.github_repo.trim(),
        argocd_app_name: formData.argocd_app_name.trim(),
        grafana_dashboard: formData.grafana_dashboard.trim(),
        grafana_alert_name: formData.grafana_alert_name.trim(),
        application_criticality: formData.application_criticality,
        description: formData.description.trim(),
        custom_metadata: formData.custom_metadata,
      };

      // Add cloud-specific fields
      if (formData.cloud_provider === 'gcp') {
        submitData.gcp_project_id = formData.gcp_project_id.trim();
        submitData.gcp_log_resource = formData.gcp_log_resource.trim();
        submitData.gke_cluster_name = formData.gke_cluster_name.trim();
        submitData.deployment_name = formData.deployment_name.trim();
        submitData.pod_name = formData.pod_name.trim();
        submitData.namespace = formData.namespace.trim();
      } else if (formData.cloud_provider === 'azure') {
        submitData.azure_subscription_id = formData.azure_subscription_id.trim();
        submitData.aks_cluster_name = formData.aks_cluster_name.trim();
        submitData.azure_deployment_name = formData.azure_deployment_name.trim();
        submitData.azure_pod_name = formData.azure_pod_name.trim();
        submitData.azure_namespace = formData.azure_namespace.trim();
        submitData.resource_group = formData.resource_group.trim();
        submitData.workspace = formData.workspace.trim();
        submitData.workspace_resource_group = formData.workspace_resource_group.trim();
        submitData.ingress_name = formData.ingress_name.trim();
        submitData.ingress_public_ip = formData.ingress_public_ip.trim();
        submitData.ingress_namespace = formData.ingress_namespace.trim();
      } else if (formData.cloud_provider === 'aws') {
        submitData.aws_account_id = formData.aws_account_id.trim();
        submitData.eks_cluster_name = formData.eks_cluster_name.trim();
        submitData.cloudwatch_log_group_path = formData.cloudwatch_log_group_path.trim();
        submitData.aws_deployment_name = formData.aws_deployment_name.trim();
        submitData.aws_pod_name = formData.aws_pod_name.trim();
        submitData.aws_namespace = formData.aws_namespace.trim();
      }

      if (isEditMode) {
        await applicationService.updateApplication(id, submitData);
      } else {
        await applicationService.createApplication(submitData);
      }

      navigate('/applications');
    } catch (err) {
      let errorMsg = `Failed to ${isEditMode ? 'update' : 'create'} application. Please try again.`;
      
      if (err.response?.data?.detail) {
        // Handle if detail is string or object
        if (typeof err.response.data.detail === 'string') {
          errorMsg = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          errorMsg = err.response.data.detail.map(e => 
            typeof e === 'string' ? e : (e?.msg || JSON.stringify(e))
          ).join(', ');
        }
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const labelClass = 'block text-[11px] font-semibold uppercase tracking-[0.35em] text-gray-400 mb-2';
  const helperTextClass = 'mt-2 text-xs text-gray-500';
  const errorTextClass = 'mt-2 text-sm text-rose-300';
  const baseInputClass = 'w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 backdrop-blur transition-all';
  const inputClass = (hasError = false) => `${baseInputClass} ${hasError ? 'border-rose-500/60 shadow-[0_0_18px_rgba(244,63,94,0.25)]' : ''}`;

  if (!isAdmin && !isTeamLead) {
    return (
      <div className="glass-panel h-[80vh] flex items-center justify-center p-10 text-center">
        <div className="max-w-xl space-y-4">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-rose-500/40 bg-rose-500/10 text-rose-200">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v4m0 4h.01M4.293 6.293a1 1 0 011.414 0L12 12.586l6.293-6.293a1 1 0 111.414 1.414L13.414 14l6.293 6.293a1 1 0 01-1.414 1.414L12 15.414l-6.293 6.293a1 1 0 01-1.414-1.414L10.586 14 4.293 7.707a1 1 0 010-1.414z" />
            </svg>
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-[0.4em] text-gray-500">Restricted</p>
            <h2 className="text-2xl font-semibold text-white">Access denied</h2>
          </div>
          <p className="text-gray-400">
            Only KaiOPS administrators can {isEditMode ? 'edit' : 'register'} applications.
          </p>
        </div>
      </div>
    );
  }

  if (loadingApp) {
    return (
      <div className="glass-panel h-[80vh] flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="mx-auto h-12 w-12 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin"></div>
          <div>
            <p className="text-[11px] uppercase tracking-[0.4em] text-gray-500">Loading</p>
            <p className="text-gray-300">Fetching application details...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full overflow-y-auto custom-scrollbar pr-2">
      <div className="mx-auto max-w-5xl space-y-6 px-6 py-6">
        {/* Header */}
        <div>
          <button
            onClick={() => navigate('/applications')}
            className="mb-4 inline-flex items-center gap-2 text-sm font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
            </svg>
            Back to Service Registry
          </button>
          <p className="text-[11px] uppercase tracking-[0.4em] text-cyan-400/60">
            {isEditMode ? 'Update Asset' : 'Register Asset'}
          </p>
          <h1 className="text-4xl font-black text-white tracking-tight mb-2">
            {isEditMode ? 'Edit Application' : 'Register New Application'}
          </h1>
          <p className="text-gray-400 text-sm">
            {isEditMode 
              ? 'Update metadata for your mission-critical service' 
              : 'Add a new workload to KaiOPS mission control. Fill in all required fields marked with *'}
          </p>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl border border-rose-500/40 bg-rose-500/10 p-4 text-rose-100"
          >
            <div>{typeof error === 'string' ? error : 'An error occurred'}</div>
          </motion.div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Cloud Provider Selection */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel rounded-3xl border border-white/10 p-6"
          >
            <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <span className="text-2xl">☁️</span> Cloud Infrastructure
            </h2>

            <div>
              <label className={labelClass}>Cloud Provider <span className="text-rose-400">*</span></label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {CLOUD_PROVIDERS.map(provider => (
                  <motion.button
                    key={provider.value}
                    type="button"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setFormData(prev => ({ ...prev, cloud_provider: provider.value }))}
                    className={`p-4 rounded-2xl border-2 transition-all text-left ${
                      formData.cloud_provider === provider.value
                        ? 'border-cyan-500/60 bg-cyan-500/20 shadow-[0_0_20px_rgba(6,182,212,0.3)]'
                        : 'border-white/10 bg-black/30 hover:border-white/20'
                    }`}
                  >
                    <div className="text-3xl mb-2">{provider.icon}</div>
                    <div className="font-semibold text-white">{provider.label}</div>
                    {formData.cloud_provider === provider.value && (
                      <div className="text-xs text-cyan-300 mt-2">✓ Selected</div>
                    )}
                  </motion.button>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Common Fields */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-panel rounded-3xl border border-white/10 p-6 space-y-6"
          >
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-2xl">📋</span> Application Details
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Application Name */}
              <div>
                <label htmlFor="application_name" className={labelClass}>
                  Application Name <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  id="application_name"
                  name="application_name"
                  value={formData.application_name}
                  onChange={handleChange}
                  placeholder="payment_gateway"
                  className={inputClass(!!validationErrors.application_name)}
                />
                {validationErrors.application_name && (
                  <p className={errorTextClass}>{validationErrors.application_name}</p>
                )}
              </div>

              {/* Application Owner */}
              <div>
                <label htmlFor="application_owner" className={labelClass}>
                  Application Owner <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  id="application_owner"
                  name="application_owner"
                  value={formData.application_owner}
                  onChange={handleChange}
                  placeholder="Laxman"
                  className={inputClass(!!validationErrors.application_owner)}
                />
                {validationErrors.application_owner && (
                  <p className={errorTextClass}>{validationErrors.application_owner}</p>
                )}
              </div>

              {/* Status */}
              <div>
                <label htmlFor="status" className={labelClass}>
                  Status <span className="text-rose-400">*</span>
                </label>
                <select
                  id="status"
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className={inputClass()}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="pending">Pending</option>
                  <option value="suspended">Suspended</option>
                </select>
              </div>

              {/* Criticality */}
              <div>
                <label className={labelClass}>
                  Application Criticality <span className="text-rose-400">*</span>
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {CRITICALITY_LEVELS.map(level => (
                    <motion.button
                      key={level.value}
                      type="button"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setFormData(prev => ({ ...prev, application_criticality: level.value }))}
                      className={`p-2 rounded-lg border transition-all text-sm font-semibold uppercase tracking-wider ${
                        formData.application_criticality === level.value
                          ? level.color
                          : 'border-white/10 bg-black/30 text-gray-400 hover:border-white/20'
                      }`}
                    >
                      {level.label}
                    </motion.button>
                  ))}
                </div>
                {validationErrors.application_criticality && (
                  <p className={errorTextClass}>{validationErrors.application_criticality}</p>
                )}
              </div>
            </div>

            {/* GitHub Repository */}
            <div>
              <label htmlFor="github_repo" className={labelClass}>
                GitHub Repository <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                id="github_repo"
                name="github_repo"
                value={formData.github_repo}
                onChange={handleChange}
                placeholder="Owner/repo_name"
                className={inputClass(!!validationErrors.github_repo)}
              />
              {validationErrors.github_repo && (
                <p className={errorTextClass}>{validationErrors.github_repo}</p>
              )}
              <p className={helperTextClass}>Format: owner/repo_name</p>
            </div>

            {/* ArgoCD Application Name */}
            <div>
              <label htmlFor="argocd_app_name" className={labelClass}>
                ArgoCD Application Name <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                id="argocd_app_name"
                name="argocd_app_name"
                value={formData.argocd_app_name}
                onChange={handleChange}
                placeholder="gcptodoapp"
                className={inputClass(!!validationErrors.argocd_app_name)}
              />
              {validationErrors.argocd_app_name && (
                <p className={errorTextClass}>{validationErrors.argocd_app_name}</p>
              )}
            </div>

            {/* Grafana Dashboard */}
            <div>
              <label htmlFor="grafana_dashboard" className={labelClass}>
                Grafana Dashboard <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                id="grafana_dashboard"
                name="grafana_dashboard"
                value={formData.grafana_dashboard}
                onChange={handleChange}
                placeholder="gcp-todo-app"
                className={inputClass(!!validationErrors.grafana_dashboard)}
              />
              {validationErrors.grafana_dashboard && (
                <p className={errorTextClass}>{validationErrors.grafana_dashboard}</p>
              )}
            </div>

            {/* Grafana Alert Name */}
            <div>
              <label htmlFor="grafana_alert_name" className={labelClass}>
                Grafana Alert Name <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                id="grafana_alert_name"
                name="grafana_alert_name"
                value={formData.grafana_alert_name}
                onChange={handleChange}
                placeholder="gcp_todo_app_alert1"
                className={inputClass(!!validationErrors.grafana_alert_name)}
              />
              {validationErrors.grafana_alert_name && (
                <p className={errorTextClass}>{validationErrors.grafana_alert_name}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className={labelClass}>
                Description (Optional)
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows="4"
                placeholder="Provide a brief description of the application..."
                className={`${inputClass()} min-h-[120px]`}
              />
            </div>
          </motion.div>

          {/* Cloud-Specific Fields */}
          <AnimatePresence mode="wait">
            {formData.cloud_provider === 'gcp' && (
              <motion.div
                key="gcp"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: 0.1 }}
                className="glass-panel rounded-3xl border border-cyan-500/30 bg-gradient-to-br from-cyan-500/10 to-transparent p-6 space-y-6"
              >
                <h2 className="text-lg font-bold text-cyan-300 flex items-center gap-2">
                  <span className="text-2xl">☁️</span> Google Cloud Platform Configuration
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="gcp_project_id" className={labelClass}>
                      GCP Project ID <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="gcp_project_id"
                      name="gcp_project_id"
                      value={formData.gcp_project_id}
                      onChange={handleChange}
                      placeholder="carbon-relic-479214-c1"
                      className={inputClass(!!validationErrors.gcp_project_id)}
                    />
                    {validationErrors.gcp_project_id && (
                      <p className={errorTextClass}>{validationErrors.gcp_project_id}</p>
                    )}
                    <p className={helperTextClass}>Your GCP project ID (6-30 chars, lowercase)</p>
                  </div>

                  <div>
                    <label htmlFor="gcp_log_resource" className={labelClass}>
                      GCP Log Resource <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="gcp_log_resource"
                      name="gcp_log_resource"
                      value={formData.gcp_log_resource}
                      onChange={handleChange}
                      placeholder="gcp-k8s_container"
                      className={inputClass(!!validationErrors.gcp_log_resource)}
                    />
                    {validationErrors.gcp_log_resource && (
                      <p className={errorTextClass}>{validationErrors.gcp_log_resource}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="gke_cluster_name" className={labelClass}>
                      GKE Cluster Name <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="gke_cluster_name"
                      name="gke_cluster_name"
                      value={formData.gke_cluster_name}
                      onChange={handleChange}
                      placeholder="gcp-kai-ops"
                      className={inputClass(!!validationErrors.gke_cluster_name)}
                    />
                    {validationErrors.gke_cluster_name && (
                      <p className={errorTextClass}>{validationErrors.gke_cluster_name}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="deployment_name" className={labelClass}>
                      Deployment Name <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="deployment_name"
                      name="deployment_name"
                      value={formData.deployment_name}
                      onChange={handleChange}
                      placeholder="todo-frontend-app-deploy"
                      className={inputClass(!!validationErrors.deployment_name)}
                    />
                    {validationErrors.deployment_name && (
                      <p className={errorTextClass}>{validationErrors.deployment_name}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="pod_name" className={labelClass}>
                      Pod Name <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="pod_name"
                      name="pod_name"
                      value={formData.pod_name}
                      onChange={handleChange}
                      placeholder="auto-populated"
                      disabled
                      className={`${inputClass(!!validationErrors.pod_name)} opacity-75 cursor-not-allowed`}
                    />
                    <p className={helperTextClass}>Auto-populated from deployment name</p>
                  </div>

                  <div>
                    <label htmlFor="namespace" className={labelClass}>
                      Application Namespace <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="namespace"
                      name="namespace"
                      value={formData.namespace}
                      onChange={handleChange}
                      placeholder="gcp-todo-ns"
                      className={inputClass(!!validationErrors.namespace)}
                    />
                    {validationErrors.namespace && (
                      <p className={errorTextClass}>{validationErrors.namespace}</p>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {formData.cloud_provider === 'azure' && (
              <motion.div
                key="azure"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: 0.1 }}
                className="glass-panel rounded-3xl border border-blue-500/30 bg-gradient-to-br from-blue-500/10 to-transparent p-6 space-y-6"
              >
                <h2 className="text-lg font-bold text-blue-300 flex items-center gap-2">
                  <span className="text-2xl">⬛</span> Microsoft Azure Configuration
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="azure_subscription_id" className={labelClass}>
                      Azure Subscription ID <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="azure_subscription_id"
                      name="azure_subscription_id"
                      value={formData.azure_subscription_id}
                      onChange={handleChange}
                      placeholder="5a309391-54e8-4597-98ca-1c35c2c9dc09"
                      className={inputClass(!!validationErrors.azure_subscription_id)}
                    />
                    {validationErrors.azure_subscription_id && (
                      <p className={errorTextClass}>{validationErrors.azure_subscription_id}</p>
                    )}
                    <p className={helperTextClass}>Your Azure Subscription ID (UUID format)</p>
                  </div>

                  <div>
                    <label htmlFor="aks_cluster_name" className={labelClass}>
                      AKS Cluster Name <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="aks_cluster_name"
                      name="aks_cluster_name"
                      value={formData.aks_cluster_name}
                      onChange={handleChange}
                      placeholder="azure-kai-ops"
                      className={inputClass(!!validationErrors.aks_cluster_name)}
                    />
                    {validationErrors.aks_cluster_name && (
                      <p className={errorTextClass}>{validationErrors.aks_cluster_name}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="azure_deployment_name" className={labelClass}>
                      Deployment Name <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="azure_deployment_name"
                      name="azure_deployment_name"
                      value={formData.azure_deployment_name}
                      onChange={handleChange}
                      placeholder="todo-frontend-app-deploy"
                      className={inputClass(!!validationErrors.azure_deployment_name)}
                    />
                    {validationErrors.azure_deployment_name && (
                      <p className={errorTextClass}>{validationErrors.azure_deployment_name}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="azure_pod_name" className={labelClass}>
                      Pod Name <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="azure_pod_name"
                      name="azure_pod_name"
                      value={formData.azure_pod_name}
                      onChange={handleChange}
                      placeholder="auto-populated"
                      disabled
                      className={`${inputClass(!!validationErrors.azure_pod_name)} opacity-75 cursor-not-allowed`}
                    />
                    <p className={helperTextClass}>Auto-populated from deployment name</p>
                  </div>

                  <div>
                    <label htmlFor="azure_namespace" className={labelClass}>
                      Application Namespace <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="azure_namespace"
                      name="azure_namespace"
                      value={formData.azure_namespace}
                      onChange={handleChange}
                      placeholder="azure-todo-ns"
                      className={inputClass(!!validationErrors.azure_namespace)}
                    />
                    {validationErrors.azure_namespace && (
                      <p className={errorTextClass}>{validationErrors.azure_namespace}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="resource_group" className={labelClass}>
                      Resource Group <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="resource_group"
                      name="resource_group"
                      value={formData.resource_group}
                      onChange={handleChange}
                      placeholder="KaiOps-RG"
                      className={inputClass(!!validationErrors.resource_group)}
                    />
                    {validationErrors.resource_group && (
                      <p className={errorTextClass}>{validationErrors.resource_group}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="workspace" className={labelClass}>
                      Workspace <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="workspace"
                      name="workspace"
                      value={formData.workspace}
                      onChange={handleChange}
                      placeholder="defaultworkspace-eus"
                      className={inputClass(!!validationErrors.workspace)}
                    />
                    {validationErrors.workspace && (
                      <p className={errorTextClass}>{validationErrors.workspace}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="workspace_resource_group" className={labelClass}>
                      Workspace Resource Group <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="workspace_resource_group"
                      name="workspace_resource_group"
                      value={formData.workspace_resource_group}
                      onChange={handleChange}
                      placeholder="defaultresourcegroup-eus"
                      className={inputClass(!!validationErrors.workspace_resource_group)}
                    />
                    {validationErrors.workspace_resource_group && (
                      <p className={errorTextClass}>{validationErrors.workspace_resource_group}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="ingress_name" className={labelClass}>
                      Ingress Name <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="ingress_name"
                      name="ingress_name"
                      value={formData.ingress_name}
                      onChange={handleChange}
                      placeholder="aks-ingress"
                      className={inputClass(!!validationErrors.ingress_name)}
                    />
                    {validationErrors.ingress_name && (
                      <p className={errorTextClass}>{validationErrors.ingress_name}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="ingress_public_ip" className={labelClass}>
                      Ingress Public IP <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="ingress_public_ip"
                      name="ingress_public_ip"
                      value={formData.ingress_public_ip}
                      onChange={handleChange}
                      placeholder="48.194.52.217"
                      className={inputClass(!!validationErrors.ingress_public_ip)}
                    />
                    {validationErrors.ingress_public_ip && (
                      <p className={errorTextClass}>{validationErrors.ingress_public_ip}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="ingress_namespace" className={labelClass}>
                      Ingress Namespace <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="ingress_namespace"
                      name="ingress_namespace"
                      value={formData.ingress_namespace}
                      onChange={handleChange}
                      placeholder="app-routing-system"
                      className={inputClass(!!validationErrors.ingress_namespace)}
                    />
                    {validationErrors.ingress_namespace && (
                      <p className={errorTextClass}>{validationErrors.ingress_namespace}</p>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {formData.cloud_provider === 'aws' && (
              <motion.div
                key="aws"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: 0.1 }}
                className="glass-panel rounded-3xl border border-orange-500/30 bg-gradient-to-br from-orange-500/10 to-transparent p-6 space-y-6"
              >
                <h2 className="text-lg font-bold text-orange-300 flex items-center gap-2">
                  <span className="text-2xl">🟠</span> Amazon Web Services Configuration
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="aws_account_id" className={labelClass}>
                      AWS Account ID <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="aws_account_id"
                      name="aws_account_id"
                      value={formData.aws_account_id}
                      onChange={handleChange}
                      placeholder="397174242206"
                      className={inputClass(!!validationErrors.aws_account_id)}
                    />
                    {validationErrors.aws_account_id && (
                      <p className={errorTextClass}>{validationErrors.aws_account_id}</p>
                    )}
                    <p className={helperTextClass}>Your AWS Account ID (12 digits)</p>
                  </div>

                  <div>
                    <label htmlFor="eks_cluster_name" className={labelClass}>
                      EKS Cluster Name <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="eks_cluster_name"
                      name="eks_cluster_name"
                      value={formData.eks_cluster_name}
                      onChange={handleChange}
                      placeholder="aws-kai-ops"
                      className={inputClass(!!validationErrors.eks_cluster_name)}
                    />
                    {validationErrors.eks_cluster_name && (
                      <p className={errorTextClass}>{validationErrors.eks_cluster_name}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="cloudwatch_log_group_path" className={labelClass}>
                      CloudWatch Log Group Path <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="cloudwatch_log_group_path"
                      name="cloudwatch_log_group_path"
                      value={formData.cloudwatch_log_group_path}
                      onChange={handleChange}
                      placeholder="/aws/containerinsights/log-agent-eks/application"
                      className={inputClass(!!validationErrors.cloudwatch_log_group_path)}
                    />
                    {validationErrors.cloudwatch_log_group_path && (
                      <p className={errorTextClass}>{validationErrors.cloudwatch_log_group_path}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="aws_deployment_name" className={labelClass}>
                      Deployment Name <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="aws_deployment_name"
                      name="aws_deployment_name"
                      value={formData.aws_deployment_name}
                      onChange={handleChange}
                      placeholder="todo-frontend-app-deploy"
                      className={inputClass(!!validationErrors.aws_deployment_name)}
                    />
                    {validationErrors.aws_deployment_name && (
                      <p className={errorTextClass}>{validationErrors.aws_deployment_name}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="aws_pod_name" className={labelClass}>
                      Pod Name <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="aws_pod_name"
                      name="aws_pod_name"
                      value={formData.aws_pod_name}
                      onChange={handleChange}
                      placeholder="auto-populated"
                      disabled
                      className={`${inputClass(!!validationErrors.aws_pod_name)} opacity-75 cursor-not-allowed`}
                    />
                    <p className={helperTextClass}>Auto-populated from deployment name</p>
                  </div>

                  <div>
                    <label htmlFor="aws_namespace" className={labelClass}>
                      Application Namespace <span className="text-rose-400">*</span>
                    </label>
                    <input
                      type="text"
                      id="aws_namespace"
                      name="aws_namespace"
                      value={formData.aws_namespace}
                      onChange={handleChange}
                      placeholder="aws-todo-ns"
                      className={inputClass(!!validationErrors.aws_namespace)}
                    />
                    {validationErrors.aws_namespace && (
                      <p className={errorTextClass}>{validationErrors.aws_namespace}</p>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Custom Metadata Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-panel rounded-3xl border border-purple-500/30 bg-gradient-to-br from-purple-500/10 to-transparent p-6"
          >
            <h2 className="text-lg font-bold text-purple-300 flex items-center gap-2 mb-6">
              <span className="text-2xl">🔧</span> Custom Metadata
            </h2>

            {/* Existing Metadata */}
            {formData.custom_metadata.length > 0 && (
              <div className="mb-6 space-y-3">
                <p className="text-sm font-semibold text-gray-400 mb-3">Added Metadata:</p>
                {formData.custom_metadata.map((meta, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="flex items-center justify-between p-3 rounded-lg border border-white/10 bg-black/30"
                  >
                    <div>
                      <p className="font-mono text-sm text-cyan-400">{meta.key}</p>
                      <p className="font-mono text-sm text-gray-400">{meta.value}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveMetadata(idx)}
                      className="p-2 rounded-lg hover:bg-rose-500/20 text-rose-400 transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </motion.div>
                ))}
              </div>
            )}

            {/* Add New Metadata */}
            <div className="space-y-3 p-4 rounded-lg border border-dashed border-white/20 bg-black/20">
              <p className="text-sm font-semibold text-gray-400">Add Custom Field:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Key"
                  value={newMetadata.key}
                  onChange={(e) => setNewMetadata(prev => ({ ...prev, key: e.target.value }))}
                  className={baseInputClass}
                />
                <input
                  type="text"
                  placeholder="Value"
                  value={newMetadata.value}
                  onChange={(e) => setNewMetadata(prev => ({ ...prev, value: e.target.value }))}
                  className={baseInputClass}
                />
              </div>
              <button
                type="button"
                onClick={handleAddMetadata}
                disabled={!newMetadata.key.trim() || !newMetadata.value.trim()}
                className="w-full py-2 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/30 font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                + Add Custom Field
              </button>
            </div>
          </motion.div>

          {/* Submit Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex flex-col gap-3 border-t border-white/10 pt-6 sm:flex-row"
          >
            <button
              type="submit"
              disabled={loading}
              className="flex-1 rounded-2xl bg-gradient-to-r from-cyan-500 to-blue-500 px-6 py-3 text-sm font-bold uppercase tracking-wider text-white shadow-lg shadow-cyan-500/30 transition-all hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                  {isEditMode ? 'Updating...' : 'Registering...'}
                </span>
              ) : (
                isEditMode ? '✓ Update Application' : '+ Register Application'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate('/applications')}
              disabled={loading}
              className="flex-1 rounded-2xl border border-white/10 bg-white/5 px-6 py-3 text-sm font-bold uppercase tracking-wider text-gray-200 transition-colors hover:border-white/20 hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
            >
              Cancel
            </button>
          </motion.div>
        </form>
      </div>
    </div>
  );
};

export default ApplicationForm;
