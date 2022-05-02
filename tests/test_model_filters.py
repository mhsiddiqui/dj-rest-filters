from django.core import exceptions as django_exceptions
from model_bakery import baker
from rest_framework.test import APIRequestFactory

from djfilters import filters

from .base import BaseTestCase
from .models import (BooleanModel, NumberModel, RelatedIntIdModel,
                     RelatedSlugIdModel, TestAbstractModel, TextModel)

factory = APIRequestFactory()


class ModelFilterCoreTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        baker.make(RelatedSlugIdModel, _quantity=10)
        baker.make(RelatedIntIdModel, _quantity=10)
        baker.make(NumberModel, _quantity=10)
        slugs = RelatedSlugIdModel.objects.all().iterator()
        ids = RelatedIntIdModel.objects.all().iterator()
        baker.make(
            TextModel,
            slug_fk=slugs,
            int_fk=ids,
            _quantity=10
        )
        cls.data = TextModel.objects.all().order_by('-int_fk').values(
            'char', 'text', 'slug', 'slug_fk', 'int_fk',
            'slug_fk__text', 'int_fk__text', 'choice'
        )
        cls.numbers = NumberModel.objects.all().values()

    def test_model_filter_without_fields(self):
        class Filter(filters.ModelFilter):
            class Meta:
                model = BooleanModel

        message = """
        ("Creating a ModelFilter without either the \'fields\' attribute or the \'exclude\' attribute is not allowed. Add an explicit fields = \'__all__\' to the Filter filter.",)
        """  # noqa: E501
        self.validation_error(
            queryset=BooleanModel.objects.all(),
            filter_class=Filter,
            message=message,
            exception=AssertionError
        )

    def test_model_filter_with_invalid_fields(self):
        class Filter(filters.ModelFilter):
            class Meta:
                model = BooleanModel
                fields = 'invalid_field'

        self.validation_error(
            queryset=BooleanModel.objects.all(),
            filter_class=Filter,
            message='The `fields` option must be a list or tuple or "__all__". Got str.',
            exception=TypeError
        )

    def test_model_filter_with_invalid_exclude(self):
        class Filter(filters.ModelFilter):
            class Meta:
                model = BooleanModel
                exclude = 'invalid_field'

        self.validation_error(
            queryset=BooleanModel.objects.all(),
            filter_class=Filter,
            message='The `exclude` option must be a list or tuple. Got str',
            exception=TypeError
        )

    def test_model_filter_with_exclude_and_fields(self):
        class Filter(filters.ModelFilter):
            class Meta:
                model = TextModel
                exclude = ('text',)
                fields = ('char', 'slug')

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message="Cannot set both 'fields' and 'exclude' options on filter Filter.",
            exception=AssertionError
        )

    def test_model_filter_with_extra_field_not_included(self):
        class Filter(filters.ModelFilter):
            another = filters.CharField(source='text')

            class Meta:
                model = TextModel
                fields = ('char', 'slug')

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message="The field 'another' was declared on filter Filter, but has not been included in the 'fields' option.",
            exception=AssertionError
        )

    def test_model_filter_with_extra_field_excluded(self):
        class Filter(filters.ModelFilter):
            another = filters.CharField(source='text')

            class Meta:
                model = TextModel
                exclude = ('another',)

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message="Cannot both declare the field 'another' and include it in the Filter 'exclude' option. Remove the field or, if inherited from a parent filter, disable with `another = None`.",  # noqa: E501
            exception=AssertionError
        )

    def test_model_filter_with_field_not_in_model(self):
        class Filter(filters.ModelFilter):

            class Meta:
                model = TextModel
                fields = ('another', 'char')

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message="Field name `another` is not valid for model `TextModel`.",
            exception=django_exceptions.ImproperlyConfigured
        )

    def test_model_filter_with_exclude_not_in_model(self):
        class Filter(filters.ModelFilter):

            class Meta:
                model = TextModel
                exclude = ('another',)

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message="The field 'another' was included on filter Filter in the 'exclude' option, but does not match any model field.",
            exception=AssertionError
        )

    def test_model_filter_with_extra_field_no_filter_method_or_source(self):
        class Filter(filters.ModelFilter):
            another = filters.CharField()

            class Meta:
                model = TextModel
                fields = '__all__'

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message="The field 'another' was included on filter but no filter method is defined. Define 'filter_another' or override filter method or define source in field 'another'of the filter in Filter",  # noqa: E501
            exception=AssertionError
        )

    def test_model_filter_with_no_meta(self):
        class Filter(filters.ModelFilter):
            another = filters.CharField()

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message='Class Filter missing "Meta" attribute',
            exception=AssertionError
        )

    def test_model_filter_with_no_model(self):
        class Filter(filters.ModelFilter):
            another = filters.CharField()

            class Meta:
                fields = ('another',)

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message='Class Filter missing "Meta.model" attribute',
            exception=AssertionError
        )

    def test_model_filter_with_abstract_model(self):
        class Filter(filters.ModelFilter):

            class Meta:
                model = TestAbstractModel
                fields = '__all__'

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message='Cannot use ModelFilter with Abstract Models.',
            exception=ValueError
        )

    def test_model_filter_with_depth(self):
        class RelatedSlugIdModelFilter(filters.ModelFilter):
            class Meta:
                model = RelatedSlugIdModel
                fields = '__all__'

        class Filter(filters.ModelFilter):
            slug_fk = RelatedSlugIdModelFilter()

            class Meta:
                model = TextModel
                fields = '__all__'
                depth = 1

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message="'depth' is not supported in filters.",
            exception=AssertionError
        )

    def test_model_filter_with_nested_filters(self):
        class RelatedSlugIdModelFilter(filters.ModelFilter):
            class Meta:
                model = RelatedSlugIdModel
                fields = '__all__'

        class Filter(filters.ModelFilter):
            slug_fk = RelatedSlugIdModelFilter(required=False)

            class Meta:
                model = TextModel
                fields = '__all__'

            def filter_slug_fk(self, qs, value):
                return qs

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message="Nested filters are not supported",
            exception=AssertionError
        )

    def test_required_field(self):
        class Filter(filters.ModelFilter):
            class Meta:
                model = TextModel
                fields = ('char',)
                extra_kwargs = {
                    'char': {'required': True}
                }

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message="{'char': [ErrorDetail(string='This field is required.', code='required')]}"
        )

    def test_maximum_length_error(self):
        class Filter(filters.ModelFilter):
            class Meta:
                model = TextModel
                fields = ('char',)

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            query={'char': '{}-extra'.format(self.data[0].get('char'))},
            message="{'char': [ErrorDetail(string='Ensure this field has no more than 100 characters.', code='max_length')]}"
        )

    def test_with_valid_query(self):
        class Filter(filters.ModelFilter):
            class Meta:
                model = TextModel
                fields = ('char',)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'char': self.data[0].get('char')}
        )
        self.assertEqual(self.data[0].get('char'), filtered_queryset.first().char)

    def test_with_valid_extra_field_and_source(self):
        class Filter(filters.ModelFilter):
            char = filters.CharField(source='text')

            class Meta:
                model = TextModel
                fields = ('char',)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'char': self.data[0].get('text')}
        )
        self.assertEqual(self.data[0].get('text'), filtered_queryset.first().text)

    def test_with_valid_extra_exclude(self):
        class Filter(filters.ModelFilter):

            class Meta:
                model = TextModel
                exclude = ('char',)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'char': self.data[0].get('char')}
        )
        self.assertTrue(filtered_queryset.count() > 1)

    def test_with_field_type_validation(self):
        class Filter(filters.ModelFilter):

            class Meta:
                model = NumberModel
                exclude = ('float',)

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            query={'number': 'invalid-number'},
            message="{'number': [ErrorDetail(string='A valid integer is required.', code='invalid')]}"
        )

    def test_with_invalid_choices(self):
        class Filter(filters.ModelFilter):

            class Meta:
                model = TextModel
                fields = '__all__'

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            query={'choice': 'i'},
            message='{\'choice\': [ErrorDetail(string=\'"i" is not a valid choice.\', code=\'invalid_choice\')]}'
        )

    def test_with_valid_choices(self):
        class Filter(filters.ModelFilter):

            class Meta:
                model = TextModel
                fields = '__all__'

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'choice': self.data[0].get('choice')}
        )
        self.assertEqual(filtered_queryset.first().choice, request.cleaned_args.get('choice'))

    def test_with_custom_validation_message(self):
        class Filter(filters.ModelFilter):

            class Meta:
                model = TextModel
                fields = '__all__'

            def validate_char(self, char):
                if len(char) < 10:
                    raise filters.ValidationError('Custom validation error')
                return char

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            query={'char': 'Lorem'},
            message="'Custom validation error'"
        )


class ModelForeignKeyTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        baker.make(RelatedSlugIdModel, _quantity=10)
        baker.make(RelatedIntIdModel, _quantity=10)
        slugs = RelatedSlugIdModel.objects.all().iterator()
        ids = RelatedIntIdModel.objects.all().iterator()
        baker.make(
            TextModel,
            slug_fk=slugs,
            int_fk=ids,
            _quantity=10
        )
        cls.data = TextModel.objects.all().order_by('-int_fk').values(
            'char', 'text', 'slug', 'slug_fk', 'int_fk',
            'slug_fk__text', 'int_fk__text'
        )

    def test_int_foreign_key(self):
        class Filter(filters.ModelFilter):
            class Meta:
                model = TextModel
                fields = ('slug_fk', 'int_fk')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'int_fk': self.data[0].get('int_fk')}
        )
        self.assertEqual(self.data[0].get('int_fk'), filtered_queryset.first().int_fk_id)

    def test_slug_foreign_key(self):
        class Filter(filters.ModelFilter):
            class Meta:
                model = TextModel
                fields = ('slug_fk', 'int_fk')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'slug_fk': self.data[0].get('slug_fk')}
        )
        self.assertEqual(self.data[0].get('slug_fk'), filtered_queryset.first().slug_fk_id)

    def test_with_source_non_id_field(self):
        class Filter(filters.ModelFilter):
            slug_text = filters.CharField(source='slug_fk.text')

            class Meta:
                model = TextModel
                fields = ('slug_text',)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'slug_text': self.data[0].get('slug_fk__text')}
        )
        self.assertEqual(self.data[0].get('slug_fk__text'), filtered_queryset.first().slug_fk.text)

    def test_with_source_id_field(self):
        class Filter(filters.ModelFilter):
            slug_id = filters.CharField(source='slug_fk.id')

            class Meta:
                model = TextModel
                fields = ('slug_id',)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'slug_id': self.data[0].get('slug_fk')}
        )
        self.assertEqual(self.data[0].get('slug_fk'), filtered_queryset.first().slug_fk_id)

    def test_with_foreignkey_does_not_exist(self):
        class Filter(filters.ModelFilter):

            class Meta:
                model = TextModel
                fields = ('int_fk',)

        number = max([d.get('int_fk') for d in self.data])
        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            query={'int_fk': number + 1},
            message="{'int_fk': [ErrorDetail(string='Invalid pk \"11\" - object does not exist.', code='does_not_exist')]}"
        )
