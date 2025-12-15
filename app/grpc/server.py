"""
gRPC Server for SSO Backend

Runs gRPC server alongside FastAPI for inter-service communication.
"""

import logging
from typing import Optional

import grpc
from grpc.aio import Server

from app.config.settings import settings
from proto.sso import user_pb2_grpc, auth_pb2_grpc
from app.grpc.handlers.auth_handler import AuthHandler
from app.grpc.handlers.user_handler import UserHandler

logger = logging.getLogger(__name__)


class GRPCServer:
    """Async gRPC server manager."""
    
    def __init__(self, port: int = 50051):
        self.port = port
        self._server: Optional[Server] = None
    
    async def start(self) -> None:
        """Start the gRPC server."""
        max_msg_size = getattr(settings, 'GRPC_MAX_MESSAGE_SIZE', 15 * 1024 * 1024)
        options = [
            ('grpc.max_send_message_length', max_msg_size),
            ('grpc.max_receive_message_length', max_msg_size),
        ]
        self._server = grpc.aio.server(options=options)
        
        # Register handlers
        auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthHandler(), self._server)
        user_pb2_grpc.add_UserServiceServicer_to_server(UserHandler(), self._server)
        
        # Bind to port
        listen_addr = f"[::]:{self.port}"
        self._server.add_insecure_port(listen_addr)
        
        await self._server.start()
        logger.info(f"gRPC server started on port {self.port}")
    
    async def stop(self) -> None:
        """Stop the gRPC server gracefully."""
        if self._server:
            await self._server.stop(grace=5)
            logger.info("gRPC server stopped")
    
    async def wait_for_termination(self) -> None:
        """Wait for server to terminate."""
        if self._server:
            await self._server.wait_for_termination()


# Global server instance
grpc_server = GRPCServer(port=getattr(settings, 'GRPC_PORT', 50051))
