"""
Feedback Database with PostgreSQL

Persistent storage for AI feedback and training datasets.
"""
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database.postgres_config import PostgresConfig
from ..database.models import Feedback, TrainingDataset, EvaluationDataset, FeedbackStatusEnum, FeedbackTypeEnum
from .models import FeedbackStatus, FeedbackType, DatasetType
import uuid
import logging

logger = logging.getLogger(__name__)


class FeedbackDatabase:
    """PostgreSQL-backed feedback database for AI response improvement."""
    
    def __init__(self):
        """Initialize feedback database."""
        try:
            PostgresConfig.check_database_exists()
            logger.info("✅ Feedback database initialized with PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to initialize feedback database: {e}")
            raise
    
    # ==================== FEEDBACK MANAGEMENT ====================
    
    def create_feedback(self, user_id: str, feedback_data: Dict) -> Dict:
        """Create new feedback entry."""
        try:
            db = PostgresConfig.get_session()
            
            # Store detailed feedback info in metadata
            metadata = {
                "conversation_id": feedback_data.get("conversation_id"),
                "message_id": feedback_data.get("message_id"),
                "user_message": feedback_data.get("user_message"),
                "ai_response": feedback_data.get("ai_response"),
                "tags": feedback_data.get("tags", []),
                "suggested_response": feedback_data.get("suggested_response"),
            }
            
            feedback = Feedback(
                id=str(uuid.uuid4()),
                user_id=user_id,
                feedback_type=feedback_data.get("feedback_type"),
                status=FeedbackStatusEnum.PENDING,
                content=feedback_data.get("comment", ""),
                rating=feedback_data.get("rating"),
                related_response_id=feedback_data.get("message_id"),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata_json=metadata
            )
            
            db.add(feedback)
            db.commit()
            
            result = self._convert_feedback_to_dict(feedback)
            db.close()
            
            logger.info(f"✅ Created feedback: {feedback.id}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error creating feedback: {e}")
            db.close()
            raise
    
    def get_feedback(self, feedback_id: str) -> Optional[Dict]:
        """Get feedback by ID."""
        try:
            db = PostgresConfig.get_session()
            fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
            result = self._convert_feedback_to_dict(fb) if fb else None
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting feedback {feedback_id}: {e}")
            db.close()
            return None
    
    def get_user_feedback(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get feedback by user."""
        try:
            db = PostgresConfig.get_session()
            feedbacks = db.query(Feedback).filter(
                Feedback.user_id == user_id
            ).order_by(desc(Feedback.created_at)).limit(limit).all()
            
            result = [self._convert_feedback_to_dict(fb) for fb in feedbacks]
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting feedback for user {user_id}: {e}")
            db.close()
            return []
    
    def get_pending_feedback(self, limit: int = 100) -> List[Dict]:
        """Get all pending feedback for review."""
        try:
            db = PostgresConfig.get_session()
            feedbacks = db.query(Feedback).filter(
                Feedback.status == FeedbackStatusEnum.PENDING
            ).order_by(Feedback.created_at.asc()).limit(limit).all()
            
            result = [self._convert_feedback_to_dict(fb) for fb in feedbacks]
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting pending feedback: {e}")
            db.close()
            return []
    
    def get_feedback_by_status(self, status: str, limit: int = 100) -> List[Dict]:
        """Get feedback by status."""
        try:
            db = PostgresConfig.get_session()
            feedbacks = db.query(Feedback).filter(
                Feedback.status == status
            ).order_by(desc(Feedback.updated_at)).limit(limit).all()
            
            result = [self._convert_feedback_to_dict(fb) for fb in feedbacks]
            db.close()
            return result
        except Exception as e:
            logger.error(f"Error getting feedback by status {status}: {e}")
            db.close()
            return []
    
    def update_feedback_status(self, feedback_id: str, status: str) -> Optional[Dict]:
        """Update feedback status."""
        try:
            db = PostgresConfig.get_session()
            
            fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
            if not fb:
                logger.warning(f"Feedback {feedback_id} not found")
                db.close()
                return None
            
            fb.status = status
            fb.updated_at = datetime.now()
            db.commit()
            
            result = self._convert_feedback_to_dict(fb)
            db.close()
            
            logger.info(f"✅ Updated feedback status: {feedback_id}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error updating feedback: {e}")
            db.close()
            raise
    
    def review_feedback(self, feedback_id: str, reviewer_id: str, review_data: Dict) -> Optional[Dict]:
        """Review feedback and update status."""
        try:
            db = PostgresConfig.get_session()
            
            fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
            if not fb:
                logger.warning(f"Feedback {feedback_id} not found")
                db.close()
                return None
            
            fb.status = review_data.get("status", fb.status)
            fb.reviewer_id = reviewer_id
            fb.reviewer_comment = review_data.get("reviewer_comment")
            fb.reviewed_at = datetime.now()
            fb.updated_at = datetime.now()
            
            # Update tags if provided
            if review_data.get("new_tags"):
                fb.tags = review_data.get("new_tags")
            
            db.commit()
            
            result = self._convert_feedback_to_dict(fb)
            db.close()
            
            logger.info(f"✅ Reviewed feedback: {feedback_id}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error reviewing feedback: {e}")
            db.close()
            raise
    
    def get_feedback_stats(self) -> Dict:
        """Get feedback statistics."""
        try:
            db = PostgresConfig.get_session()
            
            total = db.query(Feedback).count()
            pending = db.query(Feedback).filter(Feedback.status == FeedbackStatusEnum.PENDING).count()
            approved = db.query(Feedback).filter(Feedback.status == FeedbackStatusEnum.APPROVED).count()
            denied = db.query(Feedback).filter(Feedback.status == FeedbackStatusEnum.DENIED).count()
            reclassified = db.query(Feedback).filter(Feedback.status == FeedbackStatusEnum.RECLASSIFIED).count()
            
            thumbs_up = db.query(Feedback).filter(Feedback.feedback_type == FeedbackTypeEnum.THUMBS_UP).count()
            thumbs_down = db.query(Feedback).filter(Feedback.feedback_type == FeedbackTypeEnum.THUMBS_DOWN).count()
            
            # Calculate average rating from rated feedback
            from sqlalchemy import func
            avg_rating_result = db.query(func.avg(Feedback.rating)).filter(Feedback.rating.isnot(None)).scalar()
            avg_rating = float(avg_rating_result) if avg_rating_result else None
            
            # Feedback by category (from tags)
            feedback_by_category = {}
            all_feedback = db.query(Feedback).all()
            for feedback in all_feedback:
                if hasattr(feedback, 'tags') and feedback.tags:
                    tags = feedback.tags if isinstance(feedback.tags, list) else []
                    for tag in tags:
                        feedback_by_category[tag] = feedback_by_category.get(tag, 0) + 1
            
            # Feedback by user
            from sqlalchemy import func as sqlfunc
            user_feedback = db.query(Feedback.user_id, sqlfunc.count(Feedback.id)).group_by(Feedback.user_id).all()
            feedback_by_user = {user_id: count for user_id, count in user_feedback}
            
            db.close()
            
            return {
                "total_feedback": total,
                "pending_review": pending,
                "approved": approved,
                "denied": denied,
                "reclassified": reclassified,
                "thumbs_up_count": thumbs_up,
                "thumbs_down_count": thumbs_down,
                "avg_rating": avg_rating,
                "feedback_by_category": feedback_by_category,
                "feedback_by_user": feedback_by_user
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            try:
                db.close()
            except:
                pass
            return {
                "total_feedback": 0,
                "pending_review": 0,
                "approved": 0,
                "denied": 0,
                "reclassified": 0,
                "thumbs_up_count": 0,
                "thumbs_down_count": 0,
                "avg_rating": None,
                "feedback_by_category": {},
                "feedback_by_user": {}
            }
    
    def get_user_feedback_stats(self, user_id: str) -> Dict:
        """Get feedback statistics for a specific user."""
        try:
            db = PostgresConfig.get_session()
            
            total = db.query(Feedback).filter(Feedback.user_id == user_id).count()
            pending = db.query(Feedback).filter(
                Feedback.user_id == user_id,
                Feedback.status == FeedbackStatusEnum.PENDING
            ).count()
            approved = db.query(Feedback).filter(
                Feedback.user_id == user_id,
                Feedback.status == FeedbackStatusEnum.APPROVED
            ).count()
            denied = db.query(Feedback).filter(
                Feedback.user_id == user_id,
                Feedback.status == FeedbackStatusEnum.DENIED
            ).count()
            
            thumbs_up = db.query(Feedback).filter(
                Feedback.user_id == user_id,
                Feedback.feedback_type == FeedbackTypeEnum.THUMBS_UP
            ).count()
            thumbs_down = db.query(Feedback).filter(
                Feedback.user_id == user_id,
                Feedback.feedback_type == FeedbackTypeEnum.THUMBS_DOWN
            ).count()
            
            db.close()
            
            return {
                "total_feedback": total,
                "pending": pending,
                "approved": approved,
                "denied": denied,
                "thumbs_up": thumbs_up,
                "thumbs_down": thumbs_down
            }
            
        except Exception as e:
            logger.error(f"Error getting user feedback stats: {e}")
            db.close()
            return {
                "total_feedback": 0,
                "pending": 0,
                "approved": 0,
                "denied": 0,
                "thumbs_up": 0,
                "thumbs_down": 0
            }
    
    # ==================== DATASET MANAGEMENT ====================
    
    def add_training_data(self, user_id: str, input_text: str, output_text: str, **kwargs) -> Dict:
        """Add training data entry."""
        try:
            db = PostgresConfig.get_session()
            
            training = TrainingDataset(
                id=str(uuid.uuid4()),
                user_id=user_id,
                input_text=input_text,
                output_text=output_text,
                score=kwargs.get("score"),
                category=kwargs.get("category"),
                created_at=datetime.now(),
                metadata=kwargs.get("metadata", {})
            )
            
            db.add(training)
            db.commit()
            
            result = self._convert_training_to_dict(training)
            db.close()
            
            logger.info(f"✅ Added training data: {training.id}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error adding training data: {e}")
            db.close()
            raise
    
    def add_evaluation_data(self, user_id: str, input_text: str, expected_output: str, **kwargs) -> Dict:
        """Add evaluation data entry."""
        try:
            db = PostgresConfig.get_session()
            
            evaluation = EvaluationDataset(
                id=str(uuid.uuid4()),
                user_id=user_id,
                input_text=input_text,
                expected_output=expected_output,
                actual_output=kwargs.get("actual_output"),
                accuracy_score=kwargs.get("accuracy_score"),
                category=kwargs.get("category"),
                created_at=datetime.now(),
                metadata=kwargs.get("metadata", {})
            )
            
            db.add(evaluation)
            db.commit()
            
            result = self._convert_evaluation_to_dict(evaluation)
            db.close()
            
            logger.info(f"✅ Added evaluation data: {evaluation.id}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error adding evaluation data: {e}")
            db.close()
            raise
    
    def get_dataset_entries(self, dataset_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get dataset entries."""
        try:
            db = PostgresConfig.get_session()
            
            entries = []
            
            if dataset_type == DatasetType.TRAINING or not dataset_type:
                training = db.query(TrainingDataset).order_by(
                    desc(TrainingDataset.created_at)
                ).limit(limit).all()
                entries.extend([self._convert_training_to_dict(t) for t in training])
            
            if dataset_type == DatasetType.EVALUATION or not dataset_type:
                evaluation = db.query(EvaluationDataset).order_by(
                    desc(EvaluationDataset.created_at)
                ).limit(limit).all()
                entries.extend([self._convert_evaluation_to_dict(e) for e in evaluation])
            
            db.close()
            return entries
            
        except Exception as e:
            logger.error(f"Error getting dataset entries: {e}")
            db.close()
            return []
    
    def get_dataset_stats(self) -> Dict:
        """Get dataset statistics."""
        db = None
        try:
            db = PostgresConfig.get_session()
            
            training_count = db.query(TrainingDataset).count()
            evaluation_count = db.query(EvaluationDataset).count()
            
            db.close()
            
            return {
                "training_count": training_count,
                "evaluation_count": evaluation_count,
                "total_entries": training_count + evaluation_count,
                "categories_breakdown": {},
                "quality_distribution": {}
            }
            
        except Exception as e:
            logger.error(f"Error getting dataset stats: {e}")
            if db:
                try:
                    db.close()
                except:
                    pass
            return {}
    
    # ==================== HELPER METHODS ====================
    
    @staticmethod
    def _convert_feedback_to_dict(fb: Feedback) -> Dict:
        """Convert Feedback model to dictionary."""
        if not fb:
            return None
        
        metadata = fb.metadata_json or {}
        
        return {
            "id": fb.id,
            "user_id": fb.user_id,
            "feedback_type": fb.feedback_type,
            "status": fb.status,
            "content": fb.content,
            "rating": fb.rating,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
            "updated_at": fb.updated_at.isoformat() if fb.updated_at else None,
            # Extract fields from metadata for API response (with defaults for backward compatibility)
            "conversation_id": metadata.get("conversation_id") or "legacy",
            "message_id": metadata.get("message_id") or fb.id,
            "user_message": metadata.get("user_message") or fb.content,
            "ai_response": metadata.get("ai_response") or "N/A",
            "tags": metadata.get("tags") or [],
            "comment": fb.content,
            "suggested_response": metadata.get("suggested_response"),
            "reviewer_id": metadata.get("reviewer_id"),
            "reviewer_comment": metadata.get("reviewer_comment"),
            "dataset_type": metadata.get("dataset_type"),
            "reviewed_at": metadata.get("reviewed_at"),
            "metadata": metadata
        }
    
    @staticmethod
    def _convert_training_to_dict(training: TrainingDataset) -> Dict:
        """Convert TrainingDataset model to dictionary."""
        if not training:
            return None
        
        return {
            "id": training.id,
            "user_id": training.user_id,
            "input_text": training.input_text,
            "output_text": training.output_text,
            "score": training.score,
            "category": training.category,
            "created_at": training.created_at.isoformat() if training.created_at else None,
            "dataset_type": DatasetType.TRAINING,
            "metadata": training.metadata_json or {}
        }
    
    @staticmethod
    def _convert_evaluation_to_dict(evaluation: EvaluationDataset) -> Dict:
        """Convert EvaluationDataset model to dictionary."""
        if not evaluation:
            return None
        
        return {
            "id": evaluation.id,
            "user_id": evaluation.user_id,
            "input_text": evaluation.input_text,
            "expected_output": evaluation.expected_output,
            "actual_output": evaluation.actual_output,
            "accuracy_score": evaluation.accuracy_score,
            "category": evaluation.category,
            "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
            "dataset_type": DatasetType.EVALUATION,
            "metadata": evaluation.metadata_json or {}
        }


# Global feedback database instance
feedback_db = FeedbackDatabase()
