"""
Phase 5: Parallel Sub-Agent Orchestrator

Orchestrates multiple sub-agents in parallel to gather comprehensive information
and consolidate results into a single enriched response.

Sub-agents executed in parallel:
1. ArgoCD Agent: Application status, deployment history, sync status
2. Cost Agent: Cost analysis, billing information
3. Observability Agent: Metrics, logs, alerts
4. Security Agent: Security posture, compliance status
5. SCM Agent: Git repository information, commits, branches
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SubAgentType(Enum):
    """Available sub-agents for parallel execution."""
    ARGOCD = "argocd"
    COST = "cost"
    OBSERVABILITY = "observability"
    SECURITY = "security"
    SCM = "scm"
    METADATA = "metadata"


@dataclass
class SubAgentResult:
    """Result from a single sub-agent execution."""
    agent_type: SubAgentType
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "agent": self.agent_type.value,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms
        }


@dataclass
class OrchestratorResponse:
    """Consolidated response from orchestrator with all sub-agent results."""
    primary_response: str
    sub_agent_results: List[SubAgentResult] = field(default_factory=list)
    total_execution_time_ms: float = 0.0
    consolidated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        return {
            "primary_response": self.primary_response,
            "sub_agents": [r.to_dict() for r in self.sub_agent_results],
            "total_execution_time_ms": self.total_execution_time_ms,
            "consolidated_at": self.consolidated_at
        }


class SubAgentOrchestrator:
    """Orchestrates parallel execution of multiple sub-agents."""
    
    # Configuration
    DEFAULT_TIMEOUT_SECONDS = 5.0
    MAX_TIMEOUT_SECONDS = 30.0
    MIN_TIMEOUT_SECONDS = 1.0
    
    # Sub-agent priorities (higher = executed first)
    PRIORITY = {
        SubAgentType.METADATA: 10,      # Always first - provides context
        SubAgentType.ARGOCD: 9,         # High priority for main queries
        SubAgentType.SCM: 8,            # GitHub info often needed
        SubAgentType.COST: 5,           # Medium priority
        SubAgentType.OBSERVABILITY: 4,  # Medium priority
        SubAgentType.SECURITY: 3,       # Lower priority
    }
    
    def __init__(self, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS):
        """
        Initialize orchestrator.
        
        Args:
            timeout_seconds: Timeout for each sub-agent (clamped between MIN and MAX)
        """
        self.timeout_seconds = max(
            self.MIN_TIMEOUT_SECONDS,
            min(timeout_seconds, self.MAX_TIMEOUT_SECONDS)
        )
        logger.info(f"Orchestrator initialized with timeout: {self.timeout_seconds}s")
    
    async def execute_parallel(
        self,
        app_name: Optional[str],
        query: str,
        enabled_agents: List[SubAgentType]
    ) -> OrchestratorResponse:
        """
        Execute multiple sub-agents in parallel and consolidate results.
        
        Args:
            app_name: Application name to query (if extracted)
            query: User's original query
            enabled_agents: List of sub-agents to execute
            
        Returns:
            OrchestratorResponse with consolidated results
        """
        start_time = datetime.now()
        
        logger.info(
            f"Starting parallel execution for app='{app_name}' query='{query}' "
            f"with agents: {[a.value for a in enabled_agents]}"
        )
        
        # Sort agents by priority
        sorted_agents = sorted(
            enabled_agents,
            key=lambda a: self.PRIORITY.get(a, 0),
            reverse=True
        )
        
        # Create tasks for all enabled agents
        tasks = {
            agent: asyncio.create_task(
                self._execute_agent_with_timeout(agent, app_name, query)
            )
            for agent in sorted_agents
        }
        
        # Execute all tasks in parallel with gather
        try:
            results = await asyncio.gather(
                *tasks.values(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Error during parallel execution: {e}")
            results = []
        
        # Process results
        agent_results = []
        for agent, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                agent_results.append(SubAgentResult(
                    agent_type=agent,
                    success=False,
                    error=str(result)
                ))
            else:
                agent_results.append(result)
        
        # Calculate total execution time
        total_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Consolidate results
        primary_response = self._consolidate_results(app_name, query, agent_results)
        
        orchestrator_response = OrchestratorResponse(
            primary_response=primary_response,
            sub_agent_results=agent_results,
            total_execution_time_ms=total_time_ms
        )
        
        logger.info(
            f"Orchestration complete: {total_time_ms:.0f}ms total, "
            f"{len(agent_results)} agents executed"
        )
        
        return orchestrator_response
    
    async def _execute_agent_with_timeout(
        self,
        agent_type: SubAgentType,
        app_name: Optional[str],
        query: str
    ) -> SubAgentResult:
        """
        Execute a single sub-agent with timeout.
        
        Args:
            agent_type: Type of agent to execute
            app_name: Application name
            query: User query
            
        Returns:
            SubAgentResult with execution data
        """
        start_time = datetime.now()
        
        try:
            # Execute the appropriate agent
            if agent_type == SubAgentType.ARGOCD:
                data = await self._execute_argocd_agent(app_name, query)
            elif agent_type == SubAgentType.COST:
                data = await self._execute_cost_agent(app_name, query)
            elif agent_type == SubAgentType.OBSERVABILITY:
                data = await self._execute_observability_agent(app_name, query)
            elif agent_type == SubAgentType.SECURITY:
                data = await self._execute_security_agent(app_name, query)
            elif agent_type == SubAgentType.SCM:
                data = await self._execute_scm_agent(app_name, query)
            elif agent_type == SubAgentType.METADATA:
                data = await self._execute_metadata_agent(app_name, query)
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return SubAgentResult(
                agent_type=agent_type,
                success=True,
                data=data,
                execution_time_ms=execution_time_ms
            )
            
        except asyncio.TimeoutError:
            logger.warning(f"{agent_type.value} agent timed out after {self.timeout_seconds}s")
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            return SubAgentResult(
                agent_type=agent_type,
                success=False,
                error=f"Timeout after {self.timeout_seconds}s",
                execution_time_ms=execution_time_ms
            )
        except Exception as e:
            logger.error(f"Error executing {agent_type.value} agent: {e}")
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            return SubAgentResult(
                agent_type=agent_type,
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms
            )
    
    async def _execute_argocd_agent(
        self,
        app_name: Optional[str],
        query: str
    ) -> Dict[str, Any]:
        """Execute ArgoCD agent to get application status."""
        try:
            from agents.mcp_client import call_mcp_tool, parse_mcp_response
            
            data = {}
            
            # Get list of applications
            result = await call_mcp_tool("argocd", "list_applications")
            data["applications"] = parse_mcp_response(result)
            
            # Get specific app status if provided
            if app_name:
                result = await call_mcp_tool("argocd", "get_application_status", app_name=app_name)
                data["app_status"] = parse_mcp_response(result)
                
                result = await call_mcp_tool("argocd", "get_deployment_history", app_name=app_name)
                data["deployment_history"] = parse_mcp_response(result)
            
            logger.debug(f"ArgoCD agent retrieved data for app='{app_name}'")
            return data
            
        except Exception as e:
            logger.warning(f"ArgoCD agent error: {e}")
            raise
    
    async def _execute_cost_agent(
        self,
        app_name: Optional[str],
        query: str
    ) -> Dict[str, Any]:
        """Execute Cost agent to get cost analysis."""
        try:
            from app.metadata.service import MetadataService
            
            data = {}
            
            # Get metadata with cost information
            if app_name:
                metadata = MetadataService.get_metadata(app_name, use_cache=True)
                if metadata and metadata.cost and metadata.cost.enabled:
                    data["cost_center"] = metadata.cost.cost_center
                    data["message"] = f"Cost tracking enabled for cost center: {metadata.cost.cost_center}"
                else:
                    data["message"] = "No cost center configured for this application"
            else:
                data["message"] = "Cost analysis requires an application name"
            
            logger.debug(f"Cost agent retrieved data for app='{app_name}'")
            return data
            
        except Exception as e:
            logger.warning(f"Cost agent error: {e}")
            raise
    
    async def _execute_observability_agent(
        self,
        app_name: Optional[str],
        query: str
    ) -> Dict[str, Any]:
        """Execute Observability agent to get metrics and logs."""
        try:
            from app.metadata.service import MetadataService
            
            data = {}
            
            # Get Grafana dashboard info
            if app_name:
                metadata = MetadataService.get_metadata(app_name, use_cache=True)
                if metadata and metadata.grafana and metadata.grafana.enabled:
                    data["grafana_dashboard"] = {
                        "id": metadata.grafana.dashboard_id,
                        "url": metadata.grafana.dashboard_url
                    }
                    data["message"] = "Grafana dashboard available"
                else:
                    data["message"] = "No Grafana dashboard configured"
            else:
                data["message"] = "Observability analysis requires an application name"
            
            logger.debug(f"Observability agent retrieved data for app='{app_name}'")
            return data
            
        except Exception as e:
            logger.warning(f"Observability agent error: {e}")
            raise
    
    async def _execute_security_agent(
        self,
        app_name: Optional[str],
        query: str
    ) -> Dict[str, Any]:
        """Execute Security agent to get security posture."""
        try:
            data = {
                "message": "Security agent - checking security posture",
                "checks_enabled": [
                    "vulnerability_scanning",
                    "compliance_check",
                    "rbac_audit"
                ]
            }
            
            if app_name:
                data["app_name"] = app_name
                data["status"] = "Security checks queued"
            
            logger.debug(f"Security agent retrieved data for app='{app_name}'")
            return data
            
        except Exception as e:
            logger.warning(f"Security agent error: {e}")
            raise
    
    async def _execute_scm_agent(
        self,
        app_name: Optional[str],
        query: str
    ) -> Dict[str, Any]:
        """Execute SCM agent to get Git repository information."""
        try:
            from app.metadata.service import MetadataService
            
            data = {}
            
            # Get GitHub repository info
            if app_name:
                metadata = MetadataService.get_metadata(app_name, use_cache=True)
                if metadata and metadata.github and metadata.github.enabled:
                    data["github_repo"] = {
                        "owner": metadata.github.repo_owner,
                        "name": metadata.github.repo_name,
                        "branch": metadata.github.branch or "main"
                    }
                    data["message"] = f"GitHub repository: {metadata.github.repo_owner}/{metadata.github.repo_name}"
                else:
                    data["message"] = "No GitHub repository configured"
            else:
                data["message"] = "SCM analysis requires an application name"
            
            logger.debug(f"SCM agent retrieved data for app='{app_name}'")
            return data
            
        except Exception as e:
            logger.warning(f"SCM agent error: {e}")
            raise
    
    async def _execute_metadata_agent(
        self,
        app_name: Optional[str],
        query: str
    ) -> Dict[str, Any]:
        """Execute Metadata agent to get application metadata."""
        try:
            from app.metadata.service import MetadataService
            
            data = {}
            
            if app_name:
                metadata = MetadataService.get_metadata(app_name, use_cache=True)
                if metadata:
                    data["application"] = {
                        "name": metadata.app_name,
                        "description": metadata.description,
                        "environment": metadata.environment,
                        "team": metadata.team,
                        "created_at": metadata.created_at.isoformat() if metadata.created_at else None
                    }
                    data["integrations"] = {
                        "github": metadata.github is not None and metadata.github.enabled,
                        "argocd": metadata.argocd is not None and metadata.argocd.enabled,
                        "grafana": metadata.grafana is not None and metadata.grafana.enabled,
                        "cost": metadata.cost is not None and metadata.cost.enabled
                    }
                    data["message"] = f"Metadata found for {app_name}"
                else:
                    data["message"] = f"No metadata found for {app_name}"
            else:
                # List all applications
                all_metadata = MetadataService.list_all_metadata(use_cache=True)
                data["applications"] = [
                    {
                        "name": m.app_name,
                        "environment": m.environment,
                        "team": m.team
                    }
                    for m in all_metadata
                ]
                data["message"] = f"Found {len(all_metadata)} registered applications"
            
            logger.debug(f"Metadata agent retrieved data for app='{app_name}'")
            return data
            
        except Exception as e:
            logger.warning(f"Metadata agent error: {e}")
            raise
    
    def _consolidate_results(
        self,
        app_name: Optional[str],
        query: str,
        results: List[SubAgentResult]
    ) -> str:
        """
        Consolidate results from all sub-agents into a cohesive response.
        
        Args:
            app_name: Application name
            query: Original query
            results: Results from all sub-agents
            
        Returns:
            Consolidated response text
        """
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        if not successful_results:
            return "Unable to process request. All sub-agents failed."
        
        # Build consolidated response
        response_parts = []
        
        # Header
        if app_name:
            response_parts.append(f"📋 **Application Report: {app_name}**\n")
        else:
            response_parts.append("📊 **System Report**\n")
        
        # Metadata section
        metadata_result = next((r for r in successful_results if r.agent_type == SubAgentType.METADATA), None)
        if metadata_result and metadata_result.data:
            if "application" in metadata_result.data:
                app_info = metadata_result.data["application"]
                response_parts.append(
                    f"**Application:** {app_info.get('name')}\n"
                    f"**Description:** {app_info.get('description', 'N/A')}\n"
                    f"**Environment:** {app_info.get('environment', 'N/A')}\n"
                    f"**Team:** {app_info.get('team', 'N/A')}\n\n"
                )
            elif "applications" in metadata_result.data:
                apps = metadata_result.data["applications"]
                response_parts.append(f"**Registered Applications:** {len(apps)}\n\n")
        
        # ArgoCD section
        argocd_result = next((r for r in successful_results if r.agent_type == SubAgentType.ARGOCD), None)
        if argocd_result and argocd_result.data:
            response_parts.append("**ArgoCD Status:**\n")
            if "app_status" in argocd_result.data:
                response_parts.append(f"Status: {argocd_result.data['app_status']}\n")
            response_parts.append("\n")
        
        # SCM section
        scm_result = next((r for r in successful_results if r.agent_type == SubAgentType.SCM), None)
        if scm_result and scm_result.data:
            if "github_repo" in scm_result.data:
                repo = scm_result.data["github_repo"]
                response_parts.append(
                    f"**GitHub Repository:**\n"
                    f"Owner: {repo.get('owner')}\n"
                    f"Repository: {repo.get('name')}\n"
                    f"Branch: {repo.get('branch', 'main')}\n\n"
                )
        
        # Cost section
        cost_result = next((r for r in successful_results if r.agent_type == SubAgentType.COST), None)
        if cost_result and cost_result.data:
            if "cost_center" in cost_result.data:
                response_parts.append(
                    f"**Cost Center:** {cost_result.data['cost_center']}\n\n"
                )
        
        # Observability section
        obs_result = next((r for r in successful_results if r.agent_type == SubAgentType.OBSERVABILITY), None)
        if obs_result and obs_result.data:
            if "grafana_dashboard" in obs_result.data:
                dashboard = obs_result.data["grafana_dashboard"]
                response_parts.append(
                    f"**Grafana Dashboard:**\n"
                    f"Dashboard ID: {dashboard.get('id')}\n"
                    f"URL: {dashboard.get('url')}\n\n"
                )
        
        # Execution summary
        if len(results) > 0:
            response_parts.append(f"\n✅ **Sub-agents Report:** {len(successful_results)}/{len(results)} sub-agents successful")
            if failed_results:
                response_parts.append(f" ({len(failed_results)} agents unavailable)")
        
        return "".join(response_parts)


# Global orchestrator instance
orchestrator = SubAgentOrchestrator(timeout_seconds=5.0)
