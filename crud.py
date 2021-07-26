import connexion
from connexion.resolver import Resolver, MethodViewResolver

from util import ResolverComp
from db import init_db

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

flask_app = app.app

if __name__ == '__main__':
    app.run(port=8080, debug=True)