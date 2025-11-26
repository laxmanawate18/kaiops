"""
Feedback Database with MongoDB

Persistent storage for AI feedback and training datasets.
"""
from typing import Dict, Optional, List
from datetime import datetime, timezone
from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING
from ..database import get_db, Collections
from .models import (
    FeedbackType, FeedbackStatus, FeedbackCategory, DatasetType,
    FeedbackResponse, FeedbackStats, DatasetEntry, DatasetStats
)
import uuid
import logging

logger = logging.getLogger(__name__)


class FeedbackDatabase:
    """
    MongoDB-backed feedback database for AI response improvement.
    """
    
    def __init__(self):
        self.db = get_db()
        self.feedback_collection: Optional[Collection] = None
        self.training_dataset_collection: Optional[Collection] = None
        self.evaluation_dataset_collection: Optional[Collection] = None
        
        if self.db is not None:
            self.feedback_collection = self.db[Collections.FEEDBACK]
            self.training_dataset_collection = self.db[Collections.TRAINING_DATASET]
            self.evaluation_dataset_collection = self.db[Collections.EVALUATION_DATASET]
            self._create_indexes()
            self._create_sample_data()
        else:
            logger.warning("⚠️ MongoDB not available, using in-memory fallback")
            self.feedback: Dict[str, Dict] = {}
            self.training_dataset: Dict[str, Dict] = {}
            self.evaluation_dataset: Dict[str, Dict] = {}
            self._create_sample_data()
    
    def _create_indexes(self):
        """Create MongoDB indexes for efficient queries."""
        if self.feedback_collection is None:
            return
        
        try:
            # Feedback indexes - Note: unique constraints enforced at application level
            self.feedback_collection.create_index(
                [("id", ASCENDING)],
                name="feedback_id_index"
            )
            self.feedback_collection.create_index(
                [("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="user_feedback_index"
            )
            self.feedback_collection.create_index(
                [("status", ASCENDING), ("created_at", ASCENDING)],
                name="status_index"
            )
            self.feedback_collection.create_index(
                [("feedback_type", ASCENDING)],
                name="feedback_type_index"
            )
            self.feedback_collection.create_index(
                [("tags", ASCENDING)],
                name="tags_index"
            )
            
            # Training dataset indexes
            if self.training_dataset_collection is not None:
                self.training_dataset_collection.create_index(
                    [("id", ASCENDING)],
                    name="training_id_index"
                )
                self.training_dataset_collection.create_index(
                    [("feedback_id", ASCENDING)],
                    name="training_feedback_ref"
                )
                self.training_dataset_collection.create_index(
                    [("created_at", DESCENDING)],
                    name="training_created_index"
                )
            
            # Evaluation dataset indexes
            if self.evaluation_dataset_collection is not None:
                self.evaluation_dataset_collection.create_index(
                    [("id", ASCENDING)],
                    name="evaluation_id_index"
                )
                self.evaluation_dataset_collection.create_index(
                    [("feedback_id", ASCENDING)],
                    name="evaluation_feedback_ref"
                )
                self.evaluation_dataset_collection.create_index(
                    [("created_at", DESCENDING)],
                    name="evaluation_created_index"
                )
            
            logger.info("✅ Feedback database indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    def _create_sample_data(self):
        """Create some sample feedback for demonstration."""
        try:
            # Check if sample data already exists
            if self.feedback_collection is not None:
                if self.feedback_collection.count_documents({}) > 0:
                    return
            elif self.feedback:
                return
            
            # Sample feedback 1 - Thumbs Down
            sample_feedback_1 = {
                "id": str(uuid.uuid4()),
                "conversation_id": "conv_001",
                "message_id": "msg_001",
                "user_id": "user_001",
                "user_message": "What's the weather like today?",
                "ai_response": "I don't have access to current weather data.",
                "feedback_type": FeedbackType.THUMBS_DOWN,
                "rating": None,
                "tags": [FeedbackCategory.HELPFULNESS, FeedbackCategory.COMPLETENESS],
                "comment": "The AI should provide more helpful suggestions like checking weather apps or websites.",
                "suggested_response": "I don't have access to current weather data, but you can check weather.com or your local weather app for accurate forecasts.",
                "status": FeedbackStatus.PENDING,
                "reviewer_id": None,
                "reviewer_comment": None,
                "dataset_type": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "reviewed_at": None
            }
            
            # Sample feedback 2 - Thumbs Up
            sample_feedback_2 = {
                "id": str(uuid.uuid4()),
                "conversation_id": "conv_002",
                "message_id": "msg_002",
                "user_id": "user_002",
                "user_message": "How do I restart a service in Linux?",
                "ai_response": "You can restart a service in Linux using: sudo systemctl restart service-name. Replace 'service-name' with your actual service name.",
                "feedback_type": FeedbackType.THUMBS_UP,
                "rating": 5,
                "tags": [FeedbackCategory.ACCURACY, FeedbackCategory.HELPFULNESS],
                "comment": "Perfect answer, exactly what I needed!",
                "suggested_response": None,
                "status": FeedbackStatus.APPROVED,
                "reviewer_id": "admin_001",
                "reviewer_comment": "Good positive feedback, helpful for training.",
                "dataset_type": DatasetType.TRAINING,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "reviewed_at": datetime.now(timezone.utc)
            }
            
            if self.feedback_collection is not None:
                self.feedback_collection.insert_one(sample_feedback_1)
                self.feedback_collection.insert_one(sample_feedback_2)
            else:
                # In-memory fallback - convert datetime to ISO string
                for sample in [sample_feedback_1, sample_feedback_2]:
                    sample["created_at"] = sample["created_at"].isoformat()
                    sample["updated_at"] = sample["updated_at"].isoformat()
                    if sample["reviewed_at"]:
                        sample["reviewed_at"] = sample["reviewed_at"].isoformat()
                    self.feedback[sample["id"]] = sample
            
            logger.info("Sample feedback data created")
        except Exception as e:
            logger.error(f"Error creating sample feedback: {e}")
    
    # ==================== Feedback Management ====================
    
    def create_feedback(self, user_id: str, feedback_data: Dict) -> Dict:
        """Create new feedback entry."""
        feedback = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "status": FeedbackStatus.PENDING,
            "reviewer_id": None,
            "reviewer_comment": None,
            "dataset_type": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "reviewed_at": None,
            **feedback_data
        }
        
        if self.feedback_collection is not None:
            self.feedback_collection.insert_one(feedback.copy())
            # Convert datetime to ISO string for API response
            feedback["created_at"] = feedback["created_at"].isoformat()
            feedback["updated_at"] = feedback["updated_at"].isoformat()
        else:
            feedback["created_at"] = feedback["created_at"].isoformat()
            feedback["updated_at"] = feedback["updated_at"].isoformat()
            self.feedback[feedback["id"]] = feedback
        
        return feedback
    
    def get_feedback(self, feedback_id: str) -> Optional[Dict]:
        """Get feedback by ID."""
        if self.feedback_collection is not None:
            feedback = self.feedback_collection.find_one({"id": feedback_id})
            if feedback:
                feedback.pop("_id", None)
                self._convert_dates_to_iso(feedback)
            return feedback
        else:
            return self.feedback.get(feedback_id)
    
    def get_user_feedback(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get feedback by user (Azure Cosmos DB compatible)."""
        if self.feedback_collection is not None:
            cursor = self.feedback_collection.find(
                {"user_id": user_id}
            )
            
            feedbacks = []
            all_feedbacks = []
            
            for fb in cursor:
                fb.pop("_id", None)
                self._convert_dates_to_iso(fb)
                all_feedbacks.append(fb)
            
            # Sort in Python (descending by created_at)
            all_feedbacks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            # Apply limit
            for fb in all_feedbacks:
                if len(feedbacks) >= limit:
                    break
                feedbacks.append(fb)
            
            return feedbacks
        else:
            user_feedback = [
                fb for fb in self.feedback.values()
                if fb["user_id"] == user_id
            ]
            user_feedback.sort(key=lambda x: x["created_at"], reverse=True)
            return user_feedback[:limit]
    
    def get_pending_feedback(self, limit: int = 100) -> List[Dict]:
        """Get all pending feedback for review (Azure Cosmos DB compatible)."""
        if self.feedback_collection is not None:
            cursor = self.feedback_collection.find(
                {"status": FeedbackStatus.PENDING}
            )
            
            feedbacks = []
            all_feedbacks = []
            
            for fb in cursor:
                fb.pop("_id", None)
                self._convert_dates_to_iso(fb)
                all_feedbacks.append(fb)
            
            # Sort in Python (ascending by created_at - oldest first)
            all_feedbacks.sort(key=lambda x: x.get("created_at", ""))
            
            # Apply limit
            for fb in all_feedbacks:
                if len(feedbacks) >= limit:
                    break
                feedbacks.append(fb)
            
            return feedbacks
        else:
            pending = [
                fb for fb in self.feedback.values()
                if fb["status"] == FeedbackStatus.PENDING
            ]
            pending.sort(key=lambda x: x["created_at"])
            return pending[:limit]
    
    def get_feedback_by_status(self, status: FeedbackStatus, limit: int = 100) -> List[Dict]:
        """Get feedback by status (Azure Cosmos DB compatible)."""
        if self.feedback_collection is not None:
            cursor = self.feedback_collection.find(
                {"status": status}
            )
            
            feedbacks = []
            all_feedbacks = []
            
            for fb in cursor:
                fb.pop("_id", None)
                self._convert_dates_to_iso(fb)
                all_feedbacks.append(fb)
            
            # Sort in Python (descending by updated_at)
            all_feedbacks.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            
            # Apply limit
            for fb in all_feedbacks:
                if len(feedbacks) >= limit:
                    break
                feedbacks.append(fb)
            
            return feedbacks
        else:
            filtered = [
                fb for fb in self.feedback.values()
                if fb["status"] == status
            ]
            filtered.sort(key=lambda x: x["updated_at"], reverse=True)
            return filtered[:limit]
    
    def update_feedback(self, feedback_id: str, updates: Dict) -> Optional[Dict]:
        """Update feedback entry."""
        updates["updated_at"] = datetime.now(timezone.utc)
        
        if self.feedback_collection is not None:
            result = self.feedback_collection.find_one_and_update(
                {"id": feedback_id},
                {"$set": updates},
                return_document=True
            )
            if result:
                result.pop("_id", None)
                self._convert_dates_to_iso(result)
            return result
        else:
            if feedback_id not in self.feedback:
                return None
            
            feedback = self.feedback[feedback_id]
            for key, value in updates.items():
                if key != "id":
                    feedback[key] = value
            feedback["updated_at"] = datetime.now(timezone.utc).isoformat()
            return feedback
    
    def review_feedback(self, feedback_id: str, reviewer_id: str, review_data: Dict) -> Optional[Dict]:
        """Review and update feedback status.
        
        - APPROVED: Marks as approved, optionally adds to dataset
        - RECLASSIFIED: Updates tags, optionally adds to dataset with new classification
        - DENIED: Marks as denied, does NOT add to dataset
        """
        status = review_data["status"]
        
        updates = {
            "status": status,
            "reviewer_id": reviewer_id,
            "reviewer_comment": review_data.get("reviewer_comment"),
            "reviewed_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Update tags if provided (important for RECLASSIFIED)
        if "new_tags" in review_data and review_data["new_tags"]:
            updates["tags"] = review_data["new_tags"]
            logger.info(f"Updated tags for feedback {feedback_id}: {review_data['new_tags']}")
        
        # Store dataset type if specified
        if "add_to_dataset" in review_data and review_data["add_to_dataset"]:
            updates["dataset_type"] = review_data["add_to_dataset"]
        
        if self.feedback_collection is not None:
            result = self.feedback_collection.find_one_and_update(
                {"id": feedback_id},
                {"$set": updates},
                return_document=True
            )
            if result:
                result.pop("_id", None)
                self._convert_dates_to_iso(result)
                
                # Add to dataset for APPROVED or RECLASSIFIED status (if dataset choice provided)
                # Do NOT add to dataset for DENIED status
                should_add_to_dataset = (
                    status in [FeedbackStatus.APPROVED, FeedbackStatus.RECLASSIFIED] and
                    "add_to_dataset" in review_data and 
                    review_data["add_to_dataset"]
                )
                
                if should_add_to_dataset:
                    logger.info(f"Adding feedback {feedback_id} to dataset as {status}")
                    self._add_to_dataset(feedback_id, review_data["add_to_dataset"])
                elif status == FeedbackStatus.DENIED:
                    logger.info(f"Feedback {feedback_id} denied - NOT adding to dataset")
                    
            return result
        else:
            # In-memory fallback
            if feedback_id not in self.feedback:
                return None
            
            feedback = self.feedback[feedback_id]
            feedback.update({
                "status": status,
                "reviewer_id": reviewer_id,
                "reviewer_comment": review_data.get("reviewer_comment"),
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            
            if "new_tags" in review_data and review_data["new_tags"]:
                feedback["tags"] = review_data["new_tags"]
            
            # Add to dataset for APPROVED or RECLASSIFIED (if dataset choice provided)
            should_add_to_dataset = (
                status in [FeedbackStatus.APPROVED, FeedbackStatus.RECLASSIFIED] and
                "add_to_dataset" in review_data and 
                review_data["add_to_dataset"]
            )
            
            if should_add_to_dataset:
                feedback["dataset_type"] = review_data["add_to_dataset"]
                self._add_to_dataset(feedback_id, review_data["add_to_dataset"])
            
            return feedback
    
    def _add_to_dataset(self, feedback_id: str, dataset_type: DatasetType):
        """Add approved feedback to training/evaluation dataset."""
        feedback = self.get_feedback(feedback_id)
        if not feedback:
            logger.warning(f"Feedback {feedback_id} not found")
            return
        
        dataset_entry = {
            "id": str(uuid.uuid4()),
            "feedback_id": feedback_id,
            "user_message": feedback["user_message"],
            "ai_response": feedback["ai_response"],
            "expected_response": feedback.get("suggested_response"),
            "tags": feedback["tags"],
            "quality_score": self._calculate_quality_score(feedback),
            "created_at": datetime.now(timezone.utc),
            "created_by": feedback.get("reviewer_id")
        }
        
        # Add to appropriate collection(s) based on dataset_type
        if dataset_type == DatasetType.TRAINING:
            if self.training_dataset_collection is not None:
                self.training_dataset_collection.insert_one(dataset_entry.copy())
                logger.info(f"✅ Added feedback {feedback_id} to TRAINING dataset")
            else:
                entry = dataset_entry.copy()
                entry["created_at"] = entry["created_at"].isoformat()
                self.training_dataset[entry["id"]] = entry
        
        elif dataset_type == DatasetType.EVALUATION:
            if self.evaluation_dataset_collection is not None:
                self.evaluation_dataset_collection.insert_one(dataset_entry.copy())
                logger.info(f"✅ Added feedback {feedback_id} to EVALUATION dataset")
            else:
                entry = dataset_entry.copy()
                entry["created_at"] = entry["created_at"].isoformat()
                self.evaluation_dataset[entry["id"]] = entry
        
        elif dataset_type == DatasetType.BOTH:
            # Add to both collections
            if self.training_dataset_collection is not None:
                training_entry = dataset_entry.copy()
                training_entry["id"] = str(uuid.uuid4())
                self.training_dataset_collection.insert_one(training_entry)
                logger.info(f"✅ Added feedback {feedback_id} to TRAINING dataset")
            else:
                entry = dataset_entry.copy()
                entry["id"] = str(uuid.uuid4())
                entry["created_at"] = entry["created_at"].isoformat()
                self.training_dataset[entry["id"]] = entry
            
            if self.evaluation_dataset_collection is not None:
                eval_entry = dataset_entry.copy()
                eval_entry["id"] = str(uuid.uuid4())
                self.evaluation_dataset_collection.insert_one(eval_entry)
                logger.info(f"✅ Added feedback {feedback_id} to EVALUATION dataset")
            else:
                entry = dataset_entry.copy()
                entry["id"] = str(uuid.uuid4())
                entry["created_at"] = entry["created_at"].isoformat()
                self.evaluation_dataset[entry["id"]] = entry
    
    def _calculate_quality_score(self, feedback: Dict) -> float:
        """Calculate quality score based on feedback data."""
        score = 0.5  # Base score
        
        # Positive feedback gets higher score
        if feedback["feedback_type"] == FeedbackType.THUMBS_UP:
            score += 0.3
            if feedback.get("rating", 0) >= 4:
                score += 0.2
        
        # Constructive negative feedback is also valuable
        if feedback["feedback_type"] == FeedbackType.THUMBS_DOWN:
            if feedback.get("suggested_response"):
                score += 0.2
            if feedback.get("comment") and len(feedback["comment"]) > 20:
                score += 0.1
        
        return min(1.0, score)  # Cap at 1.0
    
    # ==================== Statistics ====================
    
    def get_feedback_stats(self) -> Dict:
        """Get comprehensive feedback statistics."""
        if self.feedback_collection is not None:
            pipeline = [
                {
                    "$facet": {
                        "status_counts": [
                            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                        ],
                        "type_counts": [
                            {"$group": {"_id": "$feedback_type", "count": {"$sum": 1}}}
                        ],
                        "ratings": [
                            {"$match": {"rating": {"$ne": None}}},
                            {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "all": {"$push": "$rating"}}}
                        ],
                        "total": [
                            {"$count": "count"}
                        ]
                    }
                }
            ]
            
            result = list(self.feedback_collection.aggregate(pipeline))
            if not result:
                return self._empty_stats()
            
            data = result[0]
            stats = {
                "total_feedback": data["total"][0]["count"] if data["total"] else 0,
                "pending_review": 0,
                "approved": 0,
                "denied": 0,
                "reclassified": 0,
                "thumbs_up_count": 0,
                "thumbs_down_count": 0,
                "ratings": [],
                "feedback_by_category": {},
                "feedback_by_user": {}
            }
            
            # Process status counts
            for item in data["status_counts"]:
                if item["_id"] == FeedbackStatus.PENDING:
                    stats["pending_review"] = item["count"]
                elif item["_id"] == FeedbackStatus.APPROVED:
                    stats["approved"] = item["count"]
                elif item["_id"] == FeedbackStatus.DENIED:
                    stats["denied"] = item["count"]
                elif item["_id"] == FeedbackStatus.RECLASSIFIED:
                    stats["reclassified"] = item["count"]
            
            # Process type counts
            for item in data["type_counts"]:
                if item["_id"] == FeedbackType.THUMBS_UP:
                    stats["thumbs_up_count"] = item["count"]
                elif item["_id"] == FeedbackType.THUMBS_DOWN:
                    stats["thumbs_down_count"] = item["count"]
            
            # Process ratings
            if data["ratings"]:
                stats["ratings"] = data["ratings"][0]["all"]
                stats["avg_rating"] = data["ratings"][0]["avg"]
            
            return stats
        else:
            return self._get_stats_in_memory()
    
    def _get_stats_in_memory(self) -> Dict:
        """Get stats from in-memory storage."""
        stats = {
            "total_feedback": len(self.feedback),
            "pending_review": 0,
            "approved": 0,
            "denied": 0,
            "reclassified": 0,
            "thumbs_up_count": 0,
            "thumbs_down_count": 0,
            "ratings": [],
            "feedback_by_category": {},
            "feedback_by_user": {}
        }
        
        for feedback in self.feedback.values():
            if feedback["status"] == FeedbackStatus.PENDING:
                stats["pending_review"] += 1
            elif feedback["status"] == FeedbackStatus.APPROVED:
                stats["approved"] += 1
            elif feedback["status"] == FeedbackStatus.DENIED:
                stats["denied"] += 1
            elif feedback["status"] == FeedbackStatus.RECLASSIFIED:
                stats["reclassified"] += 1
            
            if feedback["feedback_type"] == FeedbackType.THUMBS_UP:
                stats["thumbs_up_count"] += 1
            elif feedback["feedback_type"] == FeedbackType.THUMBS_DOWN:
                stats["thumbs_down_count"] += 1
            
            if feedback.get("rating"):
                stats["ratings"].append(feedback["rating"])
            
            for tag in feedback.get("tags", []):
                stats["feedback_by_category"][tag] = stats["feedback_by_category"].get(tag, 0) + 1
            
            user_id = feedback["user_id"]
            stats["feedback_by_user"][user_id] = stats["feedback_by_user"].get(user_id, 0) + 1
        
        if stats["ratings"]:
            stats["avg_rating"] = sum(stats["ratings"]) / len(stats["ratings"])
        
        return stats
    
    def _empty_stats(self) -> Dict:
        """Return empty stats structure."""
        return {
            "total_feedback": 0,
            "pending_review": 0,
            "approved": 0,
            "denied": 0,
            "reclassified": 0,
            "thumbs_up_count": 0,
            "thumbs_down_count": 0,
            "ratings": [],
            "feedback_by_category": {},
            "feedback_by_user": {}
        }
    
    def get_user_feedback_stats(self, user_id: str) -> Dict:
        """Get feedback statistics for a specific user."""
        if self.feedback_collection is not None:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {
                    "$facet": {
                        "status_counts": [
                            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                        ],
                        "total": [
                            {"$count": "count"}
                        ]
                    }
                }
            ]
            
            result = list(self.feedback_collection.aggregate(pipeline))
            if not result or not result[0]["total"]:
                return {
                    "total_feedback": 0,
                    "pending_review": 0,
                    "approved": 0,
                    "denied": 0
                }
            
            data = result[0]
            stats = {
                "total_feedback": data["total"][0]["count"],
                "pending_review": 0,
                "approved": 0,
                "denied": 0
            }
            
            # Process status counts
            for item in data["status_counts"]:
                if item["_id"] == FeedbackStatus.PENDING:
                    stats["pending_review"] = item["count"]
                elif item["_id"] == FeedbackStatus.APPROVED:
                    stats["approved"] = item["count"]
                elif item["_id"] == FeedbackStatus.DENIED:
                    stats["denied"] = item["count"]
            
            return stats
        else:
            # In-memory implementation
            user_feedback = [fb for fb in self.feedback.values() if fb["user_id"] == user_id]
            stats = {
                "total_feedback": len(user_feedback),
                "pending_review": 0,
                "approved": 0,
                "denied": 0
            }
            
            for feedback in user_feedback:
                if feedback["status"] == FeedbackStatus.PENDING:
                    stats["pending_review"] += 1
                elif feedback["status"] == FeedbackStatus.APPROVED:
                    stats["approved"] += 1
                elif feedback["status"] == FeedbackStatus.DENIED:
                    stats["denied"] += 1
            
            return stats
    
    # ==================== Dataset Management ====================
    
    def get_dataset_entries(self, dataset_type: Optional[DatasetType] = None, limit: int = 100) -> List[Dict]:
        """Get dataset entries from appropriate collection(s) (Azure Cosmos DB compatible)."""
        entries = []
        
        if self.training_dataset_collection is not None and self.evaluation_dataset_collection is not None:
            # MongoDB implementation - fetch all and sort in Python
            if dataset_type == DatasetType.TRAINING:
                cursor = self.training_dataset_collection.find()
                all_entries = []
                
                for entry in cursor:
                    entry.pop("_id", None)
                    if isinstance(entry.get("created_at"), datetime):
                        entry["created_at"] = entry["created_at"].isoformat()
                    entry["dataset_type"] = DatasetType.TRAINING
                    all_entries.append(entry)
                
                # Sort in Python
                all_entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                entries = all_entries[:limit]
            
            elif dataset_type == DatasetType.EVALUATION:
                cursor = self.evaluation_dataset_collection.find()
                all_entries = []
                
                for entry in cursor:
                    entry.pop("_id", None)
                    if isinstance(entry.get("created_at"), datetime):
                        entry["created_at"] = entry["created_at"].isoformat()
                    entry["dataset_type"] = DatasetType.EVALUATION
                    all_entries.append(entry)
                
                # Sort in Python
                all_entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                entries = all_entries[:limit]
            
            else:  # Get from both collections
                training_limit = limit // 2
                eval_limit = limit - training_limit
                
                # Get training entries
                training_cursor = self.training_dataset_collection.find()
                training_entries = []
                for entry in training_cursor:
                    entry.pop("_id", None)
                    if isinstance(entry.get("created_at"), datetime):
                        entry["created_at"] = entry["created_at"].isoformat()
                    entry["dataset_type"] = DatasetType.TRAINING
                    training_entries.append(entry)
                
                # Get evaluation entries
                eval_cursor = self.evaluation_dataset_collection.find()
                eval_entries = []
                for entry in eval_cursor:
                    entry.pop("_id", None)
                    if isinstance(entry.get("created_at"), datetime):
                        entry["created_at"] = entry["created_at"].isoformat()
                    entry["dataset_type"] = DatasetType.EVALUATION
                    eval_entries.append(entry)
                
                # Sort each in Python
                training_entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                eval_entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                
                # Combine and limit
                entries.extend(training_entries[:training_limit])
                entries.extend(eval_entries[:eval_limit])
                
                # Re-sort combined entries by created_at
                entries.sort(key=lambda x: x["created_at"], reverse=True)
        
        else:
            # In-memory fallback
            if dataset_type == DatasetType.TRAINING:
                entries = list(self.training_dataset.values())
            elif dataset_type == DatasetType.EVALUATION:
                entries = list(self.evaluation_dataset.values())
            else:
                entries = list(self.training_dataset.values()) + list(self.evaluation_dataset.values())
            
            entries.sort(key=lambda x: x["created_at"], reverse=True)
            entries = entries[:limit]
        
        return entries
    
    def get_dataset_stats(self) -> Dict:
        """Get dataset statistics from separate collections."""
        stats = {
            "training_count": 0,
            "evaluation_count": 0,
            "total_entries": 0,
            "categories_breakdown": {},
            "quality_distribution": {"high": 0, "medium": 0, "low": 0}
        }
        
        if self.training_dataset_collection is not None and self.evaluation_dataset_collection is not None:
            # Count training entries
            stats["training_count"] = self.training_dataset_collection.count_documents({})
            
            # Count evaluation entries
            stats["evaluation_count"] = self.evaluation_dataset_collection.count_documents({})
            
            # Total is sum of both (they're separate now)
            stats["total_entries"] = stats["training_count"] + stats["evaluation_count"]
            
            # Aggregate categories and quality from training collection
            for entry in self.training_dataset_collection.find():
                for tag in entry.get("tags", []):
                    stats["categories_breakdown"][tag] = stats["categories_breakdown"].get(tag, 0) + 1
                
                quality = entry.get("quality_score", 0.5)
                if quality >= 0.8:
                    stats["quality_distribution"]["high"] += 1
                elif quality >= 0.5:
                    stats["quality_distribution"]["medium"] += 1
                else:
                    stats["quality_distribution"]["low"] += 1
            
            # Aggregate categories and quality from evaluation collection
            for entry in self.evaluation_dataset_collection.find():
                for tag in entry.get("tags", []):
                    stats["categories_breakdown"][tag] = stats["categories_breakdown"].get(tag, 0) + 1
                
                quality = entry.get("quality_score", 0.5)
                if quality >= 0.8:
                    stats["quality_distribution"]["high"] += 1
                elif quality >= 0.5:
                    stats["quality_distribution"]["medium"] += 1
                else:
                    stats["quality_distribution"]["low"] += 1
        
        else:
            # In-memory fallback
            stats["training_count"] = len(self.training_dataset)
            stats["evaluation_count"] = len(self.evaluation_dataset)
            stats["total_entries"] = stats["training_count"] + stats["evaluation_count"]
            
            for entry in list(self.training_dataset.values()) + list(self.evaluation_dataset.values()):
                for tag in entry.get("tags", []):
                    stats["categories_breakdown"][tag] = stats["categories_breakdown"].get(tag, 0) + 1
                
                quality = entry.get("quality_score", 0.5)
                if quality >= 0.8:
                    stats["quality_distribution"]["high"] += 1
                elif quality >= 0.5:
                    stats["quality_distribution"]["medium"] += 1
                else:
                    stats["quality_distribution"]["low"] += 1
        
        return stats
    
    # ==================== Helper Methods ====================
    
    def _convert_dates_to_iso(self, doc: Dict):
        """Convert datetime objects to ISO strings in a document."""
        for key in ["created_at", "updated_at", "reviewed_at"]:
            if key in doc and isinstance(doc[key], datetime):
                doc[key] = doc[key].isoformat()


# Global feedback database instance
feedback_db = FeedbackDatabase()
