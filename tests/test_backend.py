from unittest import skipIf

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from model_bakery import baker
from rest_framework.pagination import PageNumberPagination
from rest_framework.test import APIRequestFactory

from djfilters import compat, filters
from djfilters.backend import DjFilterBackend

try:
    import drf_spectacular  # noqa: F401
    HAS_SPECTACULAR = True
except ImportError:
    HAS_SPECTACULAR = False

try:
    import drf_yasg  # noqa: F401
    HAS_YASG = True
except ImportError:
    HAS_YASG = False

from .base import BaseTestCase
from .filters import (NoFieldFilter, TextFieldFilter, TextModelFilter,
                      get_model_filter, get_simple_filter)
from .models import TextModel
from .views import get_view

factory = APIRequestFactory()


class FilterQuerysetBackendTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        text_model = baker.make(TextModel, _quantity=10)
        cls.search_query = {
            'text': text_model[0].text,
            'char': text_model[0].char,
            'id': text_model[0].id
        }

    def test_filter_queryset_with_no_query(self):
        request, view, filtered_queryset = self.filter_query(
            filter_class=NoFieldFilter,
        )
        self.assertEqual(filtered_queryset, view.queryset)

    def test_filter_queryset_with_query(self):
        request, view, filtered_queryset = self.filter_query(
            filter_class=get_simple_filter(
                fields={
                    'text': filters.CharField(max_length=len(self.search_query.get('text')), required=False)
                }
            ),
            queryset=TextModel.objects.all(),
            query={'text': self.search_query.get('text')}
        )
        self.assertEqual(filtered_queryset.first().id, self.search_query.get('id'))

    def test_filter_queryset_merges_view_filter_context(self):
        captured = {}

        class ContextAwareFilter(filters.Filter):
            text = filters.CharField(required=False)

            def __init__(self, *args, **kwargs):
                captured['context'] = kwargs.get('context', {})
                super(ContextAwareFilter, self).__init__(*args, **kwargs)

        view = get_view(filter_class=ContextAwareFilter, queryset=TextModel.objects.all())
        view.get_filter_context = lambda: {'extra': 'sentinel'}

        request = factory.get('/', data={})
        request.query_params = request.GET
        DjFilterBackend().filter_queryset(request, view.queryset, view)

        self.assertEqual(captured['context'].get('extra'), 'sentinel')


class ToHtmlBackendTestCase(TestCase):
    def test_to_html_renders_form(self):
        class FormFilter(filters.Filter):
            text = filters.CharField(required=False)
            active = filters.BooleanField(required=False)
            tags = filters.ListField(child=filters.CharField(), required=False)
            role = filters.ChoiceField(choices=[('a', 'A'), ('b', 'B')], required=False)

        view = get_view(filter_class=FormFilter, queryset=TextModel.objects.all())
        request = factory.get('/', data={})
        request.query_params = request.GET

        rendered = DjFilterBackend().to_html(request, view.queryset, view)
        self.assertIsInstance(rendered, str)
        self.assertIn('<', rendered)


class ModelFilterQuerysetBackendTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        text_model = baker.make(TextModel, _quantity=10)
        cls.search_query = {
            'text': text_model[0].text,
            'char': text_model[0].char
        }

    def test_filter_queryset_with_no_filter(self):
        request, view, filtered_queryset = self.filter_query(
            queryset=TextModel.objects.all()
        )
        self.assertEqual(filtered_queryset, view.queryset)

    def test_model_filter_queryset_with_no_queryset(self):
        request, view, filtered_queryset = self.filter_query(
            filter_class=TextModelFilter,
            queryset=TextModel.objects.all(),
            query={'char': 'Char value'}
        )
        self.assertEqual(
            list(filtered_queryset.values_list('id', flat=True)),
            list(view.queryset.values_list('id', flat=True))
        )

    def test_filter_with_invalid_data(self):
        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=TextFieldFilter,
            query={'text': 'Text' * 3},
            message="{'text': [ErrorDetail(string='Ensure this field has no more than 10 characters.', code='max_length')]}"
        )

    def test_filter_with_valid_data(self):
        request, view, filtered_queryset = self.filter_query(
            queryset=TextModel.objects.all(),
            filter_class=TextModelFilter,
            pagination_class=PageNumberPagination,
            query={'text': self.search_query.get('text')}
        )
        self.assertEqual(filtered_queryset.first().text, self.search_query.get('text'))


@skipIf(compat.coreapi is None, 'coreapi must be installed')
class GetSchemaFieldsTests(BaseTestCase):

    def test_fields_with_model_filter(self):
        view = get_view(
            filter_class=get_model_filter(
                TextModelFilter,
                fields=['id', 'char', 'text']
            )
        )
        fields = self.backend.get_schema_fields(view)
        fields = [f.name for f in fields]
        self.assertEqual(fields, ['id', 'char', 'text'])

    def test_malformed_model_filter(self):
        view = get_view(
            filter_class=get_model_filter(
                TextModelFilter,
                fields=['non_existent']
            )
        )
        msg = "Field name `non_existent` is not valid for model `{model}`".format(model=TextModel.__name__)
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.backend.get_schema_fields(view)

    def test_schema_with_model_filter(self):
        view = get_view(
            filter_class=get_model_filter(
                TextModelFilter,
                fields=['id', 'char', 'text']
            )
        )

        fields = self.backend.get_schema_fields(view)
        schemas = [f.schema for f in fields]
        fields = [f.name for f in fields]

        self.assertEqual(fields, ['id', 'char', 'text'])
        self.assertIsInstance(schemas[0], compat.coreschema.Integer)
        self.assertIsInstance(schemas[1], compat.coreschema.String)
        self.assertIsInstance(schemas[2], compat.coreschema.String)

    def test_field_required_model_filter(self):
        view = get_view(
            filter_class=get_model_filter(
                TextModelFilter,
                fields=['id', 'char', 'text'],
                extra_kwargs={
                    'char': {'required': True}
                }
            )
        )

        fields = self.backend.get_schema_fields(view)
        required = [f.required for f in fields]
        fields = [f.name for f in fields]

        self.assertEqual(fields, ['id', 'char', 'text'])
        self.assertFalse(required[0])
        self.assertTrue(required[1])
        self.assertFalse(required[2])

    def test_get_schema_fields_returns_empty_when_no_filter_class(self):
        view = get_view()
        self.assertEqual(self.backend.get_schema_fields(view), [])

    def test_coreschema_field_types(self):
        class TypedFilter(filters.Filter):
            count = filters.IntegerField()
            score = filters.FloatField()
            price = filters.DecimalField(max_digits=10, decimal_places=2)
            active = filters.BooleanField()
            tags = filters.ListField(child=filters.CharField())
            role = filters.ChoiceField(choices=[('a', 'A'), ('b', 'B')])
            related = filters.PrimaryKeyRelatedField(queryset=TextModel.objects.all())
            name = filters.CharField()

        view = get_view(filter_class=TypedFilter)
        schemas = {f.name: f.schema for f in self.backend.get_schema_fields(view)}

        self.assertIsInstance(schemas['count'], compat.coreschema.Integer)
        self.assertIsInstance(schemas['score'], compat.coreschema.Integer)
        self.assertIsInstance(schemas['price'], compat.coreschema.Integer)
        self.assertIsInstance(schemas['active'], compat.coreschema.Boolean)
        self.assertIsInstance(schemas['tags'], compat.coreschema.Array)
        self.assertIn("separated by", schemas['tags'].description)
        self.assertIsInstance(schemas['role'], compat.coreschema.Enum)
        self.assertIsInstance(schemas['related'], compat.coreschema.Integer)
        self.assertIsInstance(schemas['name'], compat.coreschema.String)

    def test_coreschema_listfield_uses_provided_help_text(self):
        class HelpfulFilter(filters.Filter):
            tags = filters.ListField(child=filters.CharField(), help_text='Provided help')

        view = get_view(filter_class=HelpfulFilter)
        schemas = {f.name: f.schema for f in self.backend.get_schema_fields(view)}
        self.assertEqual(schemas['tags'].description, 'Provided help')


class GetSchemaOperationParametersTests(TestCase):
    def setUp(self):
        self.backend = DjFilterBackend()

    def test_get_operation_parameters_with_filterset_fields_list(self):
        view = get_view(
            filter_class=get_model_filter(
                TextModelFilter,
                fields=['id', 'char', 'text'],
                extra_kwargs={
                    'char': {'required': True}
                }
            )
        )
        fields = self.backend.get_schema_operation_parameters(view)
        fields = [f['name'] for f in fields]

        self.assertEqual(fields, ['id', 'char', 'text'])

    def test_get_operation_parameters_with_filterset_fields_list_with_choices(self):
        view = get_view(
            filter_class=get_model_filter(
                TextModelFilter,
                fields=['text']
            )
        )
        fields = self.backend.get_schema_operation_parameters(view)

        self.assertEqual(
            fields,
            [{
                'name': 'text',
                'required': False,
                'in': 'query',
                'description': 'text',
                'schema': {
                    'type': 'string'
                },
            }]
        )

    def test_get_operation_parameters_returns_empty_when_no_filter_class(self):
        view = get_view()
        self.assertEqual(self.backend.get_schema_operation_parameters(view), [])

    def test_get_operation_parameters_maps_field_types(self):
        class TypedFilter(filters.Filter):
            name = filters.CharField()
            age = filters.IntegerField()
            score = filters.FloatField()
            price = filters.DecimalField(max_digits=10, decimal_places=2)
            active = filters.BooleanField()
            born = filters.DateField()
            seen_at = filters.DateTimeField()
            email = filters.EmailField()
            site = filters.URLField()
            role = filters.ChoiceField(choices=[('a', 'A'), ('b', 'B')])
            tags = filters.ListField(child=filters.CharField())
            window = filters.RangeField(child=filters.IntegerField())

        view = get_view(filter_class=TypedFilter)
        params = {p['name']: p['schema'] for p in self.backend.get_schema_operation_parameters(view)}

        self.assertEqual(params['name'], {'type': 'string'})
        self.assertEqual(params['age'], {'type': 'integer'})
        self.assertEqual(params['score'], {'type': 'number', 'format': 'float'})
        self.assertEqual(params['price'], {'type': 'number', 'format': 'double'})
        self.assertEqual(params['active'], {'type': 'boolean'})
        self.assertEqual(params['born'], {'type': 'string', 'format': 'date'})
        self.assertEqual(params['seen_at'], {'type': 'string', 'format': 'date-time'})
        self.assertEqual(params['email'], {'type': 'string', 'format': 'email'})
        self.assertEqual(params['site'], {'type': 'string', 'format': 'uri'})
        self.assertEqual(params['role'], {'type': 'string', 'enum': ['a', 'b']})
        self.assertEqual(params['tags'], {'type': 'array', 'items': {'type': 'string'}})
        self.assertEqual(
            params['window'],
            {'type': 'array', 'items': {'type': 'integer'}, 'minItems': 2, 'maxItems': 2},
        )

    def test_get_operation_parameters_uses_help_text_and_label(self):
        class DescribedFilter(filters.Filter):
            with_help = filters.CharField(help_text='Helpful text')
            with_label = filters.CharField(label='Pretty Label')
            plain = filters.CharField()

        view = get_view(filter_class=DescribedFilter)
        descriptions = {
            p['name']: p['description']
            for p in self.backend.get_schema_operation_parameters(view)
        }

        self.assertEqual(descriptions['with_help'], 'Helpful text')
        self.assertEqual(descriptions['with_label'], 'Pretty Label')
        self.assertEqual(descriptions['plain'], 'plain')


class _SwaggerIntegrationFilter(filters.Filter):
    name = filters.CharField(required=False)
    age = filters.IntegerField(required=False)
    active = filters.BooleanField(required=False)
    role = filters.ChoiceField(choices=[('a', 'A'), ('b', 'B')], required=False)
    tags = filters.ListField(child=filters.CharField(), required=False)


def _build_demo_urlpatterns():
    from django.urls import path
    from rest_framework import generics
    from rest_framework import serializers as drf_serializers

    class _DemoSerializer(drf_serializers.Serializer):
        id = drf_serializers.IntegerField()

    class _DemoView(generics.ListAPIView):
        queryset = []
        serializer_class = _DemoSerializer
        filter_backends = [DjFilterBackend]
        filter_class = _SwaggerIntegrationFilter

    return [path('demo/', _DemoView.as_view(), name='swagger-demo')]


@skipIf(not HAS_SPECTACULAR, 'drf-spectacular must be installed')
@override_settings(REST_FRAMEWORK={
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
})
class DrfSpectacularIntegrationTests(TestCase):
    def test_schema_generation(self):
        from drf_spectacular.generators import SchemaGenerator

        schema = SchemaGenerator(patterns=_build_demo_urlpatterns()).get_schema(
            request=None, public=True
        )
        params = {p['name']: p for p in schema['paths']['/demo/']['get']['parameters']}

        self.assertEqual(params['age']['schema'], {'type': 'integer'})
        self.assertEqual(params['active']['schema'], {'type': 'boolean'})
        self.assertEqual(params['name']['schema'], {'type': 'string'})
        self.assertEqual(params['role']['schema'], {'type': 'string', 'enum': ['a', 'b']})
        self.assertEqual(
            params['tags']['schema'],
            {'type': 'array', 'items': {'type': 'string'}},
        )


@skipIf(not HAS_YASG, 'drf-yasg must be installed')
class DrfYasgIntegrationTests(TestCase):
    def test_schema_generation(self):
        from drf_yasg import openapi
        from drf_yasg.generators import OpenAPISchemaGenerator

        info = openapi.Info(title='t', default_version='v1')
        schema = OpenAPISchemaGenerator(
            info=info, patterns=_build_demo_urlpatterns()
        ).get_schema(request=None, public=True)
        params = {p['name']: dict(p) for p in schema['paths']['/demo/']['get']['parameters']}

        self.assertEqual(params['age']['type'], 'integer')
        self.assertEqual(params['active']['type'], 'boolean')
        self.assertEqual(params['name']['type'], 'string')
        self.assertEqual(params['role']['type'], 'string')
        self.assertEqual(params['role']['enum'], ['a', 'b'])
        self.assertEqual(params['tags']['type'], 'array')
