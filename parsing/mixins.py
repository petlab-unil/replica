class NestedContentStrMixin:

    def to_dict(self):
        import types
        attrs = [attr for attr in dir(self) if not type(getattr(self, attr)) == types.MethodType and
                 not attr.startswith('__')]

        container = {}
        for attr in attrs:
            value = self.__getattribute__(attr)
            if isinstance(value, list):
                nested_list = []
                for e in value:
                    if isinstance(e, NestedContentStrMixin):
                        nested_list.append(e.to_dict())
                    else:
                        nested_list.append(e.__dict__)
                container[attr] = nested_list
            else:
                try:
                    container[attr] = value.__dict__
                except AttributeError:
                    container[attr] = value
        return container

    def __str__(self):
        import types
        attrs = [attr for attr in dir(self) if not type(getattr(self, attr)) == types.MethodType and
                 not attr.startswith('__')]
        str_dict = {}
        for attr in attrs:
            value = self.__getattribute__(attr)
            if isinstance(value, list):
                str_dict[attr] = [str(e) for e in value]
            else:
                str_dict[attr] = str(value)
        return str(str_dict)