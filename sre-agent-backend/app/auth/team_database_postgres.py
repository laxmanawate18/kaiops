"""
Team Database with PostgreSQL

Persistent storage for teams, assignments, and permissions.
"""
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from ..database.postgres_config import PostgresConfig
from ..database.models import Team, User, UserPermission, TeamPermission, team_users_association
from .models import UserRole, TeamResponse, TeamMemberResponse
import uuid
import logging

logger = logging.getLogger(__name__)


class TeamDatabase:
    """PostgreSQL-backed team database for RBAC."""
    
    def __init__(self):
        """Initialize team database."""
        try:
            PostgresConfig.check_database_exists()
            logger.info("✅ Team database initialized with PostgreSQL")
            self._create_default_teams()
        except Exception as e:
            logger.error(f"Failed to initialize team database: {e}")
            raise
    
    def _create_default_teams(self):
        """Create default teams."""
        try:
            db = PostgresConfig.get_session()
            
            if db.query(Team).count() > 0:
                logger.info("Default teams already exist")
                db.close()
                return
            
            logger.info("Creating default teams...")
            
            # SRE Team
            sre_team = Team(
                id=str(uuid.uuid4()),
                name="SRE Team",
                description="Site Reliability Engineering team responsible for system monitoring and incident response",
                is_active=True,
                created_at=datetime.now()
            )
            
            # DevOps Team
            devops_team = Team(
                id=str(uuid.uuid4()),
                name="DevOps Team",
                description="Development Operations team managing CI/CD pipelines and deployments",
                is_active=True,
                created_at=datetime.now()
            )
            
            # Security Team
            security_team = Team(
                id=str(uuid.uuid4()),
                name="Security Team",
                description="Information Security team handling security monitoring and compliance",
                is_active=True,
                created_at=datetime.now()
            )
            
            db.add_all([sre_team, devops_team, security_team])
            db.commit()
            
            logger.info("✅ Default teams created successfully")
            db.close()
            
        except Exception as e:
            logger.error(f"❌ Error creating default teams: {e}")
            db.rollback()
            db.close()
    
    # ==================== TEAM CRUD OPERATIONS ====================
    
    def create_team(self, name: str, description: Optional[str] = None) -> Dict:
        """Create a new team."""
        try:
            db = PostgresConfig.get_session()
            
            team = Team(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                is_active=True,
                created_at=datetime.now()
            )
            
            db.add(team)
            db.commit()
            
            result = self._convert_team_to_dict(team)
            db.close()
            
            logger.info(f"✅ Created team: {name}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error creating team: {e}")
            db.close()
            raise
    
    def get_team(self, team_id: str) -> Optional[Dict]:
        """Get team by ID."""
        try:
            db = PostgresConfig.get_session()
            team = db.query(Team).filter(Team.id == team_id).first()
            result = self._convert_team_to_dict(team) if team else None
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting team {team_id}: {e}")
            db.close()
            return None
    
    def get_all_teams(self) -> List[Dict]:
        """Get all teams."""
        try:
            db = PostgresConfig.get_session()
            teams = db.query(Team).filter(Team.is_active == True).all()
            result = [self._convert_team_to_dict(team) for team in teams]
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting all teams: {e}")
            db.close()
            return []
    
    def update_team(self, team_id: str, updates: Dict) -> Optional[Dict]:
        """Update team details."""
        try:
            db = PostgresConfig.get_session()
            
            team = db.query(Team).filter(Team.id == team_id).first()
            if not team:
                logger.warning(f"Team {team_id} not found")
                db.close()
                return None
            
            allowed_fields = ['name', 'description', 'is_active']
            for key, value in updates.items():
                if key in allowed_fields and hasattr(team, key):
                    setattr(team, key, value)
            
            team.updated_at = datetime.now()
            db.commit()
            
            result = self._convert_team_to_dict(team)
            db.close()
            
            logger.info(f"✅ Updated team: {team_id}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error updating team: {e}")
            db.close()
            raise
    
    def delete_team(self, team_id: str) -> bool:
        """Delete a team."""
        try:
            db = PostgresConfig.get_session()
            
            team = db.query(Team).filter(Team.id == team_id).first()
            if not team:
                logger.warning(f"Team {team_id} not found")
                db.close()
                return False
            
            db.delete(team)
            db.commit()
            
            logger.info(f"✅ Deleted team: {team_id}")
            db.close()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error deleting team: {e}")
            db.close()
            return False
    
    # ==================== TEAM MEMBER OPERATIONS ====================
    
    def assign_user_to_team(self, user_id: str, team_id: str, is_team_lead: bool = False) -> Dict:
        """Assign a user to a team."""
        try:
            db = PostgresConfig.get_session()
            
            # Check if user and team exist
            user = db.query(User).filter(User.id == user_id).first()
            team = db.query(Team).filter(Team.id == team_id).first()
            
            if not user or not team:
                raise ValueError("User or team not found")
            
            # Check if already assigned
            existing = db.query(team_users_association).filter(
                team_users_association.c.user_id == user_id,
                team_users_association.c.team_id == team_id
            ).first()
            
            if existing:
                logger.warning(f"User {user_id} already assigned to team {team_id}")
                db.close()
                raise ValueError("User already assigned to this team")
            
            # Create assignment
            stmt = team_users_association.insert().values(
                user_id=user_id,
                team_id=team_id,
                is_team_lead=is_team_lead,
                assigned_at=datetime.now()
            )
            db.execute(stmt)
            db.commit()
            
            result = {
                "user_id": user_id,
                "team_id": team_id,
                "is_team_lead": is_team_lead,
                "assigned_at": datetime.now().isoformat()
            }
            
            db.close()
            logger.info(f"✅ Assigned user {user_id} to team {team_id}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error assigning user to team: {e}")
            db.close()
            raise
    
    def get_team_members(self, team_id: str) -> List[Dict]:
        """Get all members of a team."""
        try:
            db = PostgresConfig.get_session()
            
            team = db.query(Team).filter(Team.id == team_id).first()
            if not team:
                db.close()
                return []
            
            members = []
            for user in team.users:
                members.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role
                })
            
            db.close()
            return members
            
        except Exception as e:
            logger.error(f"Error getting team members for {team_id}: {e}")
            db.close()
            return []
    
    def get_user_teams(self, user_id: str) -> List[Dict]:
        """Get all teams for a user."""
        try:
            db = PostgresConfig.get_session()
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                db.close()
                return []
            
            teams = [self._convert_team_to_dict(team) for team in user.teams]
            db.close()
            
            return teams
            
        except Exception as e:
            logger.error(f"Error getting teams for user {user_id}: {e}")
            db.close()
            return []
    
    def remove_user_from_team(self, user_id: str, team_id: str) -> bool:
        """Remove a user from a team."""
        try:
            db = PostgresConfig.get_session()
            
            stmt = team_users_association.delete().where(
                (team_users_association.c.user_id == user_id) &
                (team_users_association.c.team_id == team_id)
            )
            db.execute(stmt)
            db.commit()
            
            logger.info(f"✅ Removed user {user_id} from team {team_id}")
            db.close()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error removing user from team: {e}")
            db.close()
            return False
    
    # ==================== PERMISSIONS ====================
    
    def grant_permission(self, user_id: str, resource: str, action: str) -> Dict:
        """Grant a permission to a user."""
        try:
            db = PostgresConfig.get_session()
            
            permission = UserPermission(
                id=str(uuid.uuid4()),
                user_id=user_id,
                resource=resource,
                action=action,
                granted=True,
                created_at=datetime.now()
            )
            
            db.add(permission)
            db.commit()
            
            result = {
                "id": permission.id,
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "granted": True
            }
            
            db.close()
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error granting permission: {e}")
            db.close()
            raise
    
    def get_user_permissions(self, user_id: str) -> List[Dict]:
        """Get all permissions for a user."""
        try:
            db = PostgresConfig.get_session()
            
            perms = db.query(UserPermission).filter(UserPermission.user_id == user_id).all()
            result = [
                {
                    "id": p.id,
                    "resource": p.resource,
                    "action": p.action,
                    "granted": p.granted
                }
                for p in perms
            ]
            
            db.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting permissions for user {user_id}: {e}")
            db.close()
            return []
    
    # ==================== HELPER METHODS ====================
    
    @staticmethod
    def _convert_team_to_dict(team: Team) -> Dict:
        """Convert Team model to dictionary."""
        if not team:
            return None
        
        return {
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "is_active": team.is_active,
            "created_at": team.created_at.isoformat() if team.created_at else None,
            "updated_at": team.updated_at.isoformat() if team.updated_at else None,
        }


# Global database instance
team_db = TeamDatabase()
