"""
Root SRE Agent - Orchestration Layer

Main orchestrator that coordinates all domain experts.
Loads all subagent tools, combines prompts, and provides intelligent routing.
"""

import os
import sys
from google.adk.agents import Agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import all tools from subagents
from agents.metadata_agent.tools import (
    search_application_by_name,
    list_all_applications,
    query_mongodb
)

from agents.argocd_agent.tools import (
    get_application_status,
    get_deployment_history,
    sync_application,
    search_applications as search_argocd_applications,
    list_repositories,
    list_projects
)

from agents.github_agent.tools import (
    search_repositories,
    get_repository_info,
    search_code,
    list_issues,
    get_user_repositories,
    get_latest_commit
)

from agents.grafana_agent.tools import (
    search_dashboards,
    get_dashboard_summary,
    list_alert_rules
)

from agents.azure_rca_agent.tools import (
    check_application_logs as azure_check_application_logs,
    check_ingress_logs as azure_check_ingress_logs,
    analyze_pod_logs as azure_analyze_pod_logs
)

from agents.aws_rca_agent.tools import (
    check_application_logs as aws_check_application_logs,
    check_ingress_logs as aws_check_ingress_logs,
    analyze_pod_logs as aws_analyze_pod_logs
)

from agents.gcp_rca_agent.tools import (
    check_application_logs as gcp_check_application_logs,
    check_ingress_logs as gcp_check_ingress_logs,
    analyze_pod_logs as gcp_analyze_pod_logs
)

# Import all domain expertise prompts
from agents.sre_agent.prompt import root_instruction
from agents.metadata_agent.prompt import metadata_expertise
from agents.argocd_agent.prompt import argocd_expertise
from agents.github_agent.prompt import github_expertise
from agents.grafana_agent.prompt import grafana_expertise
from agents.azure_rca_agent.prompt import log_rca_expertise
from agents.aws_rca_agent.prompt import aws_rca_expertise
from agents.gcp_rca_agent.prompt import gcp_rca_expertise

# Get model configuration
gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
model_temperature = float(os.environ.get("MODEL_TEMPERATURE", "0.7"))

# Cloud-provider-aware router functions
def get_cloud_provider_from_app(app_name: str) -> str:
    """Determine cloud provider for an application from metadata.
    
    Queries PostgreSQL to get cloud_provider field using SQLAlchemy.
    Returns: "azure", "aws", "gcp", or "azure" (default)
    """
    try:
        from app.database.postgres_config import PostgresConfig
        from app.database.models import Application
        from sqlalchemy import func
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get database session
        session = PostgresConfig.get_session()
        try:
            # Query applications table for cloud_provider (case-insensitive)
            app = session.query(Application).filter(
                func.lower(Application.application_name) == func.lower(app_name)
            ).first()
            
            if app:
                cloud_provider = app.cloud_provider or ""
                logger.info(f"🔍 Cloud provider lookup: app='{app_name}' -> cloud_provider='{cloud_provider}'")
                
                if cloud_provider:
                    provider_lower = str(cloud_provider).lower()
                    if provider_lower in ["azure", "aws", "gcp"]:
                        logger.info(f"✅ Routing to {provider_lower.upper()} RCA agent")
                        return provider_lower
            
            logger.warning(f"⚠️ Cloud provider not found for {app_name}, defaulting to Azure")
        finally:
            session.close()
    except Exception as e:
        # Log the error but continue with default
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Error determining cloud provider for {app_name}: {str(e)}", exc_info=True)
    
    return "azure"  # Default to Azure

def check_application_logs(app_name: str, lines: int = 100, error_only: bool = False) -> dict:
    """
    Route to appropriate cloud provider's log checker based on application cloud provider.
    
    Supports:
    - Azure: Azure Log Analytics
    - AWS: CloudWatch Logs
    - GCP: Cloud Logging
    """
    import logging
    logger = logging.getLogger(__name__)
    
    cloud_provider = get_cloud_provider_from_app(app_name)
    logger.info(f"🔀 check_application_logs routing: app='{app_name}' -> cloud_provider='{cloud_provider}'")
    
    if cloud_provider == "aws":
        logger.info(f"📋 Calling AWS check_application_logs for {app_name}")
        return aws_check_application_logs(app_name, lines, error_only)
    elif cloud_provider == "gcp":
        logger.info(f"📋 Calling GCP check_application_logs for {app_name}")
        return gcp_check_application_logs(app_name, lines, error_only)
    else:  # Default to Azure
        logger.info(f"📋 Calling Azure check_application_logs for {app_name} (cloud_provider={cloud_provider})")
        return azure_check_application_logs(app_name, lines, error_only)

def check_ingress_logs(app_name: str, lines: int = 50, status_code_filter: str = "", min_response_time_ms: int = 0) -> dict:
    """
    Route to appropriate cloud provider's ingress log checker.
    
    Supports:
    - Azure: Application Gateway / Load Balancer logs
    - AWS: ALB/NLB logs
    - GCP: Cloud Load Balancing logs
    """
    import logging
    logger = logging.getLogger(__name__)
    
    cloud_provider = get_cloud_provider_from_app(app_name)
    logger.info(f"🔀 check_ingress_logs routing: app='{app_name}' -> cloud_provider='{cloud_provider}'")
    
    if cloud_provider == "aws":
        logger.info(f"📋 Calling AWS check_ingress_logs for {app_name}")
        return aws_check_ingress_logs(app_name, lines, status_code_filter, min_response_time_ms)
    elif cloud_provider == "gcp":
        logger.info(f"📋 Calling GCP check_ingress_logs for {app_name}")
        return gcp_check_ingress_logs(app_name, lines, status_code_filter, min_response_time_ms)
    else:  # Default to Azure
        logger.info(f"📋 Calling Azure check_ingress_logs for {app_name} (cloud_provider={cloud_provider})")
        return azure_check_ingress_logs(app_name, lines, status_code_filter, min_response_time_ms)

def analyze_pod_logs(app_name: str, include_events: bool = True, include_describe: bool = True) -> dict:
    """
    Route to appropriate cloud provider's pod analysis tool.
    
    Performs comprehensive RCA including:
    - Pod logs
    - Kubernetes events
    - Pod resource status and constraints
    
    Supports multi-deployment applications with health summaries.
    
    Supports:
    - Azure: AKS clusters
    - AWS: EKS clusters
    - GCP: GKE clusters
    """
    import logging
    logger = logging.getLogger(__name__)
    
    cloud_provider = get_cloud_provider_from_app(app_name)
    logger.info(f"🔀 analyze_pod_logs routing: app='{app_name}' -> cloud_provider='{cloud_provider}'")
    
    if cloud_provider == "aws":
        logger.info(f"📋 Calling AWS analyze_pod_logs for {app_name}")
        return aws_analyze_pod_logs(app_name, include_events, include_describe)
    elif cloud_provider == "gcp":
        logger.info(f"📋 Calling GCP analyze_pod_logs for {app_name}")
        return gcp_analyze_pod_logs(app_name, include_events, include_describe)
    else:  # Default to Azure
        logger.info(f"📋 Calling Azure analyze_pod_logs for {app_name} (cloud_provider={cloud_provider})")
        return azure_analyze_pod_logs(app_name, include_events, include_describe)

# Combine all prompts into comprehensive instruction
comprehensive_instruction = f"""{root_instruction}

<domain_expertise_metadata>
{metadata_expertise}
</domain_expertise_metadata>

<domain_expertise_argocd>
{argocd_expertise}
</domain_expertise_argocd>

<domain_expertise_github>
{github_expertise}
</domain_expertise_github>

<domain_expertise_grafana>
{grafana_expertise}
</domain_expertise_grafana>

<domain_expertise_log_rca>
{log_rca_expertise}

## Multi-Cloud RCA Support

This agent now supports Root Cause Analysis across multiple cloud providers:

### Azure RCA (Azure Log Analytics & AKS)
- Uses Azure Log Analytics for centralized logging
- Analyzes Azure Kubernetes Service (AKS) pods
- Queries Application Gateway and Azure Load Balancer logs

### AWS RCA (CloudWatch & EKS)
- Uses Amazon CloudWatch for log collection
- Analyzes Amazon Elastic Kubernetes Service (EKS) pods
- Queries AWS Application Load Balancer (ALB) and Network Load Balancer (NLB) logs

### GCP RCA (Cloud Logging & GKE)
- Uses Google Cloud Logging for centralized logging
- Analyzes Google Kubernetes Engine (GKE) pods
- Queries Google Cloud Load Balancing logs

### Automatic Cloud Provider Detection
When analyzing an application, the agent automatically:
1. Queries the metadata database for the application's cloud provider
2. Routes to the appropriate cloud-specific RCA tools
3. Uses cloud-native queries and interpreters
4. Returns cloud-specific analysis and recommendations

The `check_application_logs()`, `check_ingress_logs()`, and `analyze_pod_logs()` tools
automatically route to the correct cloud provider's implementation.
</domain_expertise_log_rca>

<domain_expertise_aws_rca>
{aws_rca_expertise}
</domain_expertise_aws_rca>

<domain_expertise_gcp_rca>
{gcp_rca_expertise}
</domain_expertise_gcp_rca>
"""

# Collect all tools
all_tools = [
    # Metadata tools (ALWAYS available - primary context source)
    search_application_by_name,
    list_all_applications,
    query_mongodb,
    
    # ArgoCD tools
    get_application_status,
    get_deployment_history,
    sync_application,
    search_argocd_applications,
    list_repositories,
    list_projects,
    
    # GitHub tools
    search_repositories,
    get_repository_info,
    search_code,
    list_issues,
    get_user_repositories,
    get_latest_commit,
    
    # Grafana tools
    search_dashboards,
    get_dashboard_summary,
    list_alert_rules,
    
    # Cloud-provider-aware Log RCA tools (route based on app's cloud provider)
    check_application_logs,
    check_ingress_logs,
    analyze_pod_logs
]

# Root agent definition
class SREAgent(Agent):
    """Root SRE Agent - Orchestrates all domain tools for operational intelligence."""
    pass


root_agent = SREAgent(
    name="sre_agent",
    description="KaiOPS Root SRE Agent - Orchestrates metadata management, deployment status, source code, and observability across all domains",
    instruction=comprehensive_instruction,
    model=gemini_model,
    generate_content_config={"temperature": model_temperature},
    tools=all_tools
)

__all__ = ["root_agent", "all_tools"]
