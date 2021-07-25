import logging

import connexion
from ext import ResolverComp
from connexion.resolver import Resolver, MethodViewResolver

logging.basicConfig(level=logging.INFO)

app = connexion.App(__name__, specification_dir='openapi/')
options = {'swagger_ui': True}
resolver = ResolverComp({'^/api/': MethodViewResolver('api')}, Resolver())
app.add_api('crud_api.yaml',
            options=options,
            resolver=resolver,
            strict_validation=True,
            validate_responses=True,
            pythonic_params=True)

if __name__ == '__main__':
    app.run(port=8080)
