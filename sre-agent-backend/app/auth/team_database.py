"""
Team Database with MongoDB

Persistent storage for teams, assignments, and permissions.
"""
from typing import Dict, Optional, List
from datetime import datetime
from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING
from ..database import get_db, Collections
from .models import (
    UserRole, TeamResponse, TeamMemberResponse,
    AgentType, AgentPriority, TeamAssignmentResponse, TeamAgentResponse
)
import uuid
import logging

logger = logging.getLogger(__name__)


class TeamDatabase:
    """
    MongoDB-backed team database for RBAC.
    """
    
    def __init__(self):
        self.db = get_db()
        self.teams_collection: Optional[Collection] = None
        self.assignments_collection: Optional[Collection] = None
        self.user_permissions_collection: Optional[Collection] = None
        self.team_permissions_collection: Optional[Collection] = None
        
        if self.db is not None:
            self.teams_collection = self.db[Collections.TEAMS]
            self.assignments_collection = self.db["team_assignments"]
            self.user_permissions_collection = self.db["user_permissions"]
            self.team_permissions_collection = self.db["team_permissions"]
            self._create_indexes()
            self._create_default_teams()
        else:
            logger.warning("⚠️ MongoDB not available, using in-memory fallback")
            self.teams: Dict[str, Dict] = {}
            self.team_assignments: Dict[str, Dict] = {}
            self.user_permissions: Dict[str, Dict] = {}
            self.team_permissions: Dict[str, Dict] = {}
            self._create_default_teams()
    
    def _create_indexes(self):
        """Create MongoDB indexes for efficient queries."""
        if self.teams_collection is None:
            return
        
        try:
            # Team indexes - Note: unique constraints enforced at application level
            self.teams_collection.create_index(
                [("id", ASCENDING)],
                name="team_id_index"
            )
            self.teams_collection.create_index(
                [("name", ASCENDING)],
                name="team_name_index"
            )
            self.teams_collection.create_index(
                [("is_active", ASCENDING)],
                name="is_active_index"
            )
            
            # Assignment indexes
            self.assignments_collection.create_index(
                [("id", ASCENDING)],
                name="assignment_id_index"
            )
            self.assignments_collection.create_index(
                [("user_id", ASCENDING)],
                name="user_assignments_index"
            )
            self.assignments_collection.create_index(
                [("team_id", ASCENDING)],
                name="team_members_index"
            )
            self.assignments_collection.create_index(
                [("user_id", ASCENDING), ("team_id", ASCENDING)],
                name="user_team_index"
            )
            
            # Permission indexes
            self.user_permissions_collection.create_index(
                [("id", ASCENDING)],
                name="user_permission_id_index"
            )
            self.user_permissions_collection.create_index(
                [("user_id", ASCENDING)],
                name="user_permissions_index"
            )
            
            self.team_permissions_collection.create_index(
                [("id", ASCENDING)],
                name="team_permission_id_index"
            )
            self.team_permissions_collection.create_index(
                [("team_id", ASCENDING)],
                name="team_permissions_index"
            )
            
            logger.info("✅ Team database indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    def _create_default_teams(self):
        """Create default teams for demonstration."""
        try:
            # Check if teams already exist
            if self.teams_collection is not None:
                if self.teams_collection.count_documents({}) > 0:
                    return
            elif self.teams:
                return
            
            # SRE Team
            sre_team = {
                "id": str(uuid.uuid4()),
                "name": "SRE Team",
                "description": "Site Reliability Engineering team responsible for system monitoring and incident response",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            
            # DevOps Team
            devops_team = {
                "id": str(uuid.uuid4()),
                "name": "DevOps Team",
                "description": "Development Operations team managing CI/CD pipelines and deployments",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            
            # Security Team
            security_team = {
                "id": str(uuid.uuid4()),
                "name": "Security Team",
                "description": "Information Security team handling security monitoring and compliance",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            
            if self.teams_collection is not None:
                self.teams_collection.insert_many([sre_team, devops_team, security_team])
            else:
                # In-memory fallback
                for team in [sre_team, devops_team, security_team]:
                    team["created_at"] = team["created_at"].isoformat()
                    team["updated_at"] = team["updated_at"].isoformat()
                    self.teams[team["id"]] = team
            
            logger.info("✅ Default teams created successfully")
        except Exception as e:
            logger.error(f"Error creating default teams: {e}")
    
    # ==================== Team Management ====================
    
    def create_team(self, name: str, description: Optional[str] = None) -> Dict:
        """Create a new team."""
        # Check if team name already exists
        if self.get_team_by_name(name):
            raise ValueError("Team name already exists")
        
        team_data = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        if self.teams_collection is not None:
            self.teams_collection.insert_one(team_data.copy())
            team_data["created_at"] = team_data["created_at"].isoformat()
            team_data["updated_at"] = team_data["updated_at"].isoformat()
        else:
            team_data["created_at"] = team_data["created_at"].isoformat()
            team_data["updated_at"] = team_data["updated_at"].isoformat()
            self.teams[team_data["id"]] = team_data
        
        return team_data
    
    def get_team(self, team_id: str) -> Optional[Dict]:
        """Get team by ID."""
        if self.teams_collection is not None:
            team = self.teams_collection.find_one({"id": team_id})
            if team:
                team.pop("_id", None)
                self._convert_dates_to_iso(team)
            return team
        else:
            return self.teams.get(team_id)
    
    def get_team_by_name(self, name: str) -> Optional[Dict]:
        """Get team by name."""
        if self.teams_collection is not None:
            team = self.teams_collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
            if team:
                team.pop("_id", None)
                self._convert_dates_to_iso(team)
            return team
        else:
            for team in self.teams.values():
                if team["name"].lower() == name.lower():
                    return team
            return None
    
    def get_all_teams(self) -> List[Dict]:
        """Get all teams."""
        if self.teams_collection is not None:
            teams = []
            for team in self.teams_collection.find():
                team.pop("_id", None)
                self._convert_dates_to_iso(team)
                teams.append(team)
            return teams
        else:
            return list(self.teams.values())
    
    def update_team(self, team_id: str, updates: Dict) -> Optional[Dict]:
        """Update team data."""
        # Check name uniqueness if name is being updated
        if "name" in updates:
            existing = self.get_team_by_name(updates["name"])
            if existing and existing["id"] != team_id:
                raise ValueError("Team name already exists")
        
        # Remove id from updates
        updates.pop("id", None)
        updates["updated_at"] = datetime.utcnow()
        
        if self.teams_collection is not None:
            result = self.teams_collection.find_one_and_update(
                {"id": team_id},
                {"$set": updates},
                return_document=True
            )
            if result:
                result.pop("_id", None)
                self._convert_dates_to_iso(result)
            return result
        else:
            team = self.teams.get(team_id)
            if not team:
                return None
            
            team.update(updates)
            team["updated_at"] = datetime.utcnow().isoformat()
            return team
    
    def delete_team(self, team_id: str) -> bool:
        """Delete a team and all its assignments."""
        if self.teams_collection is not None:
            # Delete team
            team_result = self.teams_collection.delete_one({"id": team_id})
            # Delete assignments
            self.assignments_collection.delete_many({"team_id": team_id})
            # Delete permissions
            self.team_permissions_collection.delete_many({"team_id": team_id})
            return team_result.deleted_count > 0
        else:
            if team_id not in self.teams:
                return False
            
            # Remove assignments
            assignments_to_remove = [
                aid for aid, assignment in self.team_assignments.items()
                if assignment["team_id"] == team_id
            ]
            for aid in assignments_to_remove:
                del self.team_assignments[aid]
            
            # Remove permissions
            permissions_to_remove = [
                pid for pid, permission in self.team_permissions.items()
                if permission.get("team_id") == team_id
            ]
            for pid in permissions_to_remove:
                del self.team_permissions[pid]
            
            del self.teams[team_id]
            return True
    
    # ==================== Team Assignment Management ====================
    
    def assign_user_to_team(
        self,
        user_id: str,
        team_id: str,
        is_team_lead: bool = False,
        assigned_by: str = "system"
    ) -> Dict:
        """Assign a user to a team."""
        # Check if team exists
        if not self.get_team(team_id):
            raise ValueError("Team does not exist")
        
        # Check if assignment already exists
        if self.teams_collection is not None:
            existing = self.assignments_collection.find_one({
                "user_id": user_id,
                "team_id": team_id
            })
            if existing:
                raise ValueError("User is already assigned to this team")
        else:
            for assignment in self.team_assignments.values():
                if assignment["user_id"] == user_id and assignment["team_id"] == team_id:
                    raise ValueError("User is already assigned to this team")
        
        assignment_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "team_id": team_id,
            "is_team_lead": is_team_lead,
            "assigned_at": datetime.utcnow(),
            "assigned_by": assigned_by,
        }
        
        if self.assignments_collection is not None:
            self.assignments_collection.insert_one(assignment_data.copy())
            assignment_data["assigned_at"] = assignment_data["assigned_at"].isoformat()
        else:
            assignment_data["assigned_at"] = assignment_data["assigned_at"].isoformat()
            self.team_assignments[assignment_data["id"]] = assignment_data
        
        return assignment_data
    
    def remove_user_from_team(self, user_id: str, team_id: str) -> bool:
        """Remove a user from a team."""
        if self.assignments_collection is not None:
            result = self.assignments_collection.delete_one({
                "user_id": user_id,
                "team_id": team_id
            })
            return result.deleted_count > 0
        else:
            assignment_to_remove = None
            for aid, assignment in self.team_assignments.items():
                if assignment["user_id"] == user_id and assignment["team_id"] == team_id:
                    assignment_to_remove = aid
                    break
            
            if assignment_to_remove:
                del self.team_assignments[assignment_to_remove]
                return True
            return False
    
    def get_user_teams(self, user_id: str) -> List[Dict]:
        """Get all teams for a user."""
        if self.assignments_collection is not None:
            user_teams = []
            for assignment in self.assignments_collection.find({"user_id": user_id}):
                team = self.get_team(assignment["team_id"])
                if team:
                    team_copy = team.copy()
                    team_copy["is_team_lead"] = assignment["is_team_lead"]
                    if isinstance(assignment.get("assigned_at"), datetime):
                        team_copy["assigned_at"] = assignment["assigned_at"].isoformat()
                    else:
                        team_copy["assigned_at"] = assignment.get("assigned_at")
                    user_teams.append(team_copy)
            return user_teams
        else:
            user_teams = []
            for assignment in self.team_assignments.values():
                if assignment["user_id"] == user_id:
                    team = self.teams.get(assignment["team_id"])
                    if team:
                        team_copy = team.copy()
                        team_copy["is_team_lead"] = assignment["is_team_lead"]
                        team_copy["assigned_at"] = assignment["assigned_at"]
                        user_teams.append(team_copy)
            return user_teams
    
    def get_team_members(self, team_id: str) -> List[Dict]:
        """Get all members of a team."""
        if self.assignments_collection is not None:
            members = []
            for assignment in self.assignments_collection.find({"team_id": team_id}):
                assignment.pop("_id", None)
                if isinstance(assignment.get("assigned_at"), datetime):
                    assignment["assigned_at"] = assignment["assigned_at"].isoformat()
                members.append({
                    "user_id": assignment["user_id"],
                    "is_team_lead": assignment["is_team_lead"],
                    "assigned_at": assignment["assigned_at"],
                    "assigned_by": assignment["assigned_by"]
                })
            return members
        else:
            members = []
            for assignment in self.team_assignments.values():
                if assignment["team_id"] == team_id:
                    members.append({
                        "user_id": assignment["user_id"],
                        "is_team_lead": assignment["is_team_lead"],
                        "assigned_at": assignment["assigned_at"],
                        "assigned_by": assignment["assigned_by"]
                    })
            return members
    
    def update_team_lead(self, team_id: str, user_id: str, is_team_lead: bool) -> bool:
        """Update team lead status for a user."""
        if self.assignments_collection is not None:
            result = self.assignments_collection.update_one(
                {"team_id": team_id, "user_id": user_id},
                {"$set": {"is_team_lead": is_team_lead}}
            )
            return result.modified_count > 0
        else:
            for assignment in self.team_assignments.values():
                if assignment["team_id"] == team_id and assignment["user_id"] == user_id:
                    assignment["is_team_lead"] = is_team_lead
                    return True
            return False
    
    # ==================== Agent Management ====================
    
    def assign_team_agent(
        self,
        team_id: str,
        agent_type: str,  # AgentType
        priority: str,    # AgentPriority
        assigned_by: str
    ) -> Dict:
        """Assign an agent to a team with specified priority (primary/secondary)."""
        if not self.get_team(team_id):
            raise ValueError("Team does not exist")
        
        agent_data = {
            "id": str(uuid.uuid4()),
            "team_id": team_id,
            "agent_type": agent_type,
            "priority": priority,
            "assigned_by": assigned_by,
            "assigned_at": datetime.utcnow(),
        }
        
        if self.team_permissions_collection is not None:
            self.team_permissions_collection.insert_one(agent_data.copy())
            agent_data["assigned_at"] = agent_data["assigned_at"].isoformat()
        else:
            agent_data["assigned_at"] = agent_data["assigned_at"].isoformat()
            self.team_permissions[agent_data["id"]] = agent_data
        
        return agent_data
    
    def remove_team_agent(self, agent_id: str) -> bool:
        """Remove an agent assignment from a team."""
        if self.team_permissions_collection is not None:
            result = self.team_permissions_collection.delete_one({"id": agent_id})
            return result.deleted_count > 0
        else:
            if agent_id in self.team_permissions:
                del self.team_permissions[agent_id]
                return True
            return False
    
    def get_user_permissions(self, user_id: str) -> List[Dict]:
        """Get all permissions for a user (direct + team permissions)."""
        permissions = []
        
        # Direct user permissions
        if self.user_permissions_collection is not None:
            for permission in self.user_permissions_collection.find({"user_id": user_id}):
                permission.pop("_id", None)
                if isinstance(permission.get("granted_at"), datetime):
                    permission["granted_at"] = permission["granted_at"].isoformat()
                permissions.append(permission)
        else:
            for permission in self.user_permissions.values():
                if permission["user_id"] == user_id:
                    permissions.append(permission)
        
        # Team permissions
        user_teams = self.get_user_teams(user_id)
        for team in user_teams:
            if self.team_permissions_collection is not None:
                for permission in self.team_permissions_collection.find({"team_id": team["id"]}):
                    permission.pop("_id", None)
                    if isinstance(permission.get("granted_at"), datetime):
                        permission["granted_at"] = permission["granted_at"].isoformat()
                    team_permission = permission.copy()
                    team_permission["via_team"] = team["name"]
                    permissions.append(team_permission)
            else:
                for permission in self.team_permissions.values():
                    if permission["team_id"] == team["id"]:
                        team_permission = permission.copy()
                        team_permission["via_team"] = team["name"]
                        permissions.append(team_permission)
        
        return permissions
    
    def get_team_agents(self, team_id: str, priority: str = None) -> List[Dict]:
        """Get all agent assignments for a team, optionally filtered by priority."""
        query = {"team_id": team_id}
        if priority:
            query["priority"] = priority
            
        if self.team_permissions_collection is not None:
            agents = []
            for agent in self.team_permissions_collection.find(query):
                agent.pop("_id", None)
                if isinstance(agent.get("assigned_at"), datetime):
                    agent["assigned_at"] = agent["assigned_at"].isoformat()
                agents.append(agent)
            return agents
        else:
            result = [
                a for a in self.team_permissions.values()
                if a["team_id"] == team_id
            ]
            if priority:
                result = [a for a in result if a.get("priority") == priority]
            return result
    
    # ==================== Helper Methods ====================
    
    def _convert_dates_to_iso(self, doc: Dict):
        """Convert datetime objects to ISO strings in a document."""
        for key in ["created_at", "updated_at", "assigned_at", "granted_at"]:
            if key in doc and isinstance(doc[key], datetime):
                doc[key] = doc[key].isoformat()


# Global team database instance
team_db = TeamDatabase()
