# Query Parameter Formats

This page describes the URL formats accepted for each kind of filter field — useful reference when constructing requests against your filtered endpoints.

## Strings

`CharField`, `EmailField`, `SlugField`, `URLField`, and `IPAddressField` all consume the raw query-string value:

```
GET /todos/?title=Buy%20groceries
```

For case-insensitive partial matching, declare the filter with `lookup_expr='icontains'` and the same URL syntax produces a `LIKE %Buy groceries%` query.

## Numbers

`IntegerField`, `FloatField`, and `DecimalField` parse the value with the corresponding Python type. Out-of-range or malformed values produce a 400 `ValidationError`.

```
GET /products/?price_gte=9.99
```

## Booleans

`BooleanField` follows DRF's permissive parser. **All of these are valid:**

| Truthy                                   | Falsy                                   |
|------------------------------------------|-----------------------------------------|
| `true`, `True`, `TRUE`, `1`, `yes`, `on` | `false`, `False`, `FALSE`, `0`, `no`, `off` |

```
GET /todos/?completed=true
GET /todos/?completed=1
```

If `allow_null=True`, the values `null`, `Null`, and the empty string `""` resolve to `None`.

## Dates and times

`DateField`, `DateTimeField`, and `TimeField` default to ISO-8601 input. Override with `input_formats=` if you need other formats.

```
GET /todos/?created=2024-12-31
GET /events/?starts_at=2024-12-31T18:00:00Z
GET /events/?starts_at=2024-12-31T18:00:00+05:00
GET /shifts/?starts=09:30:00
```

## Lists (`ListField`)

`ListField` accepts three input shapes; the first one that matches is used.

**1. Comma-separated string** (default separator — change with `separator=`):

```
GET /todos/?tags=urgent,today,backlog
```

**2. JSON-array string** — for values that contain commas or other special characters:

```
GET /todos/?tags=["red,green","blue"]
```

**3. Repeated query keys** (DRF/QueryDict standard):

```
GET /todos/?tags=urgent&tags=today&tags=backlog
```

All three produce the same validated list `['urgent', 'today', 'backlog']` and a `tags__in=(...)` query.

## Ranges (`RangeField`)

`RangeField` accepts the same three input shapes as `ListField` but the list must contain **exactly two** elements.

```
GET /products/?price=10,100
GET /products/?price=[10,100]
GET /products/?price=10&price=100
```

With the default `lookup_expr='range'` this produces `price__range=[10, 100]` (inclusive). With `lookup_expr=['gt', 'lt']`, the two values are applied positionally as `price__gt=10 AND price__lt=100`.

## Choices

`ChoiceField` validates the raw value against the configured choices:

```python
class TodoFilter(filters.Filter):
    status = filters.ChoiceField(choices=[('open', 'Open'), ('done', 'Done')])
```

```
GET /todos/?status=open    # OK
GET /todos/?status=foo     # 400 — "is not a valid choice."
```

When schema generation runs, the choices are emitted as `enum` on the OpenAPI parameter.

## Multiple lookups on the same model field

To support `gt` and `lt` on the same column, declare two filters with different names and a shared `source`:

```python
class ProductFilter(filters.Filter):
    price_min = filters.IntegerField(source='price', lookup_expr='gte')
    price_max = filters.IntegerField(source='price', lookup_expr='lte')
```

```
GET /products/?price_min=10&price_max=100
```

## Empty / missing values

A field that is omitted from the URL — or supplied as the empty string — does not contribute to the queryset filter. There is no error unless the field is declared `required=True`.
