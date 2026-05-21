"""WebSocket 连接管理器

管理 WebSocket 连接，支持广播和单点发送。
"""

from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket) -> int:
        """接受 WebSocket 连接并返回 client_id"""
        await websocket.accept()
        client_id = id(websocket)
        self.active_connections[client_id] = websocket
        return client_id

    def disconnect(self, client_id: int):
        """移除连接"""
        self.active_connections.pop(client_id, None)

    async def send_personal_message(self, client_id: int, message: dict):
        """向指定客户端发送消息"""
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """向所有客户端广播消息"""
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(client_id)
        
        for cid in disconnected:
            self.disconnect(cid)


# 全局单例
manager = ConnectionManager()
