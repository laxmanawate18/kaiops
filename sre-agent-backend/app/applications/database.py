"""
Application Database with MongoDB

Persistent storage for SRE-enabled application registrations.
"""
from typing import Dict, Optional, List
from datetime import datetime
from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING
from ..database import get_db, Collections
from .models import ApplicationStatus, ApplicationStats
import uuid
import logging

logger = logging.getLogger(__name__)


class ApplicationDatabase:
    """MongoDB-backed database for managing SRE-enabled applications."""
    
    def __init__(self):
        self.db = get_db()
        self.collection: Optional[Collection] = None
        
        if self.db is None:
            raise RuntimeError(
                "Failed to connect to Azure Cosmos DB. "
                "Please verify MONGODB_URI environment variable is set correctly."
            )
        
        self.collection = self.db[Collections.APPLICATIONS]
        self._create_indexes()
        self._ensure_demo_applications()
    
    def _create_indexes(self):
        """Create MongoDB indexes for efficient queries."""
        if self.collection is None:
            return
        
        try:
            # Index on application_name_lower (non-unique - Azure Cosmos DB limitation)
            # Uniqueness enforced at application level
            self.collection.create_index(
                [("application_name_lower", ASCENDING)],
                name="application_name_index"
            )
            
            # Index on status for filtering
            self.collection.create_index(
                [("status", ASCENDING)],
                name="status_index"
            )
            
            # Index on owner for user queries
            self.collection.create_index(
                [("application_owner", ASCENDING)],
                name="owner_index"
            )
            
            # Index on cluster for filtering
            self.collection.create_index(
                [("gke_cluster_name", ASCENDING)],
                name="cluster_index"
            )
            
            # Index on created_at for sorting
            self.collection.create_index(
                [("created_at", DESCENDING)],
                name="created_at_index"
            )
            
            logger.info("✅ Application database indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning (may already exist): {e}")
    
    def _ensure_demo_applications(self):
        """Ensure demo applications exist in MongoDB."""
        if self.collection is None:
            return
        
        try:
            # Check if demo apps already exist
            count = self.collection.count_documents({})
            if count > 0:
                logger.info(f"📊 Found {count} existing applications in MongoDB")
                return
            
            logger.info("Creating demo applications in MongoDB...")
            
            demo_apps = [
                {
                    "application_name": "Payment Gateway",
                    "github_repo": "myorg/payment-gateway",
                    "gcp_project_id": "prod-payment-gw-001",
                    "argocd_app_name": "payment-gateway-prod",
                    "grafana_dashboard": "Payment Gateway Dashboard",
                    "gke_cluster_name": "prod-cluster-us-central1",
                    "namespace": "payment-prod",
                    "application_owner": "teamlead",
                    "status": ApplicationStatus.ACTIVE.value,
                    "description": "Core payment processing service",
                    "tags": ["payment", "critical", "prod"]
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
                    "tags": ["auth", "user", "prod"]
                },
                {
                    "application_name": "Analytics Engine",
                    "github_repo": "myorg/analytics-engine",
                    "gcp_project_id": "staging-analytics-003",
                    "argocd_app_name": "analytics-engine-staging",
                    "grafana_dashboard": "Analytics Performance",
                    "gke_cluster_name": "staging-cluster-us-west1",
                    "namespace": "analytics-staging",
                    "application_owner": "teamlead",
                    "status": ApplicationStatus.INACTIVE.value,
                    "description": "Real-time analytics processing pipeline",
                    "tags": ["analytics", "staging", "data"]
                }
            ]
            
            for app_data in demo_apps:
                app_id = str(uuid.uuid4())
                created_at = datetime.utcnow()
                
                application = {
                    "id": app_id,
                    **app_data,
                    "application_name_lower": app_data["application_name"].lower(),
                    "created_by": "system",
                    "updated_by": None,
                    "created_at": created_at,
                    "updated_at": created_at
                }
                
                self.collection.insert_one(application)
            
            logger.info(f"✅ Created {len(demo_apps)} demo applications in MongoDB")
            
        except Exception as e:
            logger.error(f"❌ Error creating demo applications: {e}")

    
    def create_application(self, user_id: str, app_data: Dict) -> Dict:
        """Create a new application."""
        app_name_lower = app_data["application_name"].lower()
        
        # Check if application name already exists
        existing = self.collection.find_one({"application_name_lower": app_name_lower})
        if existing:
            raise ValueError(f"Application '{app_data['application_name']}' already exists")
        
        app_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        application = {
            "id": app_id,
            **app_data,
            "application_name_lower": app_name_lower,
            "created_by": user_id,
            "updated_by": None,
            "created_at": created_at,
            "updated_at": created_at
        }
        
        self.collection.insert_one(application)
        logger.info(f"Created application: {app_data['application_name']}")
        
        # Convert datetime to ISO string for API response
        application["created_at"] = created_at.isoformat()
        application["updated_at"] = created_at.isoformat()
        application.pop("_id", None)
        
        return application
    
    def get_application(self, app_id: str) -> Optional[Dict]:
        """Get application by ID."""
        app = self.collection.find_one({"id": app_id})
        if app:
            app.pop("_id", None)
            if isinstance(app.get("created_at"), datetime):
                app["created_at"] = app["created_at"].isoformat()
            if isinstance(app.get("updated_at"), datetime):
                app["updated_at"] = app["updated_at"].isoformat()
        return app
    
    def get_application_by_name(self, app_name: str) -> Optional[Dict]:
        """Get application by name (case-insensitive)."""
        app = self.collection.find_one({"application_name_lower": app_name.lower()})
        if app:
            app.pop("_id", None)
            if isinstance(app.get("created_at"), datetime):
                app["created_at"] = app["created_at"].isoformat()
            if isinstance(app.get("updated_at"), datetime):
                app["updated_at"] = app["updated_at"].isoformat()
        return app
    
    def get_all_applications(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all applications with pagination (Azure Cosmos DB compatible)."""
        # Fetch all documents without sort (Azure Cosmos DB doesn't support sort on unindexed fields)
        cursor = self.collection.find()
        apps = []
        all_apps = []
        
        # First, collect all apps and convert datetimes
        for app in cursor:
            app.pop("_id", None)
            if isinstance(app.get("created_at"), datetime):
                app["created_at"] = app["created_at"].isoformat()
            if isinstance(app.get("updated_at"), datetime):
                app["updated_at"] = app["updated_at"].isoformat()
            all_apps.append(app)
        
        # Sort in Python (descending by created_at)
        all_apps.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply pagination
        for idx, app in enumerate(all_apps):
            if idx < skip:
                continue
            if len(apps) >= limit:
                break
            apps.append(app)
        
        return apps
    
    def list_applications(
        self, 
        status: Optional[ApplicationStatus] = None,
        owner: Optional[str] = None,
        cluster: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Dict], int]:
        """
        Get applications with filtering and pagination (Azure Cosmos DB compatible).
        Returns (applications, total_count) tuple.
        """
        # Build filter query
        query = {}
        if status:
            query["status"] = status.value
        if owner:
            query["application_owner"] = owner
        if cluster:
            query["gke_cluster_name"] = cluster
        
        # Get total count for pagination
        total_count = self.collection.count_documents(query)
        
        # Get filtered applications - fetch all and handle sorting/pagination in Python
        cursor = self.collection.find(query)
        all_apps = []
        
        for app in cursor:
            app.pop("_id", None)
            if isinstance(app.get("created_at"), datetime):
                app["created_at"] = app["created_at"].isoformat()
            if isinstance(app.get("updated_at"), datetime):
                app["updated_at"] = app["updated_at"].isoformat()
            all_apps.append(app)
        
        # Sort in Python (descending by created_at)
        all_apps.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply pagination
        apps = []
        for idx, app in enumerate(all_apps):
            if idx < skip:
                continue
            if len(apps) >= limit:
                break
            apps.append(app)
        
        return apps, total_count
    
    def update_application(self, app_id: str, user_id: str, updates: Dict) -> Optional[Dict]:
        """Update application details."""
        # Check if name is being updated and if it conflicts
        if "application_name" in updates:
            new_name_lower = updates["application_name"].lower()
            existing = self.collection.find_one({
                "application_name_lower": new_name_lower,
                "id": {"$ne": app_id}
            })
            if existing:
                raise ValueError(f"Application '{updates['application_name']}' already exists")
            
            updates["application_name_lower"] = new_name_lower
        
        update_doc = {
            **updates,
            "updated_by": user_id,
            "updated_at": datetime.utcnow()
        }
        
        result = self.collection.find_one_and_update(
            {"id": app_id},
            {"$set": update_doc},
            return_document=True
        )
        
        if result:
            result.pop("_id", None)
            if isinstance(result.get("created_at"), datetime):
                result["created_at"] = result["created_at"].isoformat()
            if isinstance(result.get("updated_at"), datetime):
                result["updated_at"] = result["updated_at"].isoformat()
        
        return result
    
    def delete_application(self, app_id: str) -> bool:
        """Delete an application."""
        result = self.collection.delete_one({"id": app_id})
        return result.deleted_count > 0
    
    def search_applications(self, query: str, limit: int = 20) -> List[Dict]:
        """Search applications by name or description."""
        pattern = {"$regex": query, "$options": "i"}
        cursor = self.collection.find({
            "$or": [
                {"application_name": pattern},
                {"description": pattern},
                {"tags": pattern}
            ]
        }).limit(limit)
        apps = []
        for app in cursor:
            app.pop("_id", None)
            if isinstance(app.get("created_at"), datetime):
                app["created_at"] = app["created_at"].isoformat()
            if isinstance(app.get("updated_at"), datetime):
                app["updated_at"] = app["updated_at"].isoformat()
            apps.append(app)
        return apps
    
    def get_applications_by_owner(self, owner: str) -> List[Dict]:
        """Get all applications owned by a user."""
        cursor = self.collection.find({"application_owner": owner})
        apps = []
        for app in cursor:
            app.pop("_id", None)
            if isinstance(app.get("created_at"), datetime):
                app["created_at"] = app["created_at"].isoformat()
            if isinstance(app.get("updated_at"), datetime):
                app["updated_at"] = app["updated_at"].isoformat()
            apps.append(app)
        return apps
    
    def get_applications_by_cluster(self, cluster: str) -> List[Dict]:
        """Get all applications in a specific cluster."""
        cursor = self.collection.find({"gke_cluster_name": cluster})
        apps = []
        for app in cursor:
            app.pop("_id", None)
            if isinstance(app.get("created_at"), datetime):
                app["created_at"] = app["created_at"].isoformat()
            if isinstance(app.get("updated_at"), datetime):
                app["updated_at"] = app["updated_at"].isoformat()
            apps.append(app)
        return apps
    
    def get_applications_by_status(self, status: ApplicationStatus) -> List[Dict]:
        """Get all applications with a specific status."""
        status_value = status.value if hasattr(status, 'value') else status
        
        cursor = self.collection.find({"status": status_value})
        apps = []
        for app in cursor:
            app.pop("_id", None)
            if isinstance(app.get("created_at"), datetime):
                app["created_at"] = app["created_at"].isoformat()
            if isinstance(app.get("updated_at"), datetime):
                app["updated_at"] = app["updated_at"].isoformat()
            apps.append(app)
        return apps
    
    def toggle_status(self, app_id: str, user_id: str) -> Optional[Dict]:
        """Toggle application status between ACTIVE and INACTIVE."""
        app = self.get_application(app_id)
        if not app:
            return None
        
        current_status = app.get("status")
        new_status = (
            ApplicationStatus.INACTIVE.value
            if current_status == ApplicationStatus.ACTIVE.value
            else ApplicationStatus.ACTIVE.value
        )
        
        return self.update_application(app_id, user_id, {"status": new_status})
    
    def get_statistics(self) -> ApplicationStats:
        """Get application statistics."""
        from datetime import timezone, timedelta
        from collections import Counter
        
        # MongoDB implementation
        total = self.collection.count_documents({})
        active = self.collection.count_documents({"status": ApplicationStatus.ACTIVE.value})
        inactive = self.collection.count_documents({"status": ApplicationStatus.INACTIVE.value})
        pending = self.collection.count_documents({"status": ApplicationStatus.PENDING.value})
        suspended = self.collection.count_documents({"status": ApplicationStatus.SUSPENDED.value})
        
        # Get applications by owner
        all_apps = list(self.collection.find({}, {"owner": 1}))
        owners = [app.get("owner", "Unknown") for app in all_apps]
        applications_by_owner = dict(Counter(owners))
        
        # Get applications by cluster
        all_apps_cluster = list(self.collection.find({}, {"cluster": 1}))
        clusters = [app.get("cluster", "Unknown") for app in all_apps_cluster]
        applications_by_cluster = dict(Counter(clusters))
        
        # Get recent applications (last 7 days)
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        recent_applications = self.collection.count_documents({
            "created_at": {"$gte": seven_days_ago}
        })
        
        return ApplicationStats(
            total_applications=total,
            active_applications=active,
            inactive_applications=inactive,
            pending_applications=pending,
            suspended_applications=suspended,
            applications_by_owner=applications_by_owner,
            applications_by_cluster=applications_by_cluster,
            recent_applications=recent_applications
        )


# Global database instance
application_db = ApplicationDatabase()
