# dj-rest-filters

dj-rest-filters is a Django application allowing users to declaratively add dynamic QuerySet filtering from URL parameters. Its uses Django Rest Framework serializers in backend so it provides same syntax as of serializers. You can validate you query parameter in same way as you validate in your serializer and it also provides filtering mechanism against custom query parameters.

[![Build](https://github.com/mhsiddiqui/dj-rest-filters/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/mhsiddiqui/dj-rest-filters/actions/workflows/test.yml) [![codecov](https://codecov.io/gh/mhsiddiqui/dj-rest-filters/branch/master/graph/badge.svg?token=IBWACI93GM)](https://codecov.io/gh/mhsiddiqui/dj-rest-filters) [![Docs](https://readthedocs.org/projects/dj-rest-filters/badge/?version=latest)](https://dj-rest-filters.readthedocs.io/en/latest/?badge=latest)


## Installation

> pip install dj-rest-filters

Then add 'djfilters' to your INSTALLED_APPS.

## Usage

### Filtering
```python
from rest_framework import generics
from djfilters.backend import DjFilterBackend


class TodoView(generics.GenericAPIView):
    serializer_class = ...
    filter_class = TodoFilter
    filter_backends = [DjFilterBackend]
    queryset = Todo.objects.all()
```

### Validation Only
When queryset is declared, filter will be used to filter that queryset. But when there is not any queryset, filter will just be used to validate the provided query parameters.

```python
from rest_framework import generics

class TodoView(generics.GenericAPIView):
    serializer_class = ...
    filter_class = MyFilter
```

### Filter Context
Just like serializer context, context can be passed to filter by using `get_filter_context` function like this.

```python
from rest_framework import generics

class TodoView(generics.GenericAPIView):
    ....

    def get_filter_context(self):
        context = {'extra_data': 'some_extra_data'}
        return context
```

### Accessing Validated Query Params
After query param validation, validated parameters can be accessed using `request.cleaned_args`.


For detailed documentation, click [here](https://dj-rest-filters.readthedocs.io/en/latest/).





