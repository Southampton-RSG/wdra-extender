#!/usr/bin/env python
import os
from wdra_extender.app import create_app

app = create_app()
app.app_context().push()
