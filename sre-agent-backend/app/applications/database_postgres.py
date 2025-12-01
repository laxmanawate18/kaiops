"""
Application Database with PostgreSQL

Persistent storage for SRE-enabled application registrations.
"""
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from ..database.postgres_config import PostgresConfig
from ..database.models import Application, ApplicationMetadata
from .models import ApplicationStatus, ApplicationStats
import uuid
import logging

logger = logging.getLogger(__name__)


class ApplicationDatabase:
    """PostgreSQL-backed database for managing SRE-enabled applications."""
    
    def __init__(self):
        """Initialize application database."""
        try:
            PostgresConfig.check_database_exists()
            logger.info("✅ Application database initialized with PostgreSQL")
            self._ensure_demo_applications()
        except Exception as e:
            logger.error(f"Failed to initialize application database: {e}")
            raise
    
    def _ensure_demo_applications(self):
        """Ensure demo applications exist in PostgreSQL."""
        try:
            db = PostgresConfig.get_session()
            
            # Check if demo apps already exist
            count = db.query(Application).count()
            if count > 0:
                logger.info(f"📊 Found {count} existing applications in PostgreSQL")
                db.close()
                return
            
            logger.info("Creating demo applications in PostgreSQL...")
            
            demo_apps = [
                {
                    "application_name": "Payment Gateway",
                    "github_repo": "myorg/payment-gateway",
                    "gcp_project_id": "prod-payment-gw-001",
                    "argocd_app_name": "payment-gateway-prod",
                    "grafana_dashboard": "Payment Gateway Dashboard",
                    "gke_cluster_name": "prod-cluster-us-central1",
                    "namespace": "payment-prod",
                    "application_owner": "admin",
                    "status": ApplicationStatus.ACTIVE.value,
                    "description": "Core payment processing service",
                    "tags": ["payment", "critical", "prod"],
                    "cloud_provider": "gcp"
                },
                {
                    "application_name": "User Service",
                    "github_repo": "myorg/user-service",
                    "gcp_project_id": "prod-user-svc-002",
                    "argocd_app_name": "user-service-prod",
                    "grafana_dashboard": "User Service Metrics",
                    "gke_cluster_name": "prod-cluster-us-east1",
                    "namespace": "user-prod",
                    "application_owner": "admin",
                    "status": ApplicationStatus.ACTIVE.value,
                    "description": "User authentication and profile management",
                    "tags": ["auth", "user", "prod"],
                    "cloud_provider": "gcp"
                },
                {
                    "application_name": "Analytics Engine",
                    "github_repo": "myorg/analytics-engine",
                    "gcp_project_id": "staging-analytics-003",
                    "argocd_app_name": "analytics-engine-staging",
                    "grafana_dashboard": "Analytics Performance",
                    "gke_cluster_name": "staging-cluster-us-west1",
                    "namespace": "analytics-staging",
                    "application_owner": "admin",
                    "status": ApplicationStatus.INACTIVE.value,
                    "description": "Real-time analytics processing pipeline",
                    "tags": ["analytics", "staging", "data"],
                    "cloud_provider": "gcp"
                }
            ]
            
            for app_data in demo_apps:
                app = Application(
                    id=str(uuid.uuid4()),
                    **app_data,
                    created_at=datetime.now()
                )
                db.add(app)
            
            db.commit()
            logger.info(f"✅ Created {len(demo_apps)} demo applications in PostgreSQL")
            db.close()
            
        except Exception as e:
            logger.error(f"❌ Error creating demo applications: {e}")
    
    # ==================== CREATE OPERATIONS ====================
    
    def create_application(self, app_data: Dict) -> Dict:
        """Create a new application."""
        try:
            db = PostgresConfig.get_session()
            
            app_id = str(uuid.uuid4())
            
            # Convert application_owner username to user ID if needed
            owner_value = app_data.get("application_owner")
            if owner_value and '-' not in str(owner_value):
                # It's likely a username, convert to user ID
                from app.database.models import User
                owner_user = db.query(User).filter(User.username == owner_value).first()
                if owner_user:
                    owner_value = owner_user.id
                else:
                    error_msg = f"User '{owner_value}' not found in database"
                    logger.error(error_msg)
                    db.close()
                    raise ValueError(error_msg)
            
            application = Application(
                id=app_id,
                application_name=app_data.get("application_name"),
                description=app_data.get("description"),
                application_owner=owner_value,
                status=app_data.get("status", ApplicationStatus.ACTIVE.value),
                cloud_provider=app_data.get("cloud_provider", "azure"),
                gcp_project_id=app_data.get("gcp_project_id"),
                aws_account_id=app_data.get("aws_account_id"),
                azure_subscription_id=app_data.get("azure_subscription_id"),
                github_repo=app_data.get("github_repo"),
                gke_cluster_name=app_data.get("gke_cluster_name"),
                argocd_app_name=app_data.get("argocd_app_name"),
                grafana_dashboard=app_data.get("grafana_dashboard"),
                namespace=app_data.get("namespace"),
                tags=app_data.get("tags", []),
                created_by=app_data.get("created_by", "system"),
                created_at=datetime.now()
            )
            
            db.add(application)
            db.commit()
            
            result = self._convert_to_dict(application)
            db.close()
            
            logger.info(f"✅ Created application: {app_data.get('application_name')} (ID: {app_id})")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error creating application: {e}")
            db.close()
            raise
    
    # ==================== READ OPERATIONS ====================
    
    def get_application(self, app_id: str) -> Optional[Dict]:
        """Get application by ID."""
        try:
            db = PostgresConfig.get_session()
            app = db.query(Application).filter(Application.id == app_id).first()
            result = self._convert_to_dict(app) if app else None
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting application {app_id}: {e}")
            db.close()
            return None
    
    def get_application_by_name(self, app_name: str) -> Optional[Dict]:
        """Get application by name (case-insensitive)."""
        try:
            db = PostgresConfig.get_session()
            app = db.query(Application).filter(
                Application.application_name.ilike(app_name)
            ).first()
            result = self._convert_to_dict(app) if app else None
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting application by name {app_name}: {e}")
            db.close()
            return None
    
    def get_all_applications(
        self,
        status: Optional[str] = None,
        cluster: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict], int]:
        """Get all applications with optional filtering and pagination."""
        try:
            db = PostgresConfig.get_session()
            query = db.query(Application)
            
            if status:
                query = query.filter(Application.status == status)
            
            if cluster:
                query = query.filter(Application.gke_cluster_name == cluster)
            
            total = query.count()
            
            apps = query.order_by(desc(Application.created_at)).offset(skip).limit(limit).all()
            
            result = [self._convert_to_dict(app) for app in apps]
            db.close()
            
            return result, total
            
        except Exception as e:
            logger.error(f"Error getting applications: {e}")
            db.close()
            return [], 0
    
    def list_applications(
        self,
        status: Optional[str] = None,
        owner: Optional[str] = None,
        cluster: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict], int]:
        """List applications with optional filtering and pagination."""
        try:
            db = PostgresConfig.get_session()
            query = db.query(Application)
            
            if status:
                query = query.filter(Application.status == status)
            
            if owner:
                query = query.filter(Application.application_owner == owner)
            
            if cluster:
                query = query.filter(Application.gke_cluster_name == cluster)
            
            total = query.count()
            
            apps = query.order_by(desc(Application.created_at)).offset(skip).limit(limit).all()
            
            result = [self._convert_to_dict(app) for app in apps]
            db.close()
            
            return result, total
            
        except Exception as e:
            logger.error(f"Error listing applications: {e}")
            db.close()
            return [], 0
    
    
    def search_applications(self, query_text: str, limit: int = 20) -> List[Dict]:
        """Search applications by name or description."""
        try:
            db = PostgresConfig.get_session()
            search_term = f"%{query_text}%"
            
            apps = db.query(Application).filter(
                (Application.application_name.ilike(search_term)) |
                (Application.description.ilike(search_term))
            ).limit(limit).all()
            
            result = [self._convert_to_dict(app) for app in apps]
            db.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching applications: {e}")
            db.close()
            return []
    
    def get_applications_by_owner(self, owner: str) -> List[Dict]:
        """Get all applications owned by a user."""
        try:
            db = PostgresConfig.get_session()
            apps = db.query(Application).filter(
                Application.application_owner == owner
            ).order_by(desc(Application.created_at)).all()
            
            result = [self._convert_to_dict(app) for app in apps]
            db.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting applications by owner {owner}: {e}")
            db.close()
            return []
    
    def get_applications_by_cluster(self, cluster: str) -> List[Dict]:
        """Get all applications in a specific cluster."""
        try:
            db = PostgresConfig.get_session()
            apps = db.query(Application).filter(
                Application.gke_cluster_name == cluster
            ).order_by(desc(Application.created_at)).all()
            
            result = [self._convert_to_dict(app) for app in apps]
            db.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting applications by cluster {cluster}: {e}")
            db.close()
            return []
    
    def get_applications_by_status(self, status: str) -> List[Dict]:
        """Get all applications with a specific status."""
        try:
            db = PostgresConfig.get_session()
            apps = db.query(Application).filter(
                Application.status == status
            ).order_by(desc(Application.created_at)).all()
            
            result = [self._convert_to_dict(app) for app in apps]
            db.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting applications by status {status}: {e}")
            db.close()
            return []
    
    # ==================== UPDATE OPERATIONS ====================
    
    def update_application(self, app_id: str, user_id: str, updates: Dict) -> Optional[Dict]:
        """Update application details."""
        try:
            db = PostgresConfig.get_session()
            
            app = db.query(Application).filter(Application.id == app_id).first()
            if not app:
                logger.warning(f"Application {app_id} not found")
                db.close()
                return None
            
            # Convert application_owner username to user ID if needed
            if 'application_owner' in updates:
                owner_value = updates['application_owner']
                # Check if it's already a UUID (user ID) or a username
                if owner_value and '-' not in owner_value:
                    # It's likely a username, convert to user ID
                    from app.database.models import User
                    owner_user = db.query(User).filter(User.username == owner_value).first()
                    if owner_user:
                        updates['application_owner'] = owner_user.id
                    else:
                        logger.warning(f"User '{owner_value}' not found, removing application_owner from updates")
                        # Remove application_owner from updates to keep the original value
                        del updates['application_owner']
            
            # Verify ownership or admin rights (implement your auth logic)
            
            for key, value in updates.items():
                if hasattr(app, key) and key not in ['id', 'created_at']:
                    setattr(app, key, value)
            
            app.updated_by = user_id
            app.updated_at = datetime.now()
            db.commit()
            
            result = self._convert_to_dict(app)
            db.close()
            
            logger.info(f"✅ Updated application: {app_id}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error updating application {app_id}: {e}")
            db.close()
            raise
    
    def toggle_status(self, app_id: str, user_id: str) -> Optional[Dict]:
        """Toggle application status between active and inactive."""
        try:
            db = PostgresConfig.get_session()
            
            app = db.query(Application).filter(Application.id == app_id).first()
            if not app:
                logger.warning(f"Application {app_id} not found")
                db.close()
                return None
            
            # Toggle status
            if app.status == ApplicationStatus.ACTIVE.value:
                app.status = ApplicationStatus.INACTIVE.value
            else:
                app.status = ApplicationStatus.ACTIVE.value
            
            app.updated_by = user_id
            app.updated_at = datetime.now()
            
            db.commit()
            
            result = self._convert_to_dict(app)
            db.close()
            
            logger.info(f"✅ Toggled status for application: {app_id} to {app.status}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error toggling status for application {app_id}: {e}")
            db.close()
            raise
    
    # ==================== DELETE OPERATIONS ====================
    
    def delete_application(self, app_id: str) -> bool:
        """Delete an application."""
        try:
            db = PostgresConfig.get_session()
            
            app = db.query(Application).filter(Application.id == app_id).first()
            if not app:
                logger.warning(f"Application {app_id} not found")
                db.close()
                return False
            
            db.delete(app)
            db.commit()
            
            logger.info(f"✅ Deleted application: {app_id}")
            db.close()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error deleting application {app_id}: {e}")
            db.close()
            return False
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> ApplicationStats:
        """Get application statistics."""
        try:
            db = PostgresConfig.get_session()
            
            total = db.query(Application).count()
            active = db.query(Application).filter(
                Application.status == ApplicationStatus.ACTIVE.value
            ).count()
            inactive = db.query(Application).filter(
                Application.status == ApplicationStatus.INACTIVE.value
            ).count()
            pending = db.query(Application).filter(
                Application.status == ApplicationStatus.PENDING.value
            ).count()
            suspended = db.query(Application).filter(
                Application.status == ApplicationStatus.SUSPENDED.value
            ).count()
            
            # Applications by owner
            from sqlalchemy import func
            owner_stats = db.query(
                Application.application_owner,
                func.count(Application.id).label('count')
            ).group_by(Application.application_owner).all()
            
            applications_by_owner = {owner: count for owner, count in owner_stats}
            
            # Applications by cluster
            cluster_stats = db.query(
                Application.gke_cluster_name,
                func.count(Application.id).label('count')
            ).group_by(Application.gke_cluster_name).all()
            
            applications_by_cluster = {cluster: count for cluster, count in cluster_stats if cluster}
            
            # Recent applications (last 7 days)
            from datetime import timedelta
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent = db.query(Application).filter(
                Application.created_at >= seven_days_ago
            ).count()
            
            db.close()
            
            return ApplicationStats(
                total_applications=total,
                active_applications=active,
                inactive_applications=inactive,
                pending_applications=pending,
                suspended_applications=suspended,
                applications_by_owner=applications_by_owner,
                applications_by_cluster=applications_by_cluster,
                recent_applications=recent
            )
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            db.close()
            return ApplicationStats(
                total_applications=0,
                active_applications=0,
                inactive_applications=0,
                pending_applications=0,
                suspended_applications=0,
                applications_by_owner={},
                applications_by_cluster={},
                recent_applications=0
            )
    
    # ==================== HELPER METHODS ====================
    
    @staticmethod
    def _convert_to_dict(app: Application) -> Dict:
        """Convert SQLAlchemy model to dictionary."""
        if not app:
            return None
        
        return {
            "id": app.id,
            "application_name": app.application_name,
            "description": app.description,
            "application_owner": app.application_owner,
            "status": app.status.value if hasattr(app.status, 'value') else app.status,
            "cloud_provider": app.cloud_provider,
            "gcp_project_id": app.gcp_project_id,
            "aws_account_id": app.aws_account_id,
            "azure_subscription_id": app.azure_subscription_id,
            "github_repo": app.github_repo,
            "gke_cluster_name": app.gke_cluster_name,
            "argocd_app_name": app.argocd_app_name,
            "grafana_dashboard": app.grafana_dashboard,
            "namespace": app.namespace,
            "tags": app.tags or [],
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "updated_at": app.updated_at.isoformat() if app.updated_at else None,
        }


# Global database instance
application_db = ApplicationDatabase()
