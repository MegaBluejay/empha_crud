from hashlib import sha256
import re

__all__ = ['ResolverComp', 'hash_string']

def hash_string(s: str) -> str:
    return sha256(s.encode('utf8')).hexdigest()

class ResolverComp:

    def __init__(self, resolvers, default_resolver = None):
        self.default_resolver = default_resolver
        self.resolvers = {(re.compile(rgx) if isinstance(rgx,str) else rgx): res for rgx, res in resolvers.items()}

    def resolve(self, operation):
        path = operation.path
        for rgx, res in self.resolvers.items():
            if rgx.match(path):
                return res.resolve(operation)
        if self.default_resolver:
            return self.default_resolver.resolve(operation)
        raise
