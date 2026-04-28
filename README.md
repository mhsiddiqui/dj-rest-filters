# dj-rest-filters

[![Build](https://github.com/mhsiddiqui/dj-rest-filters/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/mhsiddiqui/dj-rest-filters/actions/workflows/test.yml) [![codecov](https://codecov.io/gh/mhsiddiqui/dj-rest-filters/branch/master/graph/badge.svg?token=IBWACI93GM)](https://codecov.io/gh/mhsiddiqui/dj-rest-filters) [![Docs](https://readthedocs.org/projects/dj-rest-filters/badge/?version=latest)](https://dj-rest-filters.readthedocs.io/en/latest/?badge=latest)

A Django REST Framework filter backend that lets you declaratively validate query parameters and filter querysets using DRF serializer syntax. Validate query params the same way you validate request bodies, with the same fields, the same `Meta`, and the same `validate_*` hooks.

📖 **Full docs:** https://dj-rest-filters.readthedocs.io/en/latest/

## Features

- **DRF-native syntax** — filters look like serializers; reuse what you already know.
- **Validation-only mode** — drop the queryset to use a filter purely for query-param validation; cleaned values land on `request.cleaned_args`.
- **`ListField` and `RangeField`** for `IN` and range queries; accepts comma-separated, JSON-array, or repeated-key inputs.
- **Custom per-field filtering** via `filter_<name>(self, qs, value)`, plus `lookup_expr`, `exclude=True`, and `distinct=True` on every field.
- **OpenAPI / Swagger** — schema parameters auto-generated for both [drf-spectacular](https://github.com/tfranzel/drf-spectacular) and [drf-yasg](https://github.com/axnsan12/drf-yasg).
- **Browsable API** support out of the box.

## Requirements

| | Minimum | Tested up to |
|---|---|---|
| Python | 3.8 | 3.14 |
| Django | 3.2 | 5.2 |
| Django REST Framework | 3.12 | 3.17 |

## Installation

```shell
pip install dj-rest-filters
```

Add `djfilters` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...,
    "djfilters",
]
```

## Quickstart

Define a filter — same shape as a DRF serializer:

```python
from djfilters import filters

class TodoFilter(filters.Filter):
    title = filters.CharField(required=False, lookup_expr="icontains")
    completed = filters.BooleanField(required=False)
    tags = filters.ListField(child=filters.CharField(), required=False)
```

Wire it into a view:

```python
from rest_framework import generics
from djfilters.backend import DjFilterBackend

class TodoView(generics.ListAPIView):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    filter_class = TodoFilter
    filter_backends = [DjFilterBackend]
```

`GET /todos/?title=buy&completed=true&tags=urgent,today` filters by `title__icontains="buy"`, `completed=True`, and `tags__in=("urgent", "today")`.

## Validation-only mode

Omit `queryset` to use a filter purely for query-param validation. The filter still runs, errors still surface as 400s, and the cleaned values land on `request.cleaned_args`:

```python
class TodoView(generics.GenericAPIView):
    serializer_class = TodoSerializer
    filter_class = TodoFilter
    filter_backends = [DjFilterBackend]

    def get(self, request):
        params = request.cleaned_args  # validated query params
        ...
```

## Filter context

Just like serializer context, extra context can be passed to the filter from the view:

```python
class TodoView(generics.ListAPIView):
    ...

    def get_filter_context(self):
        return {"user": self.request.user}
```

The returned dict is merged with the default `{"request": ...}` and is accessible as `self.context` inside the filter.

## Documentation

- [Filters & ModelFilters guide](https://dj-rest-filters.readthedocs.io/en/latest/filters/)
- [Field reference](https://dj-rest-filters.readthedocs.io/en/latest/filter_fields/)
- [Usage examples](https://dj-rest-filters.readthedocs.io/en/latest/usage/)

## License

MIT — see [LICENSE](LICENSE).
