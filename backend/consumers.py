# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from typing import Any
import json
import uuid
from datetime import datetime

class DashboardConsumer(AsyncWebsocketConsumer):
    """
    Main WebSocket consumer handling:
    - Cursor tracking (broadcast, no DB)
    - Task mutations (optimistic + DB sync)
    - Chat messages (DB + broadcast)
    """
    
    async def connect(self):
        """
        WebSocket connection handler.
        Authenticate user, join room group, track presence.
        """
        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"dashboard_{self.room_id}"
        self.user_id = str(self.user.id) if self.user.is_authenticated else str(uuid.uuid4())
        self.user_color = self._assign_user_color()
        
        # Validate room access
        if not await self._user_has_room_access():
            await self.close(code=403)
            return
        
        # Join the channel group for this room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Track user presence in Redis
        await self._record_user_presence(status="online")
        
        await self.accept()
        
        # Notify other users of presence
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "user_id": self.user_id,
                "username": self.user.username if self.user.is_authenticated else "Guest",
                "user_color": self.user_color,
            }
        )
    
    async def disconnect(self, close_code):
        """
        Clean up on disconnect: remove from group, mark offline.
        """
        await self._record_user_presence(status="offline")
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_left",
                "user_id": self.user_id,
            }
        )
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data: str):
        """
        Route incoming WebSocket messages by type.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get("type")
            
            if message_type == "cursor_move":
                await self.handle_cursor_move(data)
            elif message_type == "task_move":
                await self.handle_task_move(data)
            elif message_type == "chat_message":
                await self.handle_chat_message(data)
            else:
                await self.send_error(f"Unknown message type: {message_type}")
        
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
        except Exception as e:
            await self.send_error(f"Processing error: {str(e)}")
    
    # ========== CURSOR TRACKING (HIGH-FREQUENCY, EPHEMERAL) ==========
    
    async def handle_cursor_move(self, data: dict):
        """
        Broadcast cursor position to all users in room.
        - NO database persistence
        - Throttled on frontend (33ms = ~30 FPS)
        - Low-latency group broadcast
        """
        cursor_event = {
            "type": "cursor_update",
            "user_id": self.user_id,
            "user_color": self.user_color,
            "x": data.get("x"),
            "y": data.get("y"),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Broadcast to all users in room (except sender, handled by frontend)
        await self.channel_layer.group_send(
            self.room_group_name,
            cursor_event
        )
    
    async def cursor_update(self, event: dict):
        """
        Receive cursor_update from group and push to WebSocket.
        """
        await self.send(text_data=json.dumps({
            "type": "cursor_update",
            "data": {
                "user_id": event["user_id"],
                "user_color": event["user_color"],
                "x": event["x"],
                "y": event["y"],
            }
        }))
    
    # ========== TASK MUTATIONS (OPTIMISTIC + DB SYNC) ==========
    
    async def handle_task_move(self, data: dict):
        """
        Handle drag-and-drop task update.
        Flow:
          1. Validate task & permissions
          2. Update database asynchronously
          3. Broadcast new state to all clients
          4. Handle conflict resolution if needed
        """
        task_id = data.get("task_id")
        new_status = data.get("new_status")
        new_position = data.get("position")  # { "x": ..., "y": ... }
        
        try:
            # Async DB operation
            task_updated = await self._update_task_in_db(
                task_id=task_id,
                user_id=self.user_id,
                new_status=new_status,
                new_position=new_position
            )
            
            if task_updated:
                # Broadcast successful update to all clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "task_state_changed",
                        "task_id": task_id,
                        "new_status": new_status,
                        "new_position": new_position,
                        "updated_by": self.user_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            else:
                # Task locked or permission denied
                await self.send_error(
                    f"Cannot update task {task_id}. Already being edited.",
                    error_code="TASK_LOCKED"
                )
        
        except Exception as e:
            await self.send_error(f"Task update failed: {str(e)}", error_code="DB_ERROR")
    
    async def task_state_changed(self, event: dict):
        """
        Broadcast task state change to client.
        """
        await self.send(text_data=json.dumps({
            "type": "task_state_changed",
            "data": {
                "task_id": event["task_id"],
                "new_status": event["new_status"],
                "new_position": event["new_position"],
                "updated_by": event["updated_by"],
                "timestamp": event["timestamp"],
            }
        }))
    
    # ========== CHAT & NOTIFICATIONS (PERSISTED) ==========
    
    async def handle_chat_message(self, data: dict):
        """
        Store chat message in DB, then broadcast to room.
        """
        message_text = data.get("message", "").strip()
        
        if not message_text or len(message_text) > 2000:
            await self.send_error("Message must be 1-2000 characters")
            return
        
        try:
            # Save to database
            chat_msg = await self._save_chat_message(
                room_id=self.room_id,
                user_id=self.user_id,
                username=self.user.username if self.user.is_authenticated else "Guest",
                message=message_text
            )
            
            # Broadcast to all connected users in room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message_broadcast",
                    "message_id": chat_msg.id,
                    "user_id": self.user_id,
                    "username": chat_msg.username,
                    "message": message_text,
                    "timestamp": chat_msg.created_at.isoformat(),
                }
            )
        
        except Exception as e:
            await self.send_error(f"Failed to save message: {str(e)}")
    
    async def chat_message_broadcast(self, event: dict):
        """
        Push chat message to connected client.
        """
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "data": {
                "message_id": event["message_id"],
                "user_id": event["user_id"],
                "username": event["username"],
                "message": event["message"],
                "timestamp": event["timestamp"],
            }
        }))
    
    # ========== PRESENCE & UTILITY HANDLERS ==========
    
    async def user_joined(self, event: dict):
        """Broadcast when user joins."""
        await self.send(text_data=json.dumps({
            "type": "user_joined",
            "data": {
                "user_id": event["user_id"],
                "username": event["username"],
                "user_color": event["user_color"],
            }
        }))
    
    async def user_left(self, event: dict):
        """Broadcast when user leaves."""
        await self.send(text_data=json.dumps({
            "type": "user_left",
            "data": {"user_id": event["user_id"]}
        }))
    
    # ========== DATABASE OPERATIONS (Async Wrappers) ==========
    
    @database_sync_to_async
    def _user_has_room_access(self) -> bool:
        """Check if user has permission to access this room."""
        from .models import Room
        try:
            room = Room.objects.get(id=self.room_id)
            return self.user in room.members.all() or room.is_public
        except Room.DoesNotExist:
            return False
    
    @database_sync_to_async
    def _update_task_in_db(self, task_id: str, user_id: str, 
                           new_status: str, new_position: dict) -> bool:
        """
        Update task in database with optimistic locking.
        Returns True if successful, False if conflict.
        """
        from .models import Task
        from django.db import transaction
        
        try:
            with transaction.atomic():
                task = Task.objects.select_for_update().get(id=task_id)
                
                # Verify permissions
                if not self._user_can_edit_task(task, user_id):
                    return False
                
                # Update task
                task.status = new_status
                if new_position:
                    task.position_x = new_position.get("x")
                    task.position_y = new_position.get("y")
                task.updated_by_id = user_id
                task.save()
                
                return True
        
        except Exception as e:
            print(f"Task update error: {e}")
            return False
    
    @database_sync_to_async
    def _save_chat_message(self, room_id: str, user_id: str, 
                          username: str, message: str):
        """Persist chat message to database."""
        from .models import ChatMessage
        
        msg = ChatMessage.objects.create(
            room_id=room_id,
            user_id=user_id,
            username=username,
            message=message
        )
        return msg
    
    @database_sync_to_async
    def _record_user_presence(self, status: str):
        """Track user presence in Redis via Django cache."""
        from django.core.cache import cache
        
        presence_key = f"presence:{self.room_id}:{self.user_id}"
        if status == "online":
            cache.set(presence_key, {
                "username": self.user.username if self.user.is_authenticated else "Guest",
                "connected_at": datetime.now().isoformat(),
                "color": self.user_color,
            }, timeout=3600)  # 1-hour TTL
        else:
            cache.delete(presence_key)
    
    def _assign_user_color(self) -> str:
        """Assign a distinct color for cursor tracking."""
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A",
            "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2"
        ]
        hash_val = hash(self.user_id) % len(colors)
        return colors[hash_val]
    
    def _user_can_edit_task(self, task, user_id: str) -> bool:
        """Check edit permissions."""
        return task.room.members.filter(id=user_id).exists()
    
    async def send_error(self, message: str, error_code: str = "ERROR"):
        """Send error response to client."""
        await self.send(text_data=json.dumps({
            "type": "error",
            "error_code": error_code,
            "message": message,
        }))
