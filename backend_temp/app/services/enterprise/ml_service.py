"""
ML Service for Phase 4 enterprise features.
Provides machine learning capabilities for business intelligence and analytics.
"""

import uuid
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import asyncio
import logging
import json
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.schemas.enterprise import (
    MLModelCreate, MLModelUpdate, MLModelResponse, MLModelListResponse,
    MLModelStatus, MLModelType, MLTrainingJob, MLPredictionRequest,
    MLPredictionResponse, MLModelMetrics
)
from app.core.security import get_current_user_optional
from app.core.database import get_db
from app.services.ai import AIService

logger = logging.getLogger(__name__)


class MLService:
    """Service for managing machine learning models and predictions."""
    
    def __init__(self):
        self.settings = get_settings()
        self._model_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self.ai_service = None  # Lazy initialization
    
    async def _get_ai_service(self) -> AIService:
        """Get AI service instance."""
        if self.ai_service is None:
            self.ai_service = AIService()
        return self.ai_service
    
    async def create_model(self, model_data: MLModelCreate, user_id: str) -> MLModelResponse:
        """Create a new ML model."""
        try:
            # Validate model configuration
            await self._validate_model_config(model_data)
            
            # Create model record
            model_id = str(uuid.uuid4())
            model = {
                "id": model_id,
                "name": model_data.name,
                "description": model_data.description,
                "model_type": model_data.model_type,
                "version": model_data.version,
                "status": MLModelStatus.DRAFT,
                "configuration": model_data.configuration,
                "hyperparameters": model_data.hyperparameters,
                "training_data_config": model_data.training_data_config,
                "validation_data_config": model_data.validation_data_config,
                "performance_metrics": {},
                "created_by": user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Store in database (placeholder for now)
            self._model_cache[model_id] = model
            
            logger.info(f"Created ML model {model_id} of type {model_data.model_type}")
            
            return MLModelResponse(
                id=model_id,
                created_at=model["created_at"],
                updated_at=model["updated_at"],
                created_by=user_id,
                **{k: v for k, v in model.items() if k not in ["id", "created_at", "updated_at", "created_by"]}
            )
            
        except Exception as e:
            logger.error(f"Failed to create ML model: {str(e)}")
            raise
    
    async def get_model(self, model_id: str) -> Optional[MLModelResponse]:
        """Get ML model by ID."""
        try:
            # Check cache first
            if model_id in self._model_cache:
                model = self._model_cache[model_id]
                return MLModelResponse(
                    id=model_id,
                    created_at=model["created_at"],
                    updated_at=model["updated_at"],
                    created_by=model["created_by"],
                    **{k: v for k, v in model.items() if k not in ["id", "created_at", "updated_at", "created_by"]}
                )
            
            # In production, this would query the database
            return None
            
        except Exception as e:
            logger.error(f"Failed to get ML model {model_id}: {str(e)}")
            raise
    
    async def list_models(
        self,
        user_id: str,
        model_type: Optional[MLModelType] = None,
        status: Optional[MLModelStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> MLModelListResponse:
        """List ML models with filtering."""
        try:
            # Filter models based on criteria
            models = []
            for model_id, model in self._model_cache.items():
                if model["created_by"] == user_id:
                    if model_type and model["model_type"] != model_type:
                        continue
                    if status and model["status"] != status:
                        continue
                    models.append(model)
            
            # Apply pagination
            total = len(models)
            models = models[offset:offset + limit]
            
            # Convert to response format
            model_responses = []
            for model in models:
                model_responses.append(MLModelResponse(
                    id=model["id"],
                    created_at=model["created_at"],
                    updated_at=model["updated_at"],
                    created_by=model["created_by"],
                    **{k: v for k, v in model.items() if k not in ["id", "created_at", "updated_at", "created_by"]}
                ))
            
            return MLModelListResponse(
                models=model_responses,
                total=total,
                limit=limit,
                offset=offset
            )
            
        except Exception as e:
            logger.error(f"Failed to list ML models: {str(e)}")
            raise
    
    async def update_model(self, model_id: str, model_data: MLModelUpdate, user_id: str) -> MLModelResponse:
        """Update ML model."""
        try:
            # Get existing model
            model = await self.get_model(model_id)
            if not model:
                raise ValueError(f"ML model {model_id} not found")
            
            # Check permissions
            if model.created_by != user_id:
                raise PermissionError("Insufficient permissions to update this model")
            
            # Update model fields
            update_data = model_data.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            # Update cache
            if model_id in self._model_cache:
                self._model_cache[model_id].update(update_data)
            
            # Get updated model
            updated_model = await self.get_model(model_id)
            if not updated_model:
                raise ValueError("Failed to retrieve updated model")
            
            logger.info(f"Updated ML model {model_id}")
            return updated_model
            
        except Exception as e:
            logger.error(f"Failed to update ML model {model_id}: {str(e)}")
            raise
    
    async def delete_model(self, model_id: str, user_id: str) -> bool:
        """Delete ML model."""
        try:
            # Get existing model
            model = await self.get_model(model_id)
            if not model:
                raise ValueError(f"ML model {model_id} not found")
            
            # Check permissions
            if model.created_by != user_id:
                raise PermissionError("Insufficient permissions to delete this model")
            
            # Remove from cache
            if model_id in self._model_cache:
                del self._model_cache[model_id]
            
            logger.info(f"Deleted ML model {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete ML model {model_id}: {str(e)}")
            raise
    
    async def train_model(self, model_id: str, user_id: str) -> MLTrainingJob:
        """Start model training."""
        try:
            # Get model
            model = await self.get_model(model_id)
            if not model:
                raise ValueError(f"ML model {model_id} not found")
            
            # Check permissions
            if model.created_by != user_id:
                raise PermissionError("Insufficient permissions to train this model")
            
            # Check model status
            if model.status != MLModelStatus.DRAFT:
                raise ValueError(f"Model {model_id} is not in draft status")
            
            # Create training job
            job_id = str(uuid.uuid4())
            training_job = MLTrainingJob(
                id=job_id,
                model_id=model_id,
                status="training",
                started_at=datetime.utcnow(),
                created_by=user_id
            )
            
            # Update model status
            await self.update_model(
                model_id,
                MLModelUpdate(status=MLModelStatus.TRAINING),
                user_id
            )
            
            # Start training in background
            asyncio.create_task(self._train_model_background(job_id, model_id))
            
            logger.info(f"Started training for ML model {model_id}")
            return training_job
            
        except Exception as e:
            logger.error(f"Failed to start training for model {model_id}: {str(e)}")
            raise
    
    async def _train_model_background(self, job_id: str, model_id: str):
        """Background task for model training."""
        try:
            # Simulate training process
            await asyncio.sleep(10)  # Simulate training time
            
            # Update model status to trained
            if model_id in self._model_cache:
                self._model_cache[model_id]["status"] = MLModelStatus.TRAINED
                self._model_cache[model_id]["updated_at"] = datetime.utcnow()
            
            logger.info(f"Completed training for ML model {model_id}")
            
        except Exception as e:
            logger.error(f"Training failed for model {model_id}: {str(e)}")
            # Update model status to error
            if model_id in self._model_cache:
                self._model_cache[model_id]["status"] = MLModelStatus.ERROR
                self._model_cache[model_id]["updated_at"] = datetime.utcnow()
    
    async def make_prediction(
        self,
        model_id: str,
        prediction_request: MLPredictionRequest,
        user_id: str
    ) -> MLPredictionResponse:
        """Make prediction using trained model."""
        try:
            # Get model
            model = await self.get_model(model_id)
            if not model:
                raise ValueError(f"ML model {model_id} not found")
            
            # Check model status
            if model.status != MLModelStatus.TRAINED:
                raise ValueError(f"Model {model_id} is not trained")
            
            # Get AI service for prediction
            ai_service = await self._get_ai_service()
            
            # Make prediction (placeholder implementation)
            prediction_result = {
                "prediction": "sample_prediction",
                "confidence": 0.85,
                "model_version": model.version,
                "processing_time_ms": 150
            }
            
            # Create prediction response
            prediction_response = MLPredictionResponse(
                id=str(uuid.uuid4()),
                model_id=model_id,
                input_data=prediction_request.input_data,
                prediction_result=prediction_result,
                created_at=datetime.utcnow(),
                created_by=user_id
            )
            
            logger.info(f"Made prediction using model {model_id}")
            return prediction_response
            
        except Exception as e:
            logger.error(f"Failed to make prediction with model {model_id}: {str(e)}")
            raise
    
    async def get_model_metrics(self, model_id: str, user_id: str) -> MLModelMetrics:
        """Get model performance metrics."""
        try:
            # Get model
            model = await self.get_model(model_id)
            if not model:
                raise ValueError(f"ML model {model_id} not found")
            
            # Check permissions
            if model.created_by != user_id:
                raise PermissionError("Insufficient permissions to access this model")
            
            # Return metrics (placeholder implementation)
            metrics = MLModelMetrics(
                model_id=model_id,
                accuracy=0.92,
                precision=0.89,
                recall=0.94,
                f1_score=0.91,
                training_time_seconds=120,
                inference_time_ms=45,
                total_predictions=1000,
                last_updated=datetime.utcnow()
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics for model {model_id}: {str(e)}")
            raise
    
    async def _validate_model_config(self, model_data: MLModelCreate):
        """Validate model configuration."""
        # Validate model type specific requirements
        if model_data.model_type == MLModelType.CLASSIFICATION:
            if not model_data.training_data_config:
                raise ValueError("Training data configuration required for classification models")
        
        # Validate hyperparameters
        if model_data.hyperparameters:
            required_params = ["learning_rate", "batch_size", "epochs"]
            for param in required_params:
                if param not in model_data.hyperparameters:
                    raise ValueError(f"Required hyperparameter '{param}' missing")
        
        # Validate version format
        if not model_data.version or not model_data.version.startswith("v"):
            raise ValueError("Version must start with 'v' (e.g., 'v1.0.0')")
    
    async def export_model(self, model_id: str, user_id: str, format: str = "onnx") -> Dict[str, Any]:
        """Export model in specified format."""
        try:
            # Get model
            model = await self.get_model(model_id)
            if not model:
                raise ValueError(f"ML model {model_id} not found")
            
            # Check permissions
            if model.created_by != user_id:
                raise PermissionError("Insufficient permissions to export this model")
            
            # Check model status
            if model.status != MLModelStatus.TRAINED:
                raise ValueError(f"Model {model_id} is not trained")
            
            # Export model (placeholder implementation)
            export_data = {
                "model_id": model_id,
                "format": format,
                "exported_at": datetime.utcnow(),
                "file_size_mb": 25.5,
                "checksum": "abc123def456",
                "download_url": f"/api/v1/ml/models/{model_id}/export/{format}"
            }
            
            logger.info(f"Exported model {model_id} in {format} format")
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export model {model_id}: {str(e)}")
            raise
