# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`dj-rest-filters` is a Django/DRF library that lets users declaratively validate URL query parameters and filter a `QuerySet` using DRF serializer syntax. It is wired into a view as a DRF filter backend.

## Common commands

Tests use Django's test runner (not pytest) and require `DJANGO_SETTINGS_MODULE=tests.test_settings`.

```bash
# Run the full test suite (current interpreter)
DJANGO_SETTINGS_MODULE=tests.test_settings PYTHONPATH=. django-admin test -v2 tests

# Run a single test module / class / method
DJANGO_SETTINGS_MODULE=tests.test_settings PYTHONPATH=. django-admin test tests.test_filters
DJANGO_SETTINGS_MODULE=tests.test_settings PYTHONPATH=. django-admin test tests.test_filters.SomeTestCase.test_something

# Multi-version matrix (Python 3.7–3.11 × Django 1.11–4.2)
tox                          # everything
tox -e py311-dj42            # one combo
tox -e isort                 # import-order check (isort --check-only --diff djfilters tests)
tox -e lint                  # flake8 (max-line-length = 160)

# Build the docs site (mkdocs-material)
mkdocs serve
```

There is no `manage.py`; the test suite is the only runtime entry point. `tox` uses `usedevelop = true`, so the package is installed in editable mode for tests.

## Architecture

The library is one DRF filter backend wired around a serializer-shaped filter class.

- **`djfilters/backend.py` — `DjFilterBackend`**: DRF filter backend. `filter_queryset` reads `view.filter_class`, instantiates it with `request.query_params` and the view's queryset, calls `is_valid()`, stores `validated_data` on `request.cleaned_args`, and either returns the unfiltered queryset (if `None`/empty) or delegates to `filterset.filter(validated_data)`. Optional `view.get_filter_context()` is merged into the serializer context. Also implements `get_schema_fields` (coreapi) and `get_schema_operation_parameters` (OpenAPI) so filters appear in DRF's schema generation.

- **`djfilters/filters/filters.py`**:
  - `Filter` subclasses `rest_framework.serializers.Serializer`. `Filter.filter(validated_data)` iterates `self.fields`, and for each field either calls a user-defined `filter_<name>(qs, value)` on the filter class (for custom filtering) or the field's own `.filter(qs, value)`. Source paths with `.` are translated to `__`-joined ORM lookups; trailing `.id` collapses to `<rel>_id`.
  - `ModelFilter` subclasses `Filter` + `ModelSerializer`. It supplies its own `serializer_field_mapping` pointing model field types at the `FilterField` subclasses (not DRF's defaults). `get_fields()` mirrors `ModelSerializer.get_fields()` but forces every generated field to `required=False` and rejects nested filters / `Meta.depth`. `Meta.fields = '__all__'` (or an explicit list) / `Meta.exclude` are required, same as DRF.

- **`djfilters/filters/fields.py` — `FilterField` mixin**: All filter field classes are `class XField(FilterField, RestXField)`. The mixin adds `lookup_expr` (default `'exact'`), `distinct`, and `exclude` kwargs, defaults `required=False`, and implements `make_query` to translate `(field_name, lookup_expr, value)` into `qs.filter(...)` or `qs.exclude(...)`. `ListField` parses comma-separated or JSON-array query strings and defaults to `lookup_expr='in'`. `RangeField` accepts a 2-element list and supports either a single lookup (e.g. `'range'`) or a tuple of two lookups (e.g. `('gte', 'lte')`) applied positionally. `BooleanField` falls back to DRF's `BooleanField` on DRF ≥ 3.14 (where `NullBooleanField` was removed) — see `try/except` at top of the file.

- **`djfilters/compat.py`**: optional `coreapi` / `coreschema` imports — schema methods on the backend assert these are installed before use.

- **`djfilters/__init__.py`**: holds `__version__` (parsed by `setup.py` via regex) and sets `default_app_config` only on Django < 3.2.

## Conventions worth knowing

- A view without a `queryset` still works — the backend treats that as validation-only mode and just populates `request.cleaned_args` with the validated query params.
- To customize how a single declared field filters, define `filter_<field_name>(self, qs, value)` on the `Filter` subclass; the backend's per-field dispatch will pick it up and skip the default `field.filter()`.
- Field `source` with a dotted path (e.g. `source='author.name'`) is the supported way to map a query-param name to a different ORM lookup; the backend rewrites it to `author__name` (or `author_id` if the last part is `id`).
- Lint is flake8 with `max-line-length = 160`; imports are managed with `isort`. Both run in tox envs `lint` and `isort`.
