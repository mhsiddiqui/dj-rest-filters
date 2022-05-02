from unittest import skipIf

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from model_bakery import baker
from rest_framework.pagination import PageNumberPagination
from rest_framework.test import APIRequestFactory

from djfilters import compat, filters
from djfilters.backend import DjFilterBackend

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
