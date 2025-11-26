"""
Integration health check utilities.

Validates and monitors external service connectivity.
Non-breaking: optional validation step in application creation.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import aiohttp for async HTTP calls
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp not installed, integration health checks will be limited")


class IntegrationStatus(str, Enum):
    """Integration health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class IntegrationHealthCheck:
    """Result of integration health check."""
    
    def __init__(self, integration_type: str, name: str):
        self.integration_type = integration_type
        self.name = name
        self.status = IntegrationStatus.UNKNOWN
        self.last_check = None
        self.error_message = None
        self.response_time_ms = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "integration_type": self.integration_type,
            "name": self.name,
            "status": self.status.value,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "error_message": self.error_message,
            "response_time_ms": self.response_time_ms
        }


class IntegrationHealthChecker:
    """Check health of external integrations."""
    
    def __init__(self):
        self.checks_cache: Dict[str, IntegrationHealthCheck] = {}
    
    async def check_github(
        self, 
        token: str, 
        repo: str,
        timeout: int = 5
    ) -> IntegrationHealthCheck:
        """Check GitHub connectivity and token validity."""
        check = IntegrationHealthCheck("github", repo)
        
        if not AIOHTTP_AVAILABLE:
            check.status = IntegrationStatus.UNKNOWN
            check.error_message = "aiohttp not available"
            check.last_check = datetime.utcnow()
            return check
        
        start = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"token {token}"}
                async with session.get(
                    f"https://api.github.com/repos/{repo}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status == 200:
                        check.status = IntegrationStatus.HEALTHY
                    elif resp.status == 401:
                        check.status = IntegrationStatus.UNHEALTHY
                        check.error_message = "Invalid or expired GitHub token"
                    elif resp.status == 404:
                        check.status = IntegrationStatus.UNHEALTHY
                        check.error_message = f"Repository '{repo}' not found"
                    else:
                        check.status = IntegrationStatus.DEGRADED
                        check.error_message = f"Unexpected HTTP {resp.status}"
        
        except asyncio.TimeoutError:
            check.status = IntegrationStatus.UNHEALTHY
            check.error_message = f"Connection timeout after {timeout}s"
        except Exception as e:
            check.status = IntegrationStatus.UNHEALTHY
            check.error_message = str(e)
        
        finally:
            check.response_time_ms = (time.time() - start) * 1000
            check.last_check = datetime.utcnow()
        
        return check
    
    async def check_argocd(
        self, 
        url: str, 
        token: str,
        timeout: int = 5
    ) -> IntegrationHealthCheck:
        """Check ArgoCD connectivity and token validity."""
        check = IntegrationHealthCheck("argocd", url)
        
        if not AIOHTTP_AVAILABLE:
            check.status = IntegrationStatus.UNKNOWN
            check.error_message = "aiohttp not available"
            check.last_check = datetime.utcnow()
            return check
        
        start = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {token}"}
                async with session.get(
                    f"{url}/api/version",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    ssl=False  # For self-signed certificates
                ) as resp:
                    if resp.status == 200:
                        check.status = IntegrationStatus.HEALTHY
                    elif resp.status == 401:
                        check.status = IntegrationStatus.UNHEALTHY
                        check.error_message = "Invalid or expired ArgoCD token"
                    else:
                        check.status = IntegrationStatus.DEGRADED
                        check.error_message = f"Unexpected HTTP {resp.status}"
        
        except asyncio.TimeoutError:
            check.status = IntegrationStatus.UNHEALTHY
            check.error_message = f"Connection timeout after {timeout}s"
        except Exception as e:
            check.status = IntegrationStatus.UNHEALTHY
            check.error_message = str(e)
        
        finally:
            check.response_time_ms = (time.time() - start) * 1000
            check.last_check = datetime.utcnow()
        
        return check
    
    async def check_grafana(
        self, 
        url: str, 
        api_key: str,
        timeout: int = 5
    ) -> IntegrationHealthCheck:
        """Check Grafana connectivity and API key validity."""
        check = IntegrationHealthCheck("grafana", url)
        
        if not AIOHTTP_AVAILABLE:
            check.status = IntegrationStatus.UNKNOWN
            check.error_message = "aiohttp not available"
            check.last_check = datetime.utcnow()
            return check
        
        start = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {api_key}"}
                async with session.get(
                    f"{url}/api/datasources",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status == 200:
                        check.status = IntegrationStatus.HEALTHY
                    elif resp.status == 401:
                        check.status = IntegrationStatus.UNHEALTHY
                        check.error_message = "Invalid or expired Grafana API key"
                    else:
                        check.status = IntegrationStatus.DEGRADED
                        check.error_message = f"Unexpected HTTP {resp.status}"
        
        except asyncio.TimeoutError:
            check.status = IntegrationStatus.UNHEALTHY
            check.error_message = f"Connection timeout after {timeout}s"
        except Exception as e:
            check.status = IntegrationStatus.UNHEALTHY
            check.error_message = str(e)
        
        finally:
            check.response_time_ms = (time.time() - start) * 1000
            check.last_check = datetime.utcnow()
        
        return check
    
    async def check_all(
        self,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None,
        argocd_url: Optional[str] = None,
        argocd_token: Optional[str] = None,
        grafana_url: Optional[str] = None,
        grafana_api_key: Optional[str] = None
    ) -> Dict[str, IntegrationHealthCheck]:
        """Check health of all configured integrations."""
        checks = {}
        
        if github_token and github_repo:
            checks["github"] = await self.check_github(github_token, github_repo)
        
        if argocd_url and argocd_token:
            checks["argocd"] = await self.check_argocd(argocd_url, argocd_token)
        
        if grafana_url and grafana_api_key:
            checks["grafana"] = await self.check_grafana(grafana_url, grafana_api_key)
        
        return checks
    
    def get_cached_check(self, integration_type: str) -> Optional[IntegrationHealthCheck]:
        """Get cached health check if available."""
        return self.checks_cache.get(integration_type)
    
    def cache_check(self, check: IntegrationHealthCheck):
        """Cache health check result."""
        self.checks_cache[check.integration_type] = check


# Global health checker instance
_health_checker: Optional[IntegrationHealthChecker] = None


def get_health_checker() -> IntegrationHealthChecker:
    """Get global health checker instance."""
    global _health_checker
    
    if _health_checker is None:
        _health_checker = IntegrationHealthChecker()
    
    return _health_checker
