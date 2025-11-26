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
        
        if self.db is not None:
            self.collection = self.db[Collections.APPLICATIONS]
            self._create_indexes()
            self._ensure_demo_applications()
        else:
            logger.warning("⚠️ MongoDB not available, using in-memory fallback")
            self.applications: Dict[str, Dict] = {}
            self.app_name_to_id: Dict[str, str] = {}
            self._create_demo_applications_memory()
    
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
    
    def _create_demo_applications_memory(self):
        """Fallback: Create demo applications in memory."""
        try:
            demo_apps = [
                {
                    "application_name": "Payment Gateway",
                    "github_repo": "myorg/payment-gateway",
                    "gcp_project_id": "prod-payment-gw-001",
                    "argocd_app_name": "payment-gateway-prod",
                    "grafana_dashboard": "Payment Gateway Dashboard",
                    "gke_cluster_name": "prod-cluster-us-central1",
                    "application_owner": "teamlead",
                    "status": ApplicationStatus.ACTIVE,
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
                    "application_owner": "admin",
                    "status": ApplicationStatus.ACTIVE,
                    "description": "User authentication and profile management",
                    "tags": ["auth", "user", "prod"]
                }
            ]
            
            for app_data in demo_apps:
                app_id = str(uuid.uuid4())
                created_at = datetime.utcnow().isoformat()
                
                application = {
                    "id": app_id,
                    **app_data,
                    "created_by": "system",
                    "updated_by": None,
                    "created_at": created_at,
                    "updated_at": created_at
                }
                
                self.applications[app_id] = application
                self.app_name_to_id[app_data["application_name"].lower()] = app_id
                
        except Exception as e:
            logger.error(f"Error creating in-memory demo apps: {e}")
    
    def create_application(self, user_id: str, app_data: Dict) -> Dict:
        """Create a new application."""
        app_name_lower = app_data["application_name"].lower()
        
        if self.collection is not None:
            # MongoDB path
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
            application.pop("_id", None)  # Remove MongoDB ID
            
            return application
        else:
            # In-memory fallback
            if app_name_lower in self.app_name_to_id:
                raise ValueError(f"Application '{app_data['application_name']}' already exists")
            
            app_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()
            
            application = {
                "id": app_id,
                **app_data,
                "created_by": user_id,
                "updated_by": None,
                "created_at": created_at,
                "updated_at": created_at
            }
            
            self.applications[app_id] = application
            self.app_name_to_id[app_name_lower] = app_id
            
            return application
    
    def get_application(self, app_id: str) -> Optional[Dict]:
        """Get application by ID."""
        if self.collection is not None:
            app = self.collection.find_one({"id": app_id})
            if app:
                app.pop("_id", None)
                if isinstance(app.get("created_at"), datetime):
                    app["created_at"] = app["created_at"].isoformat()
                if isinstance(app.get("updated_at"), datetime):
                    app["updated_at"] = app["updated_at"].isoformat()
            return app
        else:
            return self.applications.get(app_id)
    
    def get_all_applications(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all applications with pagination."""
        if self.collection is not None:
            cursor = self.collection.find().skip(skip).limit(limit).sort("created_at", DESCENDING)
            apps = []
            for app in cursor:
                app.pop("_id", None)
                if isinstance(app.get("created_at"), datetime):
                    app["created_at"] = app["created_at"].isoformat()
                if isinstance(app.get("updated_at"), datetime):
                    app["updated_at"] = app["updated_at"].isoformat()
                apps.append(app)
            return apps
        else:
            apps = list(self.applications.values())
            return apps[skip:skip + limit]
    
    def update_application(self, app_id: str, user_id: str, updates: Dict) -> Optional[Dict]:
        """Update application details."""
        if self.collection is not None:
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
        else:
            app = self.applications.get(app_id)
            if not app:
                return None
            
            # Check name conflict in memory
            if "application_name" in updates:
                new_name_lower = updates["application_name"].lower()
                existing_id = self.app_name_to_id.get(new_name_lower)
                if existing_id and existing_id != app_id:
                    raise ValueError(f"Application '{updates['application_name']}' already exists")
                
                # Update name mapping
                old_name_lower = app["application_name"].lower()
                if old_name_lower in self.app_name_to_id:
                    del self.app_name_to_id[old_name_lower]
                self.app_name_to_id[new_name_lower] = app_id
            
            app.update(updates)
            app["updated_by"] = user_id
            app["updated_at"] = datetime.utcnow().isoformat()
            
            return app
    
    def delete_application(self, app_id: str) -> bool:
        """Delete an application."""
        if self.collection is not None:
            result = self.collection.delete_one({"id": app_id})
            return result.deleted_count > 0
        else:
            if app_id in self.applications:
                app = self.applications[app_id]
                app_name_lower = app["application_name"].lower()
                del self.applications[app_id]
                if app_name_lower in self.app_name_to_id:
                    del self.app_name_to_id[app_name_lower]
                return True
            return False
    
    def search_applications(self, query: str) -> List[Dict]:
        """Search applications by name or description."""
        if self.collection is not None:
            pattern = {"$regex": query, "$options": "i"}
            cursor = self.collection.find({
                "$or": [
                    {"application_name": pattern},
                    {"description": pattern},
                    {"tags": pattern}
                ]
            })
            apps = []
            for app in cursor:
                app.pop("_id", None)
                if isinstance(app.get("created_at"), datetime):
                    app["created_at"] = app["created_at"].isoformat()
                if isinstance(app.get("updated_at"), datetime):
                    app["updated_at"] = app["updated_at"].isoformat()
                apps.append(app)
            return apps
        else:
            query_lower = query.lower()
            return [
                app for app in self.applications.values()
                if query_lower in app["application_name"].lower()
                or query_lower in app.get("description", "").lower()
                or any(query_lower in tag.lower() for tag in app.get("tags", []))
            ]
    
    def get_applications_by_owner(self, owner: str) -> List[Dict]:
        """Get all applications owned by a user."""
        if self.collection is not None:
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
        else:
            return [app for app in self.applications.values() if app["application_owner"] == owner]
    
    def get_applications_by_cluster(self, cluster: str) -> List[Dict]:
        """Get all applications in a specific cluster."""
        if self.collection is not None:
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
        else:
            return [app for app in self.applications.values() if app["gke_cluster_name"] == cluster]
    
    def get_applications_by_status(self, status: ApplicationStatus) -> List[Dict]:
        """Get all applications with a specific status."""
        status_value = status.value if hasattr(status, 'value') else status
        
        if self.collection is not None:
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
        else:
            return [app for app in self.applications.values() if app["status"] == status_value]
    
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
        if self.collection is not None:
            total = self.collection.count_documents({})
            active = self.collection.count_documents({"status": ApplicationStatus.ACTIVE.value})
            inactive = self.collection.count_documents({"status": ApplicationStatus.INACTIVE.value})
            pending = self.collection.count_documents({"status": ApplicationStatus.PENDING.value})
            suspended = self.collection.count_documents({"status": ApplicationStatus.SUSPENDED.value})
            
            # Get applications by owner
            owner_pipeline = [
                {"$group": {"_id": "$application_owner", "count": {"$sum": 1}}}
            ]
            owner_result = list(self.collection.aggregate(owner_pipeline))
            applications_by_owner = {item["_id"]: item["count"] for item in owner_result}
            
            # Get applications by cluster
            cluster_pipeline = [
                {"$group": {"_id": "$gke_cluster_name", "count": {"$sum": 1}}}
            ]
            cluster_result = list(self.collection.aggregate(cluster_pipeline))
            applications_by_cluster = {item["_id"]: item["count"] for item in cluster_result if item["_id"]}
            
            # Get recent applications (last 7 days)
            from datetime import datetime, timedelta
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent = self.collection.count_documents({"created_at": {"$gte": seven_days_ago}})
        else:
            total = len(self.applications)
            active = sum(1 for app in self.applications.values() if app["status"] == ApplicationStatus.ACTIVE.value)
            inactive = sum(1 for app in self.applications.values() if app["status"] == ApplicationStatus.INACTIVE.value)
            pending = sum(1 for app in self.applications.values() if app["status"] == ApplicationStatus.PENDING.value)
            suspended = sum(1 for app in self.applications.values() if app["status"] == ApplicationStatus.SUSPENDED.value)
            
            applications_by_owner = {}
            applications_by_cluster = {}
            recent = 0
        
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


# Global database instance
application_db = ApplicationDatabase()
