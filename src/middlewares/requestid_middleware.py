import agero_python_logger
from fastapi import FastAPI
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        agero_python_logger.set_request_ids_with_lambda_context(request.scope.get("aws.context"), request.headers.get("x-correlation-id"))# correlation-id if not present then set-up logger sets it
        return await call_next(request)

def setup_middleware(app: FastAPI):
    app.add_middleware(RequestIdMiddleware)