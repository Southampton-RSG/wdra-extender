#!/usr/bin/env python
import celery
from wdra_extender.app import create_app

app = create_app()
app.app_context().push()
