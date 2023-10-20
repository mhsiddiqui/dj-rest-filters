import copy
from collections import OrderedDict

import six
from django.core.validators import EMPTY_VALUES
from django.db import models
from django.db.models import DurationField as ModelDurationField
from django.utils.functional import cached_property
from rest_framework.serializers import ValidationError  # noqa: F401
from rest_framework.serializers import (ALL_FIELDS, ModelSerializer,
                                        Serializer, SerializerMetaclass, empty)
from rest_framework.settings import api_settings
from rest_framework.utils import model_meta

from .fields import (BooleanField, CharField, ChoiceField, DateField,
                     DateTimeField, DecimalField, DurationField, EmailField,
                     FloatField, IntegerField, IPAddressField, ListField,
                     PrimaryKeyRelatedField, SlugField, SlugRelatedField,
                     TimeField, URLField)


@six.add_metaclass(SerializerMetaclass)
class Filter(Serializer):
    def __init__(self, instance=None, data=empty, queryset=None, **kwargs):
        if queryset is None and hasattr(self, 'Meta'):
            queryset = getattr(self, 'Meta').model._default_manager.all()
        self.queryset = queryset
        self.request = kwargs.pop('request', None)
        super(Filter, self).__init__(instance, data, **kwargs)

    @cached_property
    def _writable_fields(self):
        return self._all_fields

    @cached_property
    def _readable_fields(self):
        return self._all_fields

    @cached_property
    def _all_fields(self):
        return [
            field for field in self.fields.values()
        ]

    def filter(self, validated_data):

        qs = self.queryset.all()
        for name, filter_ in six.iteritems(self.fields):
            if filter_.source != name:
                if '.' in filter_.source:
                    name = filter_.source.split('.')[0]
                else:
                    name = filter_.source
            value = validated_data.get(name)
            filter_field = getattr(self, 'filter_{field}'.format(field=name), None)
            if filter_field:
                if value not in EMPTY_VALUES:
                    qs = filter_field(qs, value)
            else:
                qs = filter_.filter(qs, value)
        return qs

    def run_validators(self, value):
        """
        Add read_only fields with defaults to value before running validators.
        """
        if isinstance(value, dict):
            to_validate = self._read_only_defaults()
            to_validate.update(value)
        else:
            to_validate = value
        super(Serializer, self).run_validators(to_validate)


class ModelFilter(Filter, ModelSerializer):
    """
    A `ModelSerializer` is just a regular `Serializer`, except that:

    * A set of default fields are automatically populated.
    * A set of default validators are automatically populated.
    * Default `.create()` and `.update()` implementations are provided.

    The process of automatically determining a set of serializer fields
    based on the model fields is reasonably complex, but you almost certainly
    don't need to dig into the implementation.

    If the `ModelSerializer` class *doesn't* generate the set of fields that
    you need you should either declare the extra/differing fields explicitly on
    the serializer class, or simply use a `Serializer` class.
    """
    serializer_field_mapping = {
        models.AutoField: IntegerField,
        models.BigIntegerField: IntegerField,
        models.BooleanField: BooleanField,
        models.CharField: CharField,
        models.CommaSeparatedIntegerField: ListField,
        models.DateField: DateField,
        models.DateTimeField: DateTimeField,
        models.DecimalField: DecimalField,
        models.EmailField: EmailField,
        models.Field: CharField,
        models.FileField: CharField,
        models.FloatField: FloatField,
        models.ImageField: CharField,
        models.IntegerField: IntegerField,
        models.NullBooleanField: BooleanField,
        models.PositiveIntegerField: IntegerField,
        models.PositiveSmallIntegerField: IntegerField,
        models.SlugField: SlugField,
        models.SmallIntegerField: IntegerField,
        models.TextField: CharField,
        models.TimeField: TimeField,
        models.URLField: URLField,
        models.GenericIPAddressField: IPAddressField,
        models.FilePathField: CharField,
    }
    if ModelDurationField is not None:
        serializer_field_mapping[ModelDurationField] = DurationField
    serializer_related_field = PrimaryKeyRelatedField
    serializer_related_to_field = SlugRelatedField
    serializer_url_field = URLField
    serializer_choice_field = ChoiceField

    url_field_name = None
    create = None
    update = None

    def get_fields(self):
        """
        Return the dict of field names -> field instances that should be
        used for `self.fields` when instantiating the serializer.
        """
        if self.url_field_name is None:
            self.url_field_name = api_settings.URL_FIELD_NAME

        assert hasattr(self, 'Meta'), (
            'Class {filter_class} missing "Meta" attribute'.format(
                filter_class=self.__class__.__name__
            )
        )
        assert hasattr(self.Meta, 'model'), (
            'Class {filter_class} missing "Meta.model" attribute'.format(
                filter_class=self.__class__.__name__
            )
        )
        if model_meta.is_abstract_model(self.Meta.model):
            raise ValueError(
                'Cannot use ModelFilter with Abstract Models.'
            )

        declared_fields = copy.deepcopy(self._declared_fields)
        model = getattr(self.Meta, 'model')
        depth = getattr(self.Meta, 'depth', None)

        if depth:
            assert depth is None, "'depth' is not supported in filters."

        # Retrieve metadata about fields & relationships on the model class.
        info = model_meta.get_field_info(model)
        field_names = self.get_field_names(declared_fields, info)

        # Determine any extra field arguments and hidden fields that
        # should be included
        extra_kwargs = self.get_extra_kwargs()
        extra_kwargs, hidden_fields = self.get_uniqueness_extra_kwargs(
            field_names, declared_fields, extra_kwargs
        )

        # Determine the fields that should be included on the serializer.
        fields = OrderedDict()

        for field_name in field_names:
            # If the field is explicitly declared on the class then use that.
            if field_name in declared_fields:
                if field_name == 'slug_fk':
                    assert isinstance(declared_fields[field_name], Filter) is False, 'Nested filters are not supported'
                fields[field_name] = declared_fields[field_name]
                continue

            extra_field_kwargs = extra_kwargs.get(field_name, {})
            source = extra_field_kwargs.get('source', '*')
            if source == '*':
                source = field_name

            # Determine the serializer field class and keyword arguments.
            field_class, field_kwargs = self.build_field(
                source, info, model, depth
            )
            # Explicitly declaring each field as optional. `Meta.extra_kwargs` will be used to mark it as required
            field_kwargs['required'] = False
            # Include any kwargs defined in `Meta.extra_kwargs`
            field_kwargs = self.include_extra_kwargs(
                field_kwargs, extra_field_kwargs
            )

            # Create the serializer field.
            fields[field_name] = field_class(**field_kwargs)

        # Add in any hidden fields.
        fields.update(hidden_fields)
        return fields

    def get_field_names(self, declared_fields, info):
        """
        Returns the list of all field names that should be created when
        instantiating this serializer class. This is based on the default
        set of fields, but also takes into account the `Meta.fields` or
        `Meta.exclude` options if they have been specified.
        """
        fields = getattr(self.Meta, 'fields', None)
        exclude = getattr(self.Meta, 'exclude', None)

        if fields and fields != ALL_FIELDS and not isinstance(fields, (list, tuple)):
            raise TypeError(
                'The `fields` option must be a list or tuple or "__all__". '
                'Got %s.' % type(fields).__name__
            )

        if exclude and not isinstance(exclude, (list, tuple)):
            raise TypeError(
                'The `exclude` option must be a list or tuple. Got %s.' %
                type(exclude).__name__
            )

        assert not (fields and exclude), (
            "Cannot set both 'fields' and 'exclude' options on "
            "filter {filter_class}.".format(
                filter_class=self.__class__.__name__
            )
        )

        assert not (fields is None and exclude is None), (
            "Creating a ModelFilter without either the 'fields' attribute "
            "or the 'exclude' attribute is not allowed. Add an explicit fields = '__all__' to the "
            "{filter_class} filter.".format(
                filter_class=self.__class__.__name__
            ),
        )

        if fields == ALL_FIELDS:
            fields = None

        if fields is not None:
            # Ensure that all declared fields have also been included in the
            # `Meta.fields` option.

            # Do not require any fields that are declared in a parent class,
            # in order to allow serializer subclasses to only include
            # a subset of fields.
            required_field_names = set(declared_fields)
            for cls in self.__class__.__bases__:
                required_field_names -= set(getattr(cls, '_declared_fields', []))

            for field_name in required_field_names:
                assert field_name in fields, (
                    "The field '{field_name}' was declared on filter "
                    "{filter_class}, but has not been included in the "
                    "'fields' option.".format(
                        field_name=field_name,
                        filter_class=self.__class__.__name__
                    )
                )
            return fields

        # Use the default set of field names if `Meta.fields` is not specified.
        fields = self.get_default_field_names(declared_fields, info)

        if exclude is not None:
            # If `Meta.exclude` is included, then remove those fields.
            for field_name in exclude:
                assert field_name not in self._declared_fields, (
                    "Cannot both declare the field '{field_name}' and include "
                    "it in the {filter_class} 'exclude' option. Remove the "
                    "field or, if inherited from a parent filter, disable "
                    "with `{field_name} = None`."
                    .format(
                        field_name=field_name,
                        filter_class=self.__class__.__name__
                    )
                )

                assert field_name in fields, (
                    "The field '{field_name}' was included on filter "
                    "{filter_class} in the 'exclude' option, but does "
                    "not match any model field.".format(
                        field_name=field_name,
                        filter_class=self.__class__.__name__
                    )
                )
                fields.remove(field_name)

        for field_name, field in declared_fields.items():
            assert (
                hasattr(self, 'filter_{field_name}'.format(field_name=field_name)) or
                not super(ModelFilter, self).filter == self.filter or
                field.source
            ), (
                "The field '{field_name}' was included on filter but no filter method is defined. "
                "Define 'filter_{field_name}' or override filter method or define source in field '{field_name}'"
                "of the filter in {filter_class}".format(
                    field_name=field_name,
                    filter_class=self.__class__.__name__
                )
            )
        return fields
