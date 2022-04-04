# encoding: utf-8

from pydantic import BaseModel


class HashableModel(BaseModel):
    """
    Base model for all models that can be hashed.

    This base class allows us to directly compare two R53Record (or other)
    models directly, with the `==` operator without resorting to additional
    code or logic. To enable this behaviour, it's sufficient to define your
    model as a subclass of HashableModel.
    """
    def __hash__(self):

        def is_list(x):
            return isinstance(x, list)

        flat_values = []
        for v in self.__dict__.values():
            if is_list(v):
                flat_values.extend(v)
            else:
                flat_values.append(v)

        return hash((type(self),) + tuple(flat_values))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()