import asyncio
import logging
from concurrent import futures

import grpc
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import settings
from proto.sso import user_pb2_grpc, auth_pb2_grpc
from grpc_server.servicer import UserServicer, AuthServicer

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def serve():
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
        ],
    )

    # Register servicers
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServicer(), server)
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServicer(), server)

    listen_addr = f"{settings.GRPC_HOST}:{settings.GRPC_PORT}"
    server.add_insecure_port(listen_addr)

    logger.info(f"Starting gRPC server on {listen_addr}")
    logger.info("Registered services: UserService, AuthService")
    await server.start()

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        await server.stop(5)


def run_server():
    asyncio.run(serve())


if __name__ == "__main__":
    run_server()
