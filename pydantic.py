"""Minimal fallback for the repository's plain data models.

Normal installations use the declared Pydantic dependency; this keeps the
focused ledger tests usable in the runtime check's dependency-free venv.
"""

class Field:
    def __init__(self, default=None, **kwargs):
        self.default = default


class BaseModel:
    def __init__(self, **values):
        annotations = getattr(type(self), "__annotations__", {})
        for name in annotations:
            if name in values:
                value = values[name]
            else:
                default = getattr(type(self), name, None)
                value = default.default if isinstance(default, Field) else default
            setattr(self, name, value)

    def __eq__(self, other):
        return type(self) is type(other) and self.__dict__ == other.__dict__
