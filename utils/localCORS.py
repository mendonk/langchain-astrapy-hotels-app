# Demo-mode to enable React client to axios request an API (both on localhost)
# Not suitable for production.
import fastapi
from fastapi.middleware.cors import CORSMiddleware


def permitReactLocalhostClient(app: fastapi.FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        # This is to avoid CORS issues while on gitpod. Don't do in production.
        allow_origins=["*"],
        # Prefer individual source domains, such as:
        # allow_origins=['http://localhost:3000'],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
