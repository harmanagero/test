from mangum import Mangum

from .api.api import app


handler = Mangum(app, enable_lifespan=False)
