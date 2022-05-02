from __future__ import unicode_literals

import re

from django.core.validators import EMPTY_VALUES
from rest_framework.fields import CharField as RestCharField
from rest_framework.fields import ChoiceField as RestChoiceField
from rest_framework.fields import DateField as RestDateField
from rest_framework.fields import DateTimeField as RestDateTimeField
from rest_framework.fields import DecimalField as RestDecimalField
from rest_framework.fields import DurationField as RestDurationField
from rest_framework.fields import EmailField as RestEmailField
from rest_framework.fields import FloatField as RestFloatField
from rest_framework.fields import IntegerField as RestIntegerField
from rest_framework.fields import IPAddressField as RestIPAddressField
from rest_framework.fields import ListField as RestListField
from rest_framework.fields import NullBooleanField as RestNullBooleanField
from rest_framework.fields import SlugField as RestSlugField
from rest_framework.fields import TimeField as RestTimeField
from rest_framework.fields import URLField as RestURLField
from rest_framework.fields import empty
from rest_framework.relations import \
    PrimaryKeyRelatedField as RestPrimaryKeyRelatedField
from rest_framework.relations import SlugRelatedField as RestSlugRelatedField
from rest_framework.utils import json


class FilterField(object):

    def __init__(self, **kwargs):
        self.lookup_expr = kwargs.pop('lookup_expr', 'exact')
        self.distinct = kwargs.pop('distinct', False)
        self.exclude = kwargs.pop('exclude', False)
        self.extra = kwargs
        required = kwargs.pop('required', None)
        if not required:
            required = False
        super(FilterField, self).__init__(required=required, **kwargs)

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        qs = self.make_query(qs, value)
        return qs

    def make_query(self, qs, value):
        field_name = self.field_name
        if field_name != self.source:
            field_name = self.source
            if '.' in field_name:
                parts = field_name.split('.')
                value = self.get_nested_value(parts, value)
                if parts[-1] == 'id':
                    field_name = '{}_{}'.format('__'.join(parts[:-1]), 'id')
                else:
                    field_name = '__'.join(parts)
        qs = self.get_method(qs)(**{'%s__%s' % (
            field_name,
            self.lookup_expr
        ): value})
        return qs

    def get_nested_value(self, parts, value):
        """
        Get nested value from a dictionary
        """
        field_ptr = 1
        while isinstance(value, dict):
            value = value.get(parts[field_ptr])
            field_ptr += 1
        return value

    def get_method(self, qs):
        """Return filter method based on whether we're excluding
           or simply filtering.
        """
        return qs.exclude if self.exclude else qs.filter

    def validate_empty_values(self, data):
        """
        Validate empty values, and either:

        * Raise `ValidationError`, indicating invalid data.
        * Raise `SkipField`, indicating that the field should be ignored.
        * Return (True, data), indicating an empty value that should be
          returned without any further validation being applied.
        * Return (False, data), indicating a non-empty value, that should
          have validation applied as normal.
        """

        if data is empty:
            if self.required:
                self.fail('required')
            return (
                True, self.get_default()
            )

        if data is None:
            if not self.allow_null:
                self.fail('null')
            return (
                True, None
            )
        return (
            False, data
        )

    def bind(self, field_name, parent):
        """
        Initializes the field name and parent for the field instance.
        Called when a field is added to the parent serializer instance.
        """

        # In order to enforce a consistent style, we error if a redundant
        # 'source' argument has been used. For example:
        # my_field = serializer.CharField(source='my_field')
        if self.source:
            assert self.source != field_name, (
                    "It is redundant to specify `source='%s'` on field '%s' in "
                    "filter '%s', because it is the same as the field name. "
                    "Remove the `source` keyword argument." %
                    (field_name, self.__class__.__name__, parent.__class__.__name__)
            )

        self.field_name = field_name
        self.parent = parent

        # `self.label` should default to being based on the field name.
        if self.label is None:
            self.label = field_name.replace('_', ' ').capitalize()

        # self.source should default to being the same as the field name.
        if self.source is None:
            self.source = field_name

        # self.source_attrs is a list of attributes that need to be looked up
        # when serializing the instance, or populating the validated data.
        if self.source == '*':
            self.source_attrs = []
        else:
            self.source_attrs = self.source.split('.')


class PrimaryKeyRelatedField(FilterField, RestPrimaryKeyRelatedField):
    pass


class SlugRelatedField(FilterField, RestSlugRelatedField):
    pass


class BooleanField(FilterField, RestNullBooleanField):
    pass


class CharField(FilterField, RestCharField):
    pass


class EmailField(FilterField, RestEmailField):
    pass


class SlugField(FilterField, RestSlugField):
    pass


class URLField(FilterField, RestURLField):
    pass


class IPAddressField(FilterField, RestIPAddressField):
    pass


class IntegerField(FilterField, RestIntegerField):
    pass


class FloatField(FilterField, RestFloatField):
    pass


class DecimalField(FilterField, RestDecimalField):
    pass


class DateTimeField(FilterField, RestDateTimeField):
    pass


class DurationField(FilterField, RestDurationField):
    pass


class DateField(FilterField, RestDateField):
    pass


class TimeField(FilterField, RestTimeField):
    pass


class ChoiceField(FilterField, RestChoiceField):
    pass


class ListField(FilterField, RestListField):

    def __init__(self, separator=',', lookup_expr='in', *args, **kwargs):
        self.separator = separator
        super(ListField, self).__init__(lookup_expr=lookup_expr, *args, **kwargs)

    def get_value(self, dictionary):
        value = super(ListField, self).get_value(dictionary)
        if len(value) == 1:
            if re.match(r"\[([\"']?[a-zA-Z0-9][\"']?,? ?)+\]", value[0]):
                value = json.loads(value[0])
            elif re.match(r"([A-Za-z0-9]{seperator}?)+".format(seperator=self.separator), value[0]):
                value = value[0].split(self.separator)
        return value


class RangeField(ListField):
    def __init__(self, lookup_expr='range', *args, **kwargs):
        kwargs.pop('min_length', None)
        kwargs.pop('max_length', None)
        super(RangeField, self).__init__(lookup_expr=lookup_expr, min_length=2, max_length=2, *args, **kwargs)

    def make_query(self, qs, value):
        if isinstance(self.lookup_expr, str):
            return super(RangeField, self).make_query(qs, value)
        else:
            filters = {}
            for lookup, val in zip(self.lookup_expr, value):
                filters['%s__%s' % (
                    self.field_name if self.field_name == self.source else self.source,
                    lookup
                )] = val
            qs = self.get_method(qs)(**filters)
            return qs
