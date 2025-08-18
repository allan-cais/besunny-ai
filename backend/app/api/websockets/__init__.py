"""
WebSocket router for BeSunny.ai Python backend.
Handles real-time communication for document processing, notifications, and updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List
import json
import logging

from ...core.security import get_current_user
from ...core.database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: dict = {}  # user_id -> List[WebSocket]
    
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Connect a new WebSocket."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
        
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, user_id: str = None):
        """Disconnect a WebSocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, user_id: str):
        """Send message to specific user."""
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")
                    # Remove broken connection
                    self.disconnect(connection, user_id)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connections."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                # Remove broken connection
                self.disconnect(connection)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """General WebSocket endpoint."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo the message back
            await websocket.send_text(f"Message received: {message}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/documents/{document_id}")
async def document_websocket(
    websocket: WebSocket,
    document_id: str,
    user_id: str = None
):
    """WebSocket endpoint for document-specific updates."""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Send document status updates
            # In a real implementation, you would:
            # 1. Check document status from database
            # 2. Send updates when status changes
            # 3. Handle user interactions
            
            await websocket.send_text(json.dumps({
                "type": "document_status",
                "document_id": document_id,
                "status": "processing",
                "timestamp": "2024-01-01T00:00:00Z"
            }))
            
            # Wait for user input or status change
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": "2024-01-01T00:00:00Z"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


@router.websocket("/ws/notifications")
async def notifications_websocket(
    websocket: WebSocket,
    user_id: str = None
):
    """WebSocket endpoint for user notifications."""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Send notifications to user
            # In a real implementation, you would:
            # 1. Check for new notifications
            # 2. Send real-time updates
            # 3. Handle notification interactions
            
            await websocket.send_text(json.dumps({
                "type": "notification",
                "message": "New document processed",
                "timestamp": "2024-01-01T00:00:00Z"
            }))
            
            # Wait for user input
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "mark_read":
                # Mark notification as read
                await websocket.send_text(json.dumps({
                    "type": "notification_read",
                    "timestamp": "2024-01-01T00:00:00Z"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


@router.websocket("/ws/processing")
async def processing_websocket(
    websocket: WebSocket,
    user_id: str = None
):
    """WebSocket endpoint for processing status updates."""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Send processing status updates
            # In a real implementation, you would:
            # 1. Monitor background tasks
            # 2. Send progress updates
            # 3. Handle task cancellation
            
            await websocket.send_text(json.dumps({
                "type": "processing_status",
                "status": "running",
                "progress": 50,
                "message": "Processing document...",
                "timestamp": "2024-01-01T00:00:00Z"
            }))
            
            # Wait for user input
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "cancel":
                # Cancel processing
                await websocket.send_text(json.dumps({
                    "type": "processing_cancelled",
                    "timestamp": "2024-01-01T00:00:00Z"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


# Utility functions for other modules to send WebSocket messages
async def send_document_update(user_id: str, document_id: str, status: str):
    """Send document update to user via WebSocket."""
    message = json.dumps({
        "type": "document_update",
        "document_id": document_id,
        "status": status,
        "timestamp": "2024-01-01T00:00:00Z"
    })
    await manager.send_personal_message(message, user_id)


async def send_notification(user_id: str, message: str, notification_type: str = "info"):
    """Send notification to user via WebSocket."""
    notification = json.dumps({
        "type": "notification",
        "message": message,
        "notification_type": notification_type,
        "timestamp": "2024-01-01T00:00:00Z"
    })
    await manager.send_personal_message(notification, user_id)


async def broadcast_system_message(message: str):
    """Broadcast system message to all connected users."""
    system_message = json.dumps({
        "type": "system_message",
        "message": message,
        "timestamp": "2024-01-01T00:00:00Z"
    })
    await manager.broadcast(system_message)
