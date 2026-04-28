# Releases

## v1.1.0 ([latest](/en/latest/))

### Highlights
- Python 3.14 added to the supported matrix; full test suite verified on Django 5.2 + DRF 3.17.
- Much richer OpenAPI / Swagger schema generation. Filter fields now map to correct OpenAPI types and formats (`integer`, `boolean`, `string` + `date` / `date-time` / `email` / `uri`, etc.) instead of every parameter rendering as `string`. `ListField` and `RangeField` produce `type: array` with `items` derived from the child field; `RangeField` adds `minItems: 2` / `maxItems: 2`.
- Verified end-to-end with both [drf-spectacular](https://github.com/tfranzel/drf-spectacular) and [drf-yasg](https://github.com/axnsan12/drf-yasg) — see the new [Swagger / OpenAPI guide](/swagger/).
- New [Query Parameters reference](/query_parameters/) covering URL formats for booleans, lists (CSV / JSON-array / repeated keys), ranges, and dates.

### Bug fixes
- `DjFilterBackend.filter_queryset` now always returns a queryset; previously it fell off the end as `None` in validation-only mode, breaking pagination downstream.
- Removed a paginator monkey-patch (`view.paginator.get_results = lambda data: data`) that persisted across requests after a validation error.
- `ListField.get_value` now correctly parses multi-character JSON arrays (`["foo","bar"]`) and multi-character comma-separated values (`12,34,56`); the previous regex only matched single-character items.
- `FilterField.get_nested_value` now bounds-checks the source-path parts list instead of running off the end with an `IndexError` on deep dotted sources.
- Schema methods (`get_schema_fields`, `get_schema_operation_parameters`) no longer raise `TypeError` when a view has no `filter_class` — they return `[]`.
- Removed a hardcoded literal-`'slug_fk'` check in `ModelFilter.get_fields()` (a debugging leftover); the "nested filters not supported" assertion now applies to every declared field.
- Filter-method-override detection rewritten to use class-level identity (`type(self).filter is not Filter.filter`) instead of comparing bound methods with `==`.
- Replaced the `if queryset not in [None, [], '']:` pattern that triggered Python's `NotImplemented` rich-comparison fallback on every request with explicit `is`/`!=` checks.

### Compatibility
- Dropped the `six` and `pytz` dependencies (`six` is no longer needed on Python 3; `pytz` was unused).
- Install floors raised to realistic versions: Python ≥ 3.8, Django ≥ 3.2, DRF ≥ 3.12 (previously Python ≥ 3, Django > 1.10, DRF > 3.3).
- Tox matrix and CI workflow updated: dropped Python 3.7 and Django 1.x – 4.0 combos; added Django 5.0 / 5.1 / 5.2 and Python 3.12 / 3.13 / 3.14.
- GitHub Actions bumped to current majors (`checkout@v4`, `setup-python@v5`, `codecov-action@v4`); pip caching enabled.

### Other
- New `release.yml` workflow publishes to PyPI on GitHub Release using OIDC trusted publishing (no API token required).
- Dependabot config added for `github-actions` and `pip` ecosystems.
- 9 new tests covering `ListField` / `RangeField` parsing edge cases and the OpenAPI type mapping; total suite is now 125 tests.

## v1.0.4

## v1.0.3
Bug fixing

## v1.0.2
Added support for Django 4.2 and Python 3.11

## v1.0.1
Bug fixing

## v1.0.0
Features included

1. Simple Filters (For filtering and validation)
2. Model Filters
3. All possible fields   
4. Filter Backend
5. Browsable API Support
6. Swagger Support
7. Documentation
