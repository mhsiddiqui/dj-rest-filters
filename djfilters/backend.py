from __future__ import absolute_import

from rest_framework import serializers
from rest_framework.renderers import HTMLFormRenderer

from . import compat, filters


class DjFilterBackend(object):

    def filter_queryset(self, request, queryset, view):
        queryset = [] if queryset is None else queryset
        filterset = self.get_filterset(request, queryset, view)
        if filterset is None:
            return queryset

        if not filterset.is_valid():
            if view.pagination_class and view.paginator:
                view.paginator.get_results = lambda data: data
            raise serializers.ValidationError(filterset.errors)
        request.cleaned_args = filterset.validated_data
        if queryset not in [None, [], '']:
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
        form_renderer.default_style.mapping[filters.DictField] = {
            'base_template': 'textarea.html'
        }
        return form_renderer.render(
            filter_class.data, {},
            {'style': {'template_pack': 'djfilters/vertical'}}
        )

    def get_coreschema_field(self, field):
        help_text = str(field.extra.get('help_text', ''))
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
        elif isinstance(field, filters.PrimaryKeyRelatedField):
            field_cls = compat.coreschema.Integer
        else:
            field_cls = compat.coreschema.String
        return field_cls(description=help_text)

    def get_schema_fields(self, view):
        # This is not compatible with widgets where the
        # query param differs from the filter's attribute name.
        # Notably, this includes `MultiWidget`, where query
        # params will be of the format `<name>_0`, `<name>_1`, etc...
        assert compat.coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert compat.coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'

        filterset_class = self.get_filterset_class(view)()

        return [] if not filterset_class else [
            compat.coreapi.Field(
                name=field_name,
                required=field.required,
                description=field.help_text,
                location='query',
                schema=self.get_coreschema_field(field)
            ) for field_name, field in filterset_class.get_fields().items()
        ]

    def get_schema_operation_parameters(self, view):
        filterset_class = self.get_filterset_class(view)()

        if not filterset_class:
            return []

        parameters = []
        for field_name, field in filterset_class.get_fields().items():
            parameter = {
                'name': field_name,
                'required': field.required,
                'in': 'query',
                'description': (
                    field.label if field.label is not None else field_name
                ),
                'schema': {
                    'type': 'string',
                },
            }
            if field.extra and 'choices' in field.extra:
                parameter['schema']['enum'] = [
                    c[0] for c in field.extra['choices']
                ]
            parameters.append(parameter)
        return parameters
