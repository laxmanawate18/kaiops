"""
GitHub Agent Tools

MCP tool wrappers for source code management via GitHub.
All tools communicate with github-mcp-server.
"""

import sys
import os
from typing import Dict, Any

# Add parent to path for mcp_client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.mcp_client import call_mcp_tool, parse_mcp_response


async def get_latest_commit(owner: str, repo: str) -> str:
    """
    Get the latest commit from a GitHub repository with comprehensive details.
    
    Args:
        owner: Repository owner (extracted from github_repo metadata)
        repo: Repository name (extracted from github_repo metadata)
    
    Returns:
        Formatted commit information with emojis, links, and full details
    """
    try:
        if not owner or not repo or owner.lower() == "n/a" or repo.lower() == "n/a":
            return "⚠️ **No GitHub Repository**\nGitHub repository not configured for this application."
        
        result = await call_mcp_tool("github", "get_latest_commit", owner=owner, repo=repo)
        data = parse_mcp_response(result)

        if "error" in data:
            return f"❌ **GitHub Error**: {data['error']}"

        # Debug: Log what we received from MCP
        import json
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"📨 MCP Response (raw): {json.dumps(data, indent=2)}")

        # Handle nested author structure
        commit = data.get("commit", {})
        author_obj = commit.get("author", {}) if isinstance(commit.get("author"), dict) else {}
        author = author_obj.get("name", "Unknown") if isinstance(author_obj, dict) else "Unknown"
        email = author_obj.get("email", "") if isinstance(author_obj, dict) else ""
        date = author_obj.get("date", "Unknown") if isinstance(author_obj, dict) else "Unknown"
        
        full_sha = data.get("sha", "Unknown")
        sha_short = full_sha[:8] if full_sha and full_sha != "Unknown" else "Unknown"
        message = commit.get("message", "No message")
        
        # Extract additional details with fallback handling
        files_changed = data.get("stats", {}).get("files", "N/A") if isinstance(data.get("stats"), dict) else data.get("files_changed", "N/A")
        additions = data.get("stats", {}).get("additions", "N/A") if isinstance(data.get("stats"), dict) else data.get("additions", "N/A")
        deletions = data.get("stats", {}).get("deletions", "N/A") if isinstance(data.get("stats"), dict) else data.get("deletions", "N/A")
        branch = data.get("branch", "main")
        
        # Create actual GitHub URLs
        repo_url = f"https://github.com/{owner}/{repo}"
        commit_url = f"{repo_url}/commit/{full_sha}" if full_sha != "Unknown" else "#"
        
        output = f"💻 **Latest Commit**: {owner}/{repo}\n\n"
        output += f"**📝 Commit Details**:\n"
        output += f"• **Hash**: `{sha_short}` ([View Full]({commit_url}))\n"
        output += f"• **Author**: {author}" + (f" <{email}>" if email else "") + "\n"
        output += f"• **Date**: {date}\n"
        output += f"• **Branch**: `{branch}`\n\n"
        
        output += f"**📋 Message**:\n"
        output += f"{message}\n\n"
        
        output += f"**📊 Changes**:\n"
        output += f"• Files Changed: {files_changed}\n"
        output += f"• Additions: +{additions}\n"
        output += f"• Deletions: -{deletions}\n\n"
        
        output += f"**🔗 Repository Links**:\n"
        output += f"• [📂 View Repository]({repo_url})\n"
        output += f"• [📜 View All Commits]({repo_url}/commits)\n"
        output += f"• [🌿 View Branches]({repo_url}/branches)\n"
        output += f"• [⭐ Star on GitHub]({repo_url})\n"
        
        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


async def get_repository_info(owner: str, repo: str) -> str:
    """
    Get detailed information about a GitHub repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
    
    Returns:
        Formatted repository information
    """
    try:
        if not owner or not repo:
            return "⚠️ **Invalid Repository Parameters**"
        
        result = await call_mcp_tool("github", "get_repository_info", owner=owner, repo=repo)
        data = parse_mcp_response(result)

        if "error" in data:
            return f"❌ **Error Fetching Repository**: {data['error']}"

        output = f"📁 **Repository Info**: {owner}/{repo}\n\n"
        output += f"**URL**: {data.get('url', 'N/A')}\n"
        output += f"**Description**: {data.get('description', 'N/A')}\n"
        output += f"**Stars**: ⭐ {data.get('stars', 0)}\n"
        output += f"**Forks**: 🍴 {data.get('forks', 0)}\n"
        output += f"**Language**: {data.get('language', 'Unknown')}\n"
        output += f"**Default Branch**: {data.get('default_branch', 'main')}\n"
        output += f"**Open Issues**: {data.get('open_issues', 0)}\n"
        
        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


async def search_repositories(query: str, sort: str = "stars", per_page: int = 10) -> str:
    """
    Search for GitHub repositories by query.
    
    Args:
        query: Search query
        sort: Sort by (stars, forks, updated)
        per_page: Number of results
    
    Returns:
        Formatted search results
    """
    try:
        result = await call_mcp_tool("github", "search_repositories", query=query, sort=sort, per_page=per_page)
        data = parse_mcp_response(result)

        if "error" in data:
            return f"❌ **Search Error**: {data['error']}"

        repos = data.get("repositories", [])
        if not repos:
            return f"⚠️ **No Repositories Found**\nNo results for '{query}'"

        output = f"🔍 **Repository Search Results**: {query}\n\n"
        for i, repo in enumerate(repos, 1):
            name = repo.get("full_name", "Unknown")
            desc = repo.get("description", "")
            stars = repo.get("stars", 0)
            output += f"{i}. **{name}** ({stars}⭐)\n"
            if desc:
                output += f"   {desc}\n"
            output += "\n"

        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


async def search_code(owner: str, repo: str, query: str, per_page: int = 10) -> str:
    """
    Search code within a GitHub repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        query: Code search query
        per_page: Number of results
    
    Returns:
        Formatted search results with file paths and line numbers
    """
    try:
        result = await call_mcp_tool("github", "search_code", owner=owner, repo=repo, query=query, per_page=per_page)
        data = parse_mcp_response(result)

        if "error" in data:
            return f"❌ **Search Error**: {data['error']}"

        results = data.get("results", [])
        if not results:
            return f"⚠️ **No Code Found**\nNo matches for '{query}' in {owner}/{repo}"

        output = f"🔍 **Code Search**: {owner}/{repo}\n"
        output += f"**Query**: {query}\n\n"
        for i, result in enumerate(results, 1):
            path = result.get("path", "Unknown")
            line = result.get("line_number", "?")
            output += f"{i}. `{path}` (line {line})\n"

        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


async def list_issues(owner: str, repo: str, state: str = "open", per_page: int = 10) -> str:
    """
    List GitHub issues in a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        state: Issue state (open, closed, all)
        per_page: Number of results
    
    Returns:
        Formatted list of issues
    """
    try:
        result = await call_mcp_tool("github", "list_issues", owner=owner, repo=repo, state=state, per_page=per_page)
        data = parse_mcp_response(result)

        if "error" in data:
            return f"❌ **Error Fetching Issues**: {data['error']}"

        issues = data.get("issues", [])
        if not issues:
            return f"✅ **No {state.capitalize()} Issues**\n{owner}/{repo} has no {state} issues"

        output = f"🚨 **GitHub Issues**: {owner}/{repo} ({state})\n\n"
        for issue in issues[:per_page]:
            number = issue.get("number", "?")
            title = issue.get("title", "Unknown")
            state_val = issue.get("state", "unknown")
            state_emoji = "🟢" if state_val == "closed" else "🔴"
            output += f"{state_emoji} **#{number}**: {title}\n"

        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


async def get_user_repositories(username: str, per_page: int = 10) -> str:
    """
    List repositories owned by a GitHub user.
    
    Args:
        username: GitHub username
        per_page: Number of results
    
    Returns:
        Formatted list of user's repositories
    """
    try:
        result = await call_mcp_tool("github", "get_user_repositories", username=username, per_page=per_page)
        data = parse_mcp_response(result)

        if "error" in data:
            return f"❌ **User Not Found**: {data['error']}"

        repos = data.get("repositories", [])
        if not repos:
            return f"⚠️ **No Repositories**\nUser '{username}' has no repositories"

        output = f"👤 **Repositories by {username}**\n\n"
        for repo in repos[:per_page]:
            name = repo.get("name", "Unknown")
            desc = repo.get("description", "")
            stars = repo.get("stars", 0)
            output += f"• **{name}** ({stars}⭐)"
            if desc:
                output += f"\n  {desc}"
            output += "\n\n"

        return output
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


__all__ = [
    "get_latest_commit",
    "get_repository_info",
    "search_repositories",
    "search_code",
    "list_issues",
    "get_user_repositories"
]
