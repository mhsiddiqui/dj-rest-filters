# Fields Guild

Filter fields handle converting between primitive values and internal datatypes. They also deal with validating input values with builtin as well as custom validation methods. They also provide builtin as well as custom filtering methods. 

## Core Arguments

### lookup_expr
Lookup expression is the operation used to filter data from your model. By default, its value for most of the fields is `exact`. But it can be overridden by any of the expressions supported by Django.

### distinct
With this argument, you can control if you want to apply distinct function to your queryset.

### exclude
Its boolean parameter control if you want to apply the `filter` of `exclude` operation in your filter. If `exclude=True` then data according to provided query parameters will be excluded from queryset.

### required
With this argument, a field can be marked as required or optional. Contrary to the serializer, by default, it will be `False` in filters.

### default
If set, this gives the default value that will be used for the field if no input value is supplied. If not set the default behavior is to not populate the attribute at all.

### allow_null
Normally an error will be raised if None is passed to a filter field. Set this keyword argument to `True` if None should be considered a valid value.

### source
The source is provided if the declared field will be used to filter on the basis of another field. This is used when there are foreign keys in your model and you want to filter on the basis of those foreign keys.

### validators
A list of validator functions which should be applied to the incoming field input, and which either raise a validation error or simply return. Validator functions should typically raise serializers.ValidationError, but Django's built-in ValidationError is also supported for compatibility with validators defined in the Django codebase or third party Django packages.

### error_messages
A dictionary of error codes to error messages.

### label
A short text string that may be used as the name of the field in HTML form fields or other descriptive elements.

### help_text
A text string that may be used as a description of the field in HTML form fields or other descriptive elements.

### initial
A value that should be used for pre-populating the value of HTML form fields. You may pass a callable to it, just as you may do with any regular Django Field:

```python
import datetime
from djfilters import filters
class ExampleFilter(filters.Filter):
    day = filters.DateField(initial=datetime.date.today)
```

## Field List

### BooleanField
Boolean field can be used when query param will have any boolean value. Its a nullable field with `default=None`. In model filter, it corresponds to `django.db.models.fields.BooleanField`. For model filter, you can set it as required by using `extra_kwargs` option.

**Signature**: `BooleanField()`

### CharField
A text field which validates the text to be shorter than `max_length` and longer than `min_length`. In model filter, it corresponds to `django.db.models.fields.CharField` or `django.db.models.fields.TextField`.

**Signature**: `CharField(max_length=None, min_length=None, allow_blank=False, trim_whitespace=True)`

* `max_length` - Validates that the input contains no more than this number of characters.
* `min_length` - Validates that the input contains no fewer than this number of characters.
* `allow_blank` - If set to `True` then the empty string should be considered a valid value. If set to `False` then the empty string is considered invalid and will raise a validation error. Defaults to `False`.
* `trim_whitespace` - If set to `True` then leading and trailing whitespace is trimmed. Defaults to `True`.


### EmailField
A text representation, validates the text to be a valid e-mail address.

Corresponds to `django.db.models.fields.EmailField`

**Signature**: `EmailField(max_length=None, min_length=None, allow_blank=False)`

### SlugField

A text field that validates the input against the pattern [a-zA-Z0-9_-]+.

Corresponds to `django.db.models.fields.SlugField`.

**Signature**: `SlugField(max_length=50, min_length=None, allow_blank=False)`

### URLField
A text field that validates the input against a URL matching pattern. Expects fully qualified URLs of the form `http://<host>/<path>`.

Corresponds to `django.db.models.fields.URLField`. Uses Django's `django.core.validators.URLValidator` for validation.

**Signature**: `URLField(max_length=200, min_length=None, allow_blank=False)`

### IPAddressField
A field that ensures the input is a valid IPv4 or IPv6 string.

Corresponds to `django.forms.fields.IPAddressField` and `django.forms.fields.GenericIPAddressField`.

**Signature**: `IPAddressField(protocol='both', unpack_ipv4=False, **options)`

* `protocol` Limits valid inputs to the specified protocol. Accepted values are 'both' (default), 'IPv4' or 'IPv6'. Matching is case insensitive.
* `unpack_ipv4` Unpacks IPv4 mapped addresses like ::ffff:192.0.2.1. If this option is enabled that address would be unpacked to 192.0.2.1. Default is disabled. Can only be used when protocol is set to 'both'.

### IntegerField
An integer field.

Corresponds to `django.db.models.fields.IntegerField`, `django.db.models.fields.SmallIntegerField`, `django.db.models.fields.PositiveIntegerField` and `django.db.models.fields.PositiveSmallIntegerField`.

**Signature**: `IntegerField(max_value=None, min_value=None)`

* `max_value` Validate that the number provided is no greater than this value.
* `min_value` Validate that the number provided is no less than this value.

### FloatField
A floating point field.

Corresponds to `django.db.models.fields.FloatField`.

**Signature**: `FloatField(max_value=None, min_value=None)`

* `max_value` Validate that the number provided is no greater than this value.
* `min_value` Validate that the number provided is no less than this value.

### DecimalField
A decimal field, represented in Python by a Decimal instance.

Corresponds to `django.db.models.fields.DecimalField`.

**Signature**: `DecimalField(max_digits, decimal_places, max_value=None, min_value=None)`

* `max_digits` The maximum number of digits allowed in the number. It must be either `None` or an integer greater than or equal to `decimal_places`.
* `decimal_places` The number of decimal places to store with the number.
* `max_value` Validate that the number provided is no greater than this value.
* `min_value` Validate that the number provided is no less than this value.

**Example usage**

To validate numbers up to 999 with a resolution of 2 decimal places, you would use:

```python
filters.DecimalField(max_digits=5, decimal_places=2)
```
And to validate numbers up to anything less than one billion with a resolution of 10 decimal places:
```python
filters.DecimalField(max_digits=19, decimal_places=10)
```

### DateTimeField
A date and time field.

Corresponds to `django.db.models.fields.DateTimeField`.

**Signature**: `DateTimeField(input_formats=None, default_timezone=None)`

* `input_formats` - A list of strings representing the input formats which may be used to parse the date. If not specified, the `DATETIME_INPUT_FORMATS` setting will be used, which defaults to `['iso-8601']`.
* `default_timezone` - A `tzinfo` subclass (`zoneinfo` or `pytz`) prepresenting the timezone. If not specified and the `USE_TZ` setting is enabled, this defaults to the current timezone. If `USE_TZ` is disabled, then datetime objects will be naive.

For this field, lookup expression supported by Django such as `date` or `date__year` or `date__month` can be used.

### DurationField
A Duration field. Corresponds to `django.db.models.fields.DurationField`

The `validated_data` for these fields will contain a `datetime.timedelta` instance. The representation is a string following this format `[DD] [HH:[MM:]]ss[.uuuuuu]`.

**Signature**: `DurationField(max_value=None, min_value=None)`

* `max_value` Validate that the duration provided is no greater than this value.
* `min_value` Validate that the duration provided is no less than this value.

### DateField
A date field.

Corresponds to `django.db.models.fields.DateField`

**Signature**: `DateField(input_formats=None)`

* `input_formats` - A list of strings representing the input formats which may be used to parse the date. If not specified, the `DATE_INPUT_FORMATS` setting will be used, which defaults to `['iso-8601']`.

### TimeField
A time field.

Corresponds to `django.db.models.fields.TimeField`

**Signature**: `TimeField(input_formats=None)`

* `input_formats` - A list of strings representing the input formats which may be used to parse the date. If not specified, the `TIME_INPUT_FORMATS` setting will be used, which defaults to `['iso-8601']`.

### ChoiceField
A field that can accept a value out of a limited set of choices.

Used by ModelFilter to automatically generate fields if the corresponding model field includes a `choices=…` argument.

**Signature**: `ChoiceField(choices)`

* `choices` - A list of valid values, or a list of `(key, display_name)` tuples.
* `allow_blank` - If set to `True` then the empty string should be considered a valid value. If set to `False` then the empty string is considered invalid and will raise a validation error. Defaults to `False`.
* `html_cutoff` - If set this will be the maximum number of choices that will be displayed by a HTML select drop down. Can be used to ensure that automatically generated ChoiceFields with very large possible selections do not prevent a template from rendering. Defaults to `None`.
* `html_cutoff_text` - If set this will display a textual indicator if the maximum number of items have been cutoff in an HTML select drop down. Defaults to `"More than {count} items…"`
Both the `allow_blank` and `allow_null` are valid options on `ChoiceField`, although it is highly recommended that you only use one and not both. `allow_blank` should be preferred for textual choices, and `allow_null` should be preferred for numeric or other non-textual choices.

### ListField
A field class that validates a list of objects.

**Signature**: `ListField(child=<A_FIELD_INSTANCE>, allow_empty=True, min_length=None, max_length=None, separator=',')`

* `child` - A field instance that should be used for validating the objects in the list. If this argument is not provided then objects in the list will not be validated.
* `allow_empty` - Designates if empty lists are allowed.
* `min_length` - Validates that the list contains no fewer than this number of elements.
* `max_length` - Validates that the list contains no more than this number of elements.
* `separator`- A separator which will be used to split values. By default it is `,`.

The value of `lookup_expr` for `ListField` is `in`.

For example, to validate a list of integers you might use something like the following:
```python
scores = filters.ListField(
   child=filters.IntegerField(min_value=0, max_value=100)
)

```
### RangeField

A list field which is used for range filtering. In this field, list must have 2 values. 

**Signature**: `RangeField(child=<A_FIELD_INSTANCE>, allow_empty=True, separator=',')`

* `child` - A field instance that should be used for validating the objects in the list. If this argument is not provided then objects in the list will not be validated.
* `allow_empty` - Designates if empty lists are allowed.
* `separator`- A separator which will be used to split values. By default it is `,`.

The value of `lookup_expr` for `ListField` is `range`. By default range operation use `gte` and `lte` lookup expression. This can be overriden by providing `lookup_expr` in list for like `lookup_expr=['gt', 'lt']`. Values should be in same order for this to work properly.

For example, to validate a list of integers you might use something like the following:
```python
scores = filters.RangeField(
   child=filters.IntegerField(min_value=0, max_value=100)
)

```
Its query will be `scores__range=[10, 20]`.

## Custom Field

To define custom field, you need to inherrit your field from default serializer field and filter field like this

```python
from rest_framework import serializers
from djfilters import filters

class CustomField(filters.FilterField, serializers.Field):
    pass
```
