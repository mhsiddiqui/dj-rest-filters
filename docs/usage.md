# Usage

Dj-rest-filters provides simple way to filter queryset based on the parameters provided in query params. Beside filtering, it can also just be used to validate query parameters. Writing a filter is very similar to writing a serializer. So if you are familiar with serializers, you can easily write a filter. The filters can be used with DRF GenericViews. To use it, you need to set `filter_class` attribute in your view.

## Filtering
```python
from rest_framework import generics
from djfilters.backend import DjFilterBackend


class TodoView(generics.GenericAPIView):
    serializer_class = ...
    filter_class = TodoFilter
    filter_backends = [DjFilterBackend]
    queryset = Todo.objects.all()
```

## Validation Only
When queryset is declared, filter will be used to filter that queryset. But when there is not any queryset, filter will just be used to validate the provided query parameters.

```python
from rest_framework import generics

class TodoView(generics.GenericAPIView):
    serializer_class = ...
    filter_class = MyFilter
```

## Filter Context
Just like serializer context, context can be passed to filter by using `get_filter_context` function like this.

```python
from rest_framework import generics

class TodoView(generics.GenericAPIView):
    ....

    def get_filter_context(self):
        context = {'extra_data': 'some_extra_data'}
        return context
```

## Accessing Validated Query Params
After query param validation, validated parameters can be accessed using `request.cleaned_args`.
