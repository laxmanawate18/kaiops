"""
Response Formatter Module

Provides utilities for formatting rich, attractive responses with analysis,
recommendations, and user-friendly presentation across all agents.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class ResponseFormatter:
    """Format agent responses with rich details, emojis, and analysis."""
    
    @staticmethod
    def format_argocd_application(app_data: Dict[str, Any]) -> str:
        """Format ArgoCD application data into an attractive, detailed response."""
        try:
            # Extract data
            name = app_data.get("metadata", {}).get("name", "Unknown")
            namespace = app_data.get("metadata", {}).get("namespace", "Unknown")
            
            spec = app_data.get("spec", {})
            source = spec.get("source", {})
            repo_url = source.get("repoURL", "N/A")
            path = source.get("path", "N/A")
            target_revision = source.get("targetRevision", "N/A")
            
            status = app_data.get("status", {})
            sync_status = status.get("sync", {}).get("status", "Unknown")
            health_status = status.get("health", {}).get("status", "Unknown")
            operation_state = status.get("operationState", {})
            operation_phase = operation_state.get("phase", "N/A")
            operation_message = operation_state.get("message", "")
            
            resources = status.get("resources", [])
            conditions = status.get("conditions", [])
            
            # Status emojis
            sync_emoji = "✅" if sync_status == "Synced" else "⚠️" if sync_status == "OutOfSync" else "⏳"
            health_emoji = "✅" if health_status == "Healthy" else "🔴" if health_status == "Degraded" else "⚠️"
            
            # Build response
            output = f"\n{'='*70}\n"
            output += f"🚀 ARGOCD APPLICATION STATUS: {name}\n"
            output += f"{'='*70}\n\n"
            
            # Status Section
            output += "📊 STATUS OVERVIEW\n"
            output += f"{'─'*70}\n"
            output += f"{sync_emoji} Sync Status       : {sync_status}\n"
            output += f"{health_emoji} Health Status     : {health_status}\n"
            output += f"⚙️  Operation Phase   : {operation_phase}\n"
            if operation_message:
                output += f"💬 Message          : {operation_message}\n"
            output += "\n"
            
            # Configuration Section
            output += "⚙️  DEPLOYMENT CONFIGURATION\n"
            output += f"{'─'*70}\n"
            output += f"📦 Application Name : {name}\n"
            output += f"🔗 Namespace        : {namespace}\n"
            output += f"📁 Repository       : {repo_url}\n"
            output += f"🌿 Path             : {path}\n"
            output += f"🏷️  Target Revision  : {target_revision}\n"
            output += "\n"
            
            # Resources Section
            if resources:
                output += "📋 RESOURCES\n"
                output += f"{'─'*70}\n"
                output += f"Total Resources: {len(resources)}\n"
                
                # Group resources by kind
                resource_groups = {}
                for res in resources:
                    kind = res.get("kind", "Unknown")
                    health = res.get("health", {}).get("status", "Unknown")
                    sync = res.get("status", "Unknown")
                    if kind not in resource_groups:
                        resource_groups[kind] = []
                    resource_groups[kind].append({"health": health, "status": sync, "name": res.get("name", "")})
                
                for kind, items in resource_groups.items():
                    healthy = sum(1 for i in items if i["health"] == "Healthy")
                    output += f"\n  {kind}: {healthy}/{len(items)} healthy\n"
                    for item in items[:3]:  # Show first 3 of each type
                        health_emoji = "✅" if item["health"] == "Healthy" else "⚠️"
                        output += f"    {health_emoji} {item['name']}\n"
                    if len(items) > 3:
                        output += f"    ... and {len(items) - 3} more\n"
                output += "\n"
            
            # Conditions/Issues Section
            if conditions:
                output += "⚠️  CONDITIONS & ISSUES\n"
                output += f"{'─'*70}\n"
                for condition in conditions:
                    cond_type = condition.get("type", "Unknown")
                    cond_status = condition.get("status", "Unknown")
                    message = condition.get("message", "")
                    output += f"• {cond_type} ({cond_status})\n"
                    if message:
                        output += f"  {message}\n"
                output += "\n"
            
            # Recommendations
            output += "💡 RECOMMENDATIONS\n"
            output += f"{'─'*70}\n"
            if sync_status != "Synced":
                output += "⚠️  Application is out of sync. Consider running a sync operation.\n"
            if health_status != "Healthy":
                output += "🔴 Application health is degraded. Check resources and logs.\n"
            if not conditions:
                output += "✅ No issues detected. System running smoothly.\n"
            output += f"\n{'='*70}\n"
            
            return output
            
        except Exception as e:
            return f"Error formatting ArgoCD response: {str(e)}"
    
    @staticmethod
    def format_github_commit(commit_data: Dict[str, Any], owner: str = "", repo: str = "") -> str:
        """Format GitHub commit data into an attractive response."""
        try:
            message = commit_data.get("message", "No message")
            author = commit_data.get("author", {})
            author_name = author.get("name", "Unknown")
            author_email = author.get("email", "Unknown")
            author_date = author.get("date", "Unknown")
            
            committer = commit_data.get("committer", {})
            committer_name = committer.get("name", "Unknown")
            
            sha = commit_data.get("sha", "")
            hash_short = sha[:7] if sha else "Unknown"
            
            url = commit_data.get("url", "")
            
            output = f"\n{'='*70}\n"
            if owner and repo:
                output += f"📝 LATEST COMMIT: {owner}/{repo}\n"
            else:
                output += f"📝 LATEST COMMIT\n"
            output += f"{'='*70}\n\n"
            
            output += f"🔖 Commit Hash    : {hash_short}\n"
            output += f"👤 Author         : {author_name} <{author_email}>\n"
            output += f"📅 Commit Date    : {author_date}\n"
            output += f"⚙️  Committer       : {committer_name}\n"
            if url:
                output += f"🔗 URL             : {url}\n"
            output += "\n"
            
            output += f"💬 MESSAGE:\n"
            output += f"{'─'*70}\n"
            output += f"{message}\n\n"
            
            output += f"{'='*70}\n"
            return output
            
        except Exception as e:
            return f"Error formatting commit: {str(e)}"
    
    @staticmethod
    def format_health_report(app_name: str, data: Dict[str, Any]) -> str:
        """Format comprehensive health report combining all agents."""
        try:
            argocd_data = data.get("argocd", {})
            github_data = data.get("github", {})
            grafana_data = data.get("grafana", {})
            metadata = data.get("metadata", {})
            
            # Extract key info
            argocd_status = argocd_data.get("status", {}).get("sync", {}).get("status", "Unknown")
            argocd_health = argocd_data.get("status", {}).get("health", {}).get("status", "Unknown")
            
            # Status emojis
            argocd_emoji = "✅" if argocd_status == "Synced" else "⚠️"
            health_emoji = "✅" if argocd_health == "Healthy" else "🔴"
            github_emoji = "✅" if github_data else "❌"
            grafana_emoji = "✅" if grafana_data.get("dashboards") else "⚠️"
            
            # Overall health
            all_checks = [
                argocd_status == "Synced",
                argocd_health == "Healthy",
                bool(github_data),
                bool(grafana_data.get("dashboards"))
            ]
            overall_health = sum(all_checks) / len(all_checks) * 100
            
            output = f"\n{'='*80}\n"
            output += f"📊 COMPREHENSIVE HEALTH REPORT: {app_name.upper()}\n"
            output += f"{'='*80}\n\n"
            
            # Executive Summary
            output += "🎯 EXECUTIVE SUMMARY\n"
            output += f"{'─'*80}\n"
            output += f"Application Status: {'HEALTHY' if overall_health >= 75 else 'DEGRADED' if overall_health >= 50 else 'CRITICAL'}\n"
            output += f"Overall Health Score: {overall_health:.0f}%\n\n"
            
            # Deployment Status
            output += "🚀 DEPLOYMENT STATUS\n"
            output += f"{'─'*80}\n"
            output += f"{argocd_emoji} Sync Status         : {argocd_status}\n"
            output += f"{health_emoji} Health Status       : {argocd_health}\n"
            if argocd_data.get("spec", {}).get("source", {}).get("repoURL"):
                output += f"📁 Repository         : {argocd_data['spec']['source']['repoURL']}\n"
            if argocd_data.get("spec", {}).get("source", {}).get("targetRevision"):
                output += f"🏷️  Target Revision    : {argocd_data['spec']['source']['targetRevision']}\n"
            output += "\n"
            
            # Code Status
            if github_data:
                output += "💻 SOURCE CODE STATUS\n"
                output += f"{'─'*80}\n"
                output += f"{github_emoji} Repository Status  : Available\n"
                if github_data.get("repo"):
                    output += f"📦 Repository URL    : {github_data['repo']}\n"
                if github_data.get("latest_commit"):
                    commit = github_data["latest_commit"]
                    output += f"📝 Latest Commit     : {commit.get('message', 'N/A')[:50]}...\n"
                    output += f"👤 Author            : {commit.get('author', {}).get('name', 'N/A')}\n"
                    output += f"📅 Commit Date       : {commit.get('author', {}).get('date', 'N/A')}\n"
                output += "\n"
            
            # Observability
            output += "📊 OBSERVABILITY\n"
            output += f"{'─'*80}\n"
            if grafana_data.get("dashboards"):
                output += f"{grafana_emoji} Dashboards         : {len(grafana_data['dashboards'])} found\n"
                for dash in grafana_data["dashboards"][:3]:
                    output += f"  📈 {dash.get('title', 'Unknown')}\n"
                if len(grafana_data["dashboards"]) > 3:
                    output += f"  ... and {len(grafana_data['dashboards']) - 3} more\n"
            else:
                output += f"{grafana_emoji} Dashboards         : Not available\n"
            
            if grafana_data.get("alerts"):
                alerts = grafana_data["alerts"]
                output += f"\n🚨 Alert Rules       : {len(alerts)} total\n"
                firing = sum(1 for a in alerts if a.get("state") == "firing")
                if firing > 0:
                    output += f"   🔴 Firing         : {firing}\n"
                    for alert in [a for a in alerts if a.get("state") == "firing"][:3]:
                        output += f"     • {alert.get('name', 'Unknown')}\n"
            output += "\n"
            
            # Analysis & Recommendations
            output += "💡 ANALYSIS & RECOMMENDATIONS\n"
            output += f"{'─'*80}\n"
            
            issues = []
            if argocd_status != "Synced":
                issues.append("❌ Application is out of sync - consider running sync operation")
            if argocd_health != "Healthy":
                issues.append("🔴 Application health is degraded - check resource status")
            if grafana_data.get("alerts"):
                firing_alerts = [a for a in grafana_data["alerts"] if a.get("state") == "firing"]
                if firing_alerts:
                    issues.append(f"⚠️  {len(firing_alerts)} alert(s) currently firing")
            if not github_data:
                issues.append("⚠️  Source code repository information not available")
            
            if issues:
                for issue in issues:
                    output += f"{issue}\n"
            else:
                output += "✅ All systems operational. No critical issues detected.\n"
            
            # Best practices
            output += "\n📋 BEST PRACTICES CHECK\n"
            best_practices = []
            if argocd_status == "Synced":
                best_practices.append("✅ Deployment is synchronized with source")
            if argocd_health == "Healthy":
                best_practices.append("✅ All resources are healthy")
            if github_data:
                best_practices.append("✅ Source repository is accessible")
            if grafana_data.get("dashboards"):
                best_practices.append("✅ Monitoring dashboards configured")
            
            for practice in best_practices:
                output += f"{practice}\n"
            
            output += f"\n{'='*80}\n"
            output += f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            output += f"{'='*80}\n"
            
            return output
            
        except Exception as e:
            return f"Error formatting health report: {str(e)}"
