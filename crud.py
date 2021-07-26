import logging

import connexion
from connexion.resolver import Resolver, MethodViewResolver

from ext import ResolverComp
from db import init_db

logging.basicConfig(level=logging.INFO)

init_db()
app = connexion.App(__name__, specification_dir='openapi/')
options = {'swagger_ui': True}
resolver = ResolverComp({'^/api/': MethodViewResolver('api')}, Resolver())
app.add_api('crud_api.yaml',
            options=options,
            resolver=resolver,
            strict_validation=True,
            validate_responses=True,
            pythonic_params=True)

app.run(port=8080)
