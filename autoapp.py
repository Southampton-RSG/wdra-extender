"""Create an application instance."""
from wdra_extender.app import create_app

app, celery = create_app()
