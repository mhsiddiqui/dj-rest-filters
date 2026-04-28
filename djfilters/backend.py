from __future__ import absolute_import

from rest_framework import serializers
from rest_framework.renderers import HTMLFormRenderer

from . import compat, filters

_OPENAPI_TYPE_MAP = {
    filters.IntegerField: ('integer', None),
    filters.FloatField: ('number', 'float'),
    filters.DecimalField: ('number', 'double'),
    filters.BooleanField: ('boolean', None),
    filters.DateField: ('string', 'date'),
    filters.DateTimeField: ('string', 'date-time'),
    filters.TimeField: ('string', 'time'),
    filters.DurationField: ('string', 'duration'),
    filters.EmailField: ('string', 'email'),
    filters.URLField: ('string', 'uri'),
    filters.PrimaryKeyRelatedField: ('integer', None),
}


class DjFilterBackend(object):

    def filter_queryset(self, request, queryset, view):
        filterset = self.get_filterset(request, queryset, view)
        if filterset is None:
            return queryset

        if not filterset.is_valid():
            raise serializers.ValidationError(filterset.errors)
        request.cleaned_args = filterset.validated_data
        if queryset is None or queryset == [] or queryset == '':
            return queryset
        return filterset.filter(filterset.validated_data)

    def get_filterset_class(self, view):
        """
        Return the `FilterSet` class used to filter the queryset.
        """
        return getattr(view, 'filter_class', None)

    def get_filterset_kwargs(self, request, queryset, view):
        context = {'request': request}
        filter_context = getattr(view, 'get_filter_context', None)
        if filter_context:
            context.update(filter_context())
        return {
            'data': request.query_params,
            'queryset': queryset,
            'context': context,
        }

    def get_filterset(self, request, queryset, view):
        filterset_class = self.get_filterset_class(view)
        if filterset_class is None:
            return None
        return filterset_class(
            **self.get_filterset_kwargs(request, queryset, view)
        )

    def to_html(self, request, queryset, view):
        filter_class = self.get_filterset(request, queryset, view)
        filter_class.is_valid()
        form_renderer = HTMLFormRenderer()
        form_renderer.default_style.mapping[filters.BooleanField] = {
            'base_template': 'checkbox.html'
        }
        form_renderer.default_style.mapping[filters.ListField] = {
            'base_template': 'textarea.html'
        }
        return form_renderer.render(
            filter_class.data, {},
            {'style': {'template_pack': 'djfilters/vertical'}}
        )

    def get_coreschema_field(self, field):
        help_text = str(field.extra.get('help_text', ''))
        extra_kwargs = {}
        if isinstance(
            field, (
                filters.IntegerField,
                filters.FloatField,
                filters.DecimalField
            )
        ):
            field_cls = compat.coreschema.Integer
        elif isinstance(field, filters.BooleanField):
            field_cls = compat.coreschema.Boolean
        elif isinstance(field, filters.ListField):
            field_cls = compat.coreschema.Array
            help_text = (
                field.extra.get('help_text', '') or
                "values separated by a '{separator}'".format(
                    separator=getattr(field, 'separator', ',')
                )
            )
        elif isinstance(field, filters.ChoiceField):
            field_cls = compat.coreschema.Enum
            extra_kwargs['enum'] = [c[0] for c in field.extra.get('choices', [])]
        elif isinstance(field, filters.PrimaryKeyRelatedField):
            field_cls = compat.coreschema.Integer
        else:
            field_cls = compat.coreschema.String
        return field_cls(description=help_text, **extra_kwargs)

    def get_schema_fields(self, view):
        # This is not compatible with widgets where the
        # query param differs from the filter's attribute name.
        # Notably, this includes `MultiWidget`, where query
        # params will be of the format `<name>_0`, `<name>_1`, etc...
        assert compat.coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert compat.coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'

        filterset_class = self.get_filterset_class(view)
        if filterset_class is None:
            return []

        return [
            compat.coreapi.Field(
                name=field_name,
                required=field.required,
                description=field.help_text,
                location='query',
                schema=self.get_coreschema_field(field)
            ) for field_name, field in filterset_class().get_fields().items()
        ]

    def get_schema_operation_parameters(self, view):
        filterset_class = self.get_filterset_class(view)
        if filterset_class is None:
            return []

        parameters = []
        for field_name, field in filterset_class().get_fields().items():
            parameter = {
                'name': field_name,
                'required': bool(field.required),
                'in': 'query',
                'description': self._field_description(field, field_name),
                'schema': self._openapi_schema_for(field),
            }
            parameters.append(parameter)
        return parameters

    def _field_description(self, field, field_name):
        if getattr(field, 'help_text', None):
            return str(field.help_text)
        if field.label is not None:
            return str(field.label)
        return field_name

    def _openapi_schema_for(self, field):
        if isinstance(field, filters.ListField):
            child = getattr(field, 'child', None)
            items = self._openapi_schema_for(child) if child is not None else {'type': 'string'}
            schema = {'type': 'array', 'items': items}
            if isinstance(field, filters.RangeField):
                schema['minItems'] = 2
                schema['maxItems'] = 2
            return schema

        otype, fmt = 'string', None
        for cls, (mapped_type, mapped_fmt) in _OPENAPI_TYPE_MAP.items():
            if isinstance(field, cls):
                otype, fmt = mapped_type, mapped_fmt
                break

        schema = {'type': otype}
        if fmt:
            schema['format'] = fmt
        if field.extra and 'choices' in field.extra:
            schema['enum'] = [c[0] for c in field.extra['choices']]
        return schema
