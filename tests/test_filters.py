import datetime
import random

from model_bakery import baker
from rest_framework.pagination import PageNumberPagination
from rest_framework.test import APIRequestFactory

from djfilters import filters
from tests.filters import BooleanFilter

from .base import BaseTestCase
from .models import (BooleanModel, DateFieldModel, EmailModel, IpModel,
                     NumberModel, RelatedSlugIdModel, TextModel, URLModel)

factory = APIRequestFactory()


class BooleanFilterTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        baker.make(BooleanModel, flag=True, _quantity=5)
        baker.make(BooleanModel, flag=False, _quantity=5)

    def test_boolean_field_filter_with_false(self):
        request, view, filtered_queryset = self.filter_query(
            queryset=BooleanModel.objects.all(),
            filter_class=BooleanFilter,
            query={'flag': False}
        )
        self.assertEqual(all(list(filtered_queryset.values_list('flag', flat=True))), False)

    def test_boolean_field_filter_with_true(self):
        request, view, filtered_queryset = self.filter_query(
            queryset=BooleanModel.objects.all(),
            filter_class=BooleanFilter,
            query={'flag': True}
        )
        self.assertEqual(all(list(filtered_queryset.values_list('flag', flat=True))), True)

    def test_boolean_field_filter_with_invalid(self):
        self.validation_error(
            queryset=BooleanModel.objects.all(),
            filter_class=BooleanFilter,
            query={'flag': 'an-invalid-value'},
            message="{'flag': [ErrorDetail(string='Must be a valid boolean.', code='invalid')]}"
        )

    def test_boolean_field_filter_without_queryset_and_invalid_value(self):
        self.validation_error(
            queryset=BooleanModel.objects.all(),
            filter_class=BooleanFilter,
            query={'flag': 'an-invalid-value'},
            message="{'flag': [ErrorDetail(string='Must be a valid boolean.', code='invalid')]}"
        )

    def test_boolean_field_filter_invalid_value_with_pagination(self):
        self.validation_error(
            queryset=BooleanModel.objects.all(),
            filter_class=BooleanFilter,
            pagination_class=PageNumberPagination,
            query={'flag': 'an-invalid-value'},
            message="{'flag': [ErrorDetail(string='Must be a valid boolean.', code='invalid')]}"
        )

    def test_boolean_field_filter_without_queryset_and_valid_value(self):
        request, view, filtered_queryset = self.filter_query(
            filter_class=BooleanFilter,
            query={'flag': True}
        )
        self.assertIsNone(filtered_queryset)


class CharFilterTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        baker.make(TextModel, char='Lorem Ipsum', _quantity=5)
        baker.make(TextModel, char='Neque porro', _quantity=5)

    def test_required_field_filter(self):
        class Filter(filters.Filter):
            char = filters.CharField(max_length=10, min_length=5, required=True)
        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            message="{'char': [ErrorDetail(string='This field is required.', code='required')]}"
        )

    def test_min_length_validation(self):
        class Filter(filters.Filter):
            char = filters.CharField(max_length=10, min_length=5)

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            query={'char': 'Nequ'},
            message="{'char': [ErrorDetail(string='Ensure this field has at least 5 characters.', code='min_length')]}"
        )

    def test_max_length_validation(self):
        class Filter(filters.Filter):
            char = filters.CharField(max_length=10, min_length=5)

        self.validation_error(
            queryset=TextModel.objects.all(),
            filter_class=Filter,
            query={'char': 'Lorem Ipsum Nequ'},
            message="{'char': [ErrorDetail(string='Ensure this field has no more than 10 characters.', code='max_length')]}"
        )

    def test_not_required_field(self):
        class Filter(filters.Filter):
            char = filters.CharField(max_length=10, min_length=5, required=False)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all()
        )
        self.assertEqual(list(view.queryset.values_list('id')), list(filtered_queryset.values_list('id')))

    def test_with_empty_query(self):
        class Filter(filters.Filter):
            char = filters.CharField(max_length=10, min_length=0, required=False)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'char': ''}
        )
        self.assertEqual(list(view.queryset.values_list('id')), list(filtered_queryset.values_list('id')))

    def test_with_valid_exact_query(self):
        class Filter(filters.Filter):
            char = filters.CharField(max_length=15, min_length=5)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'char': 'Lorem Ipsum'}
        )
        self.assertEqual(
            list(set(filtered_queryset.values_list('char', flat=True)))[0], 'Lorem Ipsum'
        )

    def test_with_valid_partial_insensitive_query(self):
        class Filter(filters.Filter):
            char = filters.CharField(max_length=15, min_length=5, lookup_expr='icontains')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'char': 'Lorem'}
        )
        self.assertTrue(
            all(['Lorem' in value for value in filtered_queryset.values_list('char', flat=True)])
        )

    def test_with_valid_partial_sensitive_query(self):
        class Filter(filters.Filter):
            char = filters.CharField(max_length=15, min_length=5, lookup_expr='contains')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'char': 'lorem'}
        )
        self.assertTrue(
            all(['lorem' in value.lower() for value in filtered_queryset.values_list('char', flat=True)])
        )

    def test_with_exclude_valid_query(self):
        class Filter(filters.Filter):
            char = filters.CharField(max_length=15, min_length=5, exclude=True)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'char': 'Lorem Ipsum'}
        )
        self.assertTrue(
            all(['Lorem Ipsum' != value for value in filtered_queryset.values_list('char', flat=True)])
        )

    def test_with_distinct_and_valid_query(self):
        class Filter(filters.Filter):
            char = filters.CharField(max_length=15, min_length=5, distinct=True)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'char': 'Lorem Ipsum'}
        )
        self.assertTrue(filtered_queryset.values_list('char', flat=True).count() == 1)
        self.assertEqual(filtered_queryset.first().char, 'Lorem Ipsum')

    def test_with_source(self):
        class Filter(filters.Filter):
            text = filters.CharField(max_length=15, min_length=5, source='char')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'text': 'Lorem Ipsum'}
        )
        self.assertEqual(
            list(set(filtered_queryset.values_list('char', flat=True)))[0], 'Lorem Ipsum'
        )

    def test_with_custom_filter(self):
        class Filter(filters.Filter):
            text = filters.CharField(max_length=15, min_length=5)

            def filter_text(self, queryset, value):
                return queryset.filter(char__icontains=value)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'text': 'Lorem Ipsum'}
        )
        self.assertEqual(
            list(set(filtered_queryset.values_list('char', flat=True)))[0], 'Lorem Ipsum'
        )

    def test_with_nullable_field(self):
        class Filter(filters.Filter):
            text = filters.CharField(max_length=15, min_length=5, allow_null=True)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=TextModel.objects.all(),
            query={'text': ''}
        )
        self.assertEqual(
            list(filtered_queryset.values_list('id', flat=True)), list(view.queryset.values_list('id', flat=True))
        )


class EmailFilterTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        baker.make(EmailModel, _quantity=10)
        cls.emails = EmailModel.objects.values_list('email', flat=True)

    def test_required_field_filter(self):
        class Filter(filters.Filter):
            email = filters.EmailField(max_length=50, min_length=20, required=True)

        self.validation_error(
            queryset=EmailModel.objects.all(),
            filter_class=Filter,
            message="{'email': [ErrorDetail(string='This field is required.', code='required')]}"
        )

    def test_with_invalid_email(self):
        class Filter(filters.Filter):
            email = filters.EmailField(max_length=50, min_length=10)

        self.validation_error(
            queryset=EmailModel.objects.all(),
            filter_class=Filter,
            query={'email': 'invalid_email_address'},
            message="{'email': [ErrorDetail(string='Enter a valid email address.', code='invalid')]}"
        )

    def test_min_length_validation(self):
        class Filter(filters.Filter):
            email = filters.EmailField(max_length=50, min_length=15)
        self.validation_error(
            queryset=EmailModel.objects.all(),
            filter_class=Filter,
            query={'email': 'abc@abc.com'},
            message="{'email': [ErrorDetail(string='Ensure this field has at least 15 characters.', code='min_length')]}"
        )

    def test_max_length_validation(self):
        class Filter(filters.Filter):
            email = filters.EmailField(max_length=20, min_length=10)

        self.validation_error(
            queryset=EmailModel.objects.all(),
            filter_class=Filter,
            query={'email': 'invalid_email_address@invalid_domain.com'},
            message="{'email': [ErrorDetail(string='Ensure this field has no more than 20 characters.', code='max_length')"
        )

    def test_not_required_field(self):
        class Filter(filters.Filter):
            email = filters.EmailField(max_length=20, min_length=10, required=False)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=EmailModel.objects.all(),
        )
        self.assertEqual(list(view.queryset.values_list('id')), list(filtered_queryset.values_list('id')))

    def test_with_valid_exact_query(self):
        class Filter(filters.Filter):
            email = filters.EmailField(max_length=len(self.emails[0]), min_length=10)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=EmailModel.objects.all(),
            query={'email': self.emails[0]}
        )

        self.assertEqual(
            list(set(filtered_queryset.values_list('email', flat=True)))[0], self.emails[0]
        )

    def test_with_exclude_valid_query(self):
        class Filter(filters.Filter):
            email = filters.EmailField(max_length=len(self.emails[0]), min_length=10, exclude=True)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=EmailModel.objects.all(),
            query={'email': self.emails[0]}
        )
        self.assertTrue(
            all([self.emails[0] != value for value in filtered_queryset.values_list('email', flat=True)])
        )


class SlugFilterTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        baker.make(RelatedSlugIdModel, _quantity=10)
        cls.data = RelatedSlugIdModel.objects.values_list('id', flat=True)

    def test_with_invalid_slug(self):
        class Filter(filters.Filter):
            id = filters.SlugField(max_length=len(self.data[0]), min_length=10)
        msg = """
        {'id': [ErrorDetail(string='Enter a valid "slug" consisting of letters, numbers, underscores or hyphens.', code='invalid')]}
        """
        self.validation_error(
            queryset=RelatedSlugIdModel.objects.all(),
            filter_class=Filter,
            query={'id': 'invalid slug with space'},
            message=msg
        )

    def test_with_valid_exact_slug(self):
        class Filter(filters.Filter):
            id = filters.SlugField(max_length=len(self.data[0]), min_length=10)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=RelatedSlugIdModel.objects.all(),
            query={'id': self.data[0]}
        )
        self.assertTrue(filtered_queryset.first().id == self.data[0])

    def test_with_valid_partial_slug(self):
        class Filter(filters.Filter):
            id = filters.SlugField(max_length=len(self.data[0]), min_length=10, lookup_expr='icontains')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=RelatedSlugIdModel.objects.all(),
            query={'id': self.data[0][:len(self.data[0]) // 2]}
        )
        self.assertTrue(
            all([request.cleaned_args.get('id') in value.id for value in filtered_queryset])
        )

    def test_with_exclude(self):
        class Filter(filters.Filter):
            id = filters.SlugField(max_length=len(self.data[0]), min_length=10, exclude=True)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=RelatedSlugIdModel.objects.all(),
            query={'id': self.data[0]}
        )
        self.assertTrue(
            all([request.cleaned_args.get('id') != value.id for value in filtered_queryset])
        )


class URLFilterTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        baker.make(URLModel, _quantity=10)
        cls.urls = URLModel.objects.values_list('url', flat=True)

    def test_with_invalid_url(self):
        class Filter(filters.Filter):
            url = filters.URLField(max_length=len(self.urls[0]), min_length=10)

        self.validation_error(
            queryset=RelatedSlugIdModel.objects.all(),
            filter_class=Filter,
            query={'url': 'invalid url'},
            message="{'url': [ErrorDetail(string='Enter a valid URL.', code='invalid')]}"
        )

    def test_with_valid_url(self):
        class Filter(filters.Filter):
            url = filters.URLField(max_length=len(self.urls[0]), min_length=10)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=URLModel.objects.all(),
            query={'url': self.urls[0]}
        )
        self.assertTrue(
            all([request.cleaned_args.get('url') in value.url for value in filtered_queryset])
        )


class IPFilterTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        baker.make(IpModel, _quantity=10)
        cls.ips = IpModel.objects.values_list('ip', flat=True)

    def test_with_invalid_ip(self):
        class Filter(filters.Filter):
            ip = filters.IPAddressField(max_length=len(self.ips[0]), min_length=10)

        self.validation_error(
            queryset=IpModel.objects.all(),
            filter_class=Filter,
            query={'ip': 'invalid ip'},
            message="{'ip': [ErrorDetail(string='Enter a valid IPv4 or IPv6 address.', code='invalid')]}"
        )

    def test_with_valid_url(self):
        class Filter(filters.Filter):
            ip = filters.IPAddressField(max_length=len(self.ips[0]), min_length=10)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=IpModel.objects.all(),
            query={'ip': self.ips[0]}
        )
        self.assertTrue(
            all([request.cleaned_args.get('ip') in value.ip for value in filtered_queryset])
        )


class NumberTestCases(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        def get_random_no():
            return random.randint(1, 999)

        baker.make(
            NumberModel,
            number=get_random_no,
            float=get_random_no,
            decimal=get_random_no,
            _quantity=100
        )
        cls.number = NumberModel.objects.values_list('number', flat=True)
        cls.float = NumberModel.objects.values_list('float', flat=True)
        cls.decimal = NumberModel.objects.values_list('decimal', flat=True)

    def test_with_invalid_value_type(self):
        class Filter(filters.Filter):
            number = filters.IntegerField(max_value=100, min_value=10)
            float = filters.FloatField(max_value=100, min_value=10)

        msg = """
        {'number': [ErrorDetail(string='A valid integer is required.', code='invalid')], 'float': [ErrorDetail(string='A valid number is required.', code='invalid')]}
        """  # noqa: E501
        self.validation_error(
            queryset=NumberModel.objects.all(),
            filter_class=Filter,
            query={'number': 'invalid number', 'float': 'invalid float'},
            message=msg
        )

    def test_with_invalid_decimal_type(self):
        class Filter(filters.Filter):
            decimal = filters.DecimalField(max_digits=5, decimal_places=2)

        msg = "{'decimal': [ErrorDetail(string='A valid number is required.', code='invalid')]}"
        self.validation_error(
            queryset=NumberModel.objects.all(),
            filter_class=Filter,
            query={'decimal': 'invalid number'},
            message=msg
        )

    def test_with_valid_decimal_type(self):
        class Filter(filters.Filter):
            decimal = filters.DecimalField(max_digits=5, decimal_places=2)

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={'decimal': self.decimal[0]}
        )
        self.assertTrue(
            all([request.cleaned_args.get('decimal') == value.decimal for value in filtered_queryset])
        )

    def test_with_invalid_min_and_max_value(self):
        class Filter(filters.Filter):
            number = filters.IntegerField(max_value=100, min_value=10)
            float = filters.FloatField(max_value=100, min_value=10)

        msg = """
        {'number': [ErrorDetail(string='Ensure this value is less than or equal to 100.', code='max_value')], 'float': [ErrorDetail(string='Ensure this value is greater than or equal to 10.', code='min_value')]}
        """  # noqa: E501

        self.validation_error(
            queryset=NumberModel.objects.all(),
            filter_class=Filter,
            query={'number': 101, 'float': 8},
            message=msg
        )

    def test_with_valid_exact_integer(self):
        class Filter(filters.Filter):
            number = filters.IntegerField()

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={'number': self.number[0]}
        )
        self.assertTrue(
            all([request.cleaned_args.get('number') == value.number for value in filtered_queryset])
        )

    def test_with_valid_exact_float(self):
        class Filter(filters.Filter):
            float = filters.FloatField()

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={'float': self.float[0]}
        )
        self.assertTrue(
            all([request.cleaned_args.get('float') == value.float for value in filtered_queryset])
        )

    def test_with_valid_gt_integer(self):
        class Filter(filters.Filter):
            number = filters.IntegerField(lookup_expr='gt')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={'number': min(self.number)}
        )
        self.assertTrue(
            all([request.cleaned_args.get('number') < value.number for value in filtered_queryset])
        )

    def test_with_valid_gte_integer(self):
        class Filter(filters.Filter):
            number = filters.IntegerField(lookup_expr='gte')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={'number': min(self.number)}
        )
        self.assertTrue(
            all([request.cleaned_args.get('number') <= value.number for value in filtered_queryset])
        )

    def test_with_valid_lt_integer(self):
        class Filter(filters.Filter):
            number = filters.IntegerField(lookup_expr='lt')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={'number': max(self.number)}
        )
        self.assertTrue(
            all([request.cleaned_args.get('number') > value.number for value in filtered_queryset])
        )

    def test_with_valid_lte_integer(self):
        class Filter(filters.Filter):
            number = filters.IntegerField(lookup_expr='lte')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={'number': max(self.number)}
        )
        self.assertTrue(
            all([request.cleaned_args.get('number') >= value.number for value in filtered_queryset])
        )


class DateTimeTestCases(BaseTestCase):
    @classmethod
    def setUpTestData(cls):

        def random_date():
            return (datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 60))).date()

        def random_date_time():
            return datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 60))

        def random_time():
            return (datetime.datetime.now() + datetime.timedelta(minutes=random.randint(1, 60*69*24))).time()

        baker.make(
            DateFieldModel,
            date=random_date,
            datetime=random_date_time,
            time=random_time,
            _quantity=60
        )
        cls.dates = list(DateFieldModel.objects.order_by('-date').values_list('date', flat=True))
        cls.datetime = list(DateFieldModel.objects.order_by('-datetime').values_list('datetime', flat=True))
        cls.times = list(DateFieldModel.objects.order_by('-time').values_list('time', flat=True))

    def test_date_filter_with_invalid_date(self):
        class Filter(filters.Filter):
            date = filters.DateField(input_formats=['%Y-%m-%d'])

        msg = "{'date': [ErrorDetail(string='Date has wrong format. Use one of these formats instead: YYYY-MM-DD.', code='invalid')]}"
        self.validation_error(
            queryset=DateFieldModel.objects.all(),
            filter_class=Filter,
            query={'date': 'invalid date'},
            message=msg
        )

    def test_datetime_filter_with_invalid_datetime(self):
        class Filter(filters.Filter):
            datetime = filters.DateTimeField(input_formats=['%Y-%m-%d %H:%M:%S'])

        msg = "{'datetime': [ErrorDetail(string='Datetime has wrong format. Use one of these formats instead: YYYY-MM-DD hh:mm:ss.', code='invalid')]}"
        self.validation_error(
            queryset=DateFieldModel.objects.all(),
            filter_class=Filter,
            query={'datetime': 'invalid date'},
            message=msg
        )

    def test_time_filter_with_invalid_time(self):
        class Filter(filters.Filter):
            time = filters.DateTimeField(input_formats=['%H:%M:%S'])

        msg = "{'time': [ErrorDetail(string='Datetime has wrong format. Use one of these formats instead: hh:mm:ss.', code='invalid')]}"

        self.validation_error(
            queryset=DateFieldModel.objects.all(),
            filter_class=Filter,
            query={'time': 'invalid date'},
            message=msg
        )

    def test_date_filter_with_valid_exact_date(self):
        class Filter(filters.Filter):
            date = filters.DateField(input_formats=['%Y-%m-%d'])

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={'date': self.dates[0].strftime('%Y-%m-%d')}
        )

        self.assertTrue(
            all([request.cleaned_args.get('date') == value.date for value in filtered_queryset])
        )

    def test_date_filter_with_valid_gt_date(self):
        class Filter(filters.Filter):
            date = filters.DateField(input_formats=['%Y-%m-%d'], lookup_expr='gt')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={'date': self.dates[-1].strftime('%Y-%m-%d')}
        )
        self.assertTrue(
            all([request.cleaned_args.get('date') < value.date for value in filtered_queryset])
        )

    def test_date_filter_with_valid_lt_date(self):
        class Filter(filters.Filter):
            date = filters.DateField(input_formats=['%Y-%m-%d'], lookup_expr='lt')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={'date': self.dates[0].strftime('%Y-%m-%d')}
        )
        self.assertTrue(
            all([request.cleaned_args.get('date') > value.date for value in filtered_queryset])
        )

    def test_date_filter_with_valid_gte_date(self):
        class Filter(filters.Filter):
            date = filters.DateField(input_formats=['%Y-%m-%d'], lookup_expr='gte')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={'date': self.dates[-1].strftime('%Y-%m-%d')}
        )
        self.assertTrue(
            all([request.cleaned_args.get('date') <= value.date for value in filtered_queryset])
        )

    def test_date_filter_with_valid_lte_date(self):
        class Filter(filters.Filter):
            date = filters.DateField(input_formats=['%Y-%m-%d'], lookup_expr='lte')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={'date': self.dates[0].strftime('%Y-%m-%d')}
        )
        self.assertTrue(
            all([request.cleaned_args.get('date') >= value.date for value in filtered_queryset])
        )

    def test_datetime_filter_with_valid_exact_datetime(self):
        class Filter(filters.Filter):
            datetime = filters.DateTimeField(input_formats=['%Y-%m-%d %H:%M:%S'])

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={'datetime': self.datetime[0].strftime('%Y-%m-%d %H:%M:%S')}
        )
        self.assertTrue(
            all([request.cleaned_args.get('datetime') == value.datetime for value in filtered_queryset])
        )

    def test_datetime_filter_with_valid_date(self):
        class Filter(filters.Filter):
            datetime = filters.DateField(input_formats=['%Y-%m-%d'], lookup_expr='date')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={'datetime': self.datetime[-1].strftime('%Y-%m-%d')}
        )
        self.assertTrue(
            all([request.cleaned_args.get('datetime') == value.datetime.date() for value in filtered_queryset])
        )

    def test_datetime_filter_with_valid_gt_date(self):
        class Filter(filters.Filter):
            datetime = filters.DateField(input_formats=['%Y-%m-%d'], lookup_expr='gt')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={'datetime': self.datetime[-1].strftime('%Y-%m-%d')}
        )
        self.assertTrue(
            all([request.cleaned_args.get('datetime') <= value.datetime.date() for value in filtered_queryset])
        )

    def test_datetime_filter_with_valid_lt_date(self):
        class Filter(filters.Filter):
            datetime = filters.DateField(input_formats=['%Y-%m-%d'], lookup_expr='lt')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={
                'datetime': self.datetime[0].strftime('%Y-%m-%d')
            }
        )
        self.assertTrue(
            all([request.cleaned_args.get('datetime') > value.datetime.date() for value in filtered_queryset])
        )

    def test_datetime_filter_with_valid_gte_date(self):
        class Filter(filters.Filter):
            datetime = filters.DateField(input_formats=['%Y-%m-%d'], lookup_expr='gte')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={'datetime': self.datetime[-1].strftime('%Y-%m-%d')}
        )
        self.assertTrue(
            all([request.cleaned_args.get('datetime') <= value.datetime.date() for value in filtered_queryset])
        )

    def test_datetime_filter_with_valid_lte_date(self):
        class Filter(filters.Filter):
            datetime = filters.DateField(input_formats=['%Y-%m-%d'], lookup_expr='lte')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={
                'datetime': self.datetime[0].strftime('%Y-%m-%d')
            }
        )
        self.assertTrue(
            all([request.cleaned_args.get('datetime') >= value.datetime.date() for value in filtered_queryset])
        )

    def test_time_filter_with_valid_exact_time(self):
        class Filter(filters.Filter):
            time = filters.TimeField(input_formats=['%H:%M:%S'])

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={'time': self.times[0].strftime('%H:%M:%S')}
        )
        self.assertTrue(
            all([request.cleaned_args.get('time') == value.time for value in filtered_queryset])
        )

    def test_time_filter_with_valid_gt_time(self):
        class Filter(filters.Filter):
            time = filters.TimeField(input_formats=['%H:%M:%S'], lookup_expr='gt')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={'time': self.times[-1].strftime('%H:%M:%S')}
        )
        self.assertTrue(
            all([request.cleaned_args.get('time') < value.time for value in filtered_queryset])
        )

    def test_time_filter_with_valid_lt_time(self):
        class Filter(filters.Filter):
            time = filters.TimeField(input_formats=['%H:%M:%S'], lookup_expr='lt')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={
                'time': self.times[0].strftime('%H:%M:%S')
            }
        )
        self.assertTrue(
            all([request.cleaned_args.get('time') > value.time for value in filtered_queryset])
        )

    def test_time_filter_with_valid_gte_time(self):
        class Filter(filters.Filter):
            time = filters.TimeField(input_formats=['%H:%M:%S'], lookup_expr='gte')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={'time': self.times[-1].strftime('%H:%M:%S')}
        )
        self.assertTrue(
            all([request.cleaned_args.get('time') <= value.time for value in filtered_queryset])
        )

    def test_time_filter_with_valid_lte_time(self):
        class Filter(filters.Filter):
            time = filters.TimeField(input_formats=['%H:%M:%S'], lookup_expr='lte')

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=DateFieldModel.objects.all(),
            query={
                'time': self.times[0].strftime('%H:%M:%S')
            }
        )
        self.assertTrue(
            all([request.cleaned_args.get('time') >= value.time for value in filtered_queryset])
        )


class ListFieldTestCases(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(100):
            baker.make(
                NumberModel,
                number=i,
                float=i,
                decimal=i,
                _quantity=1
            )

    def test_list_field_with_invalid_type(self):
        class Filter(filters.Filter):
            number = filters.ListField(child=filters.IntegerField(min_value=0, max_value=100))

        message = """
        {'number': {0: [ErrorDetail(string='A valid integer is required.', code='invalid')], 1: [ErrorDetail(string='A valid integer is required.', code='invalid')], 2: [ErrorDetail(string='A valid integer is required.', code='invalid')]}}
        """  # noqa: E501
        self.validation_error(
            queryset=NumberModel.objects.all(),
            filter_class=Filter,
            query={'number': ['a', 'b', 'c']},
            message=message
        )

    def test_list_field_out_of_range_value(self):
        class Filter(filters.Filter):
            number = filters.ListField(child=filters.IntegerField(min_value=0, max_value=100))

        message = """
        {'number': {0: [ErrorDetail(string='Ensure this value is greater than or equal to 0.', code='min_value')], 1: [ErrorDetail(string='Ensure this value is less than or equal to 100.', code='max_value')], 2: [ErrorDetail(string='Ensure this value is less than or equal to 100.', code='max_value')]}}
        """  # noqa: E501
        self.validation_error(
            queryset=NumberModel.objects.all(),
            filter_class=Filter,
            query={'number': [-1, 111, 1233]},
            message=message
        )

    def test_list_field_with_min_limit(self):
        class Filter(filters.Filter):
            number = filters.ListField(min_length=3, child=filters.IntegerField(min_value=0, max_value=100))

        self.validation_error(
            queryset=NumberModel.objects.all(),
            filter_class=Filter,
            query={'number': [1, 12]},
            message="{'number': [ErrorDetail(string='Ensure this field has at least 3 elements.', code='min_length')]}"
        )

    def test_list_field_with_max_limit(self):
        class Filter(filters.Filter):
            number = filters.ListField(max_length=3, child=filters.IntegerField(min_value=0, max_value=100))

        self.validation_error(
            queryset=NumberModel.objects.all(),
            filter_class=Filter,
            query={'number': [1, 12, 13, 14]},
            message="{'number': [ErrorDetail(string='Ensure this field has no more than 3 elements.', code='max_length')]}"
        )

    def test_list_field_with_invalid_format(self):
        class Filter(filters.Filter):
            number = filters.ListField(min_length=3, child=filters.IntegerField(min_value=0, max_value=100))

        self.validation_error(
            queryset=NumberModel.objects.all(),
            filter_class=Filter,
            query={'number': '[12/12['},
            message="{'number': {0: [ErrorDetail(string='A valid integer is required.', code='invalid')]}}"
        )

    def test_with_valid_list(self):
        class Filter(filters.Filter):
            number = filters.ListField(min_length=3, child=filters.IntegerField(min_value=0, max_value=100))

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={
                'number': [3, 4, 5]
            }
        )
        self.assertTrue(
            all([v.number in [3, 4, 5] for v in filtered_queryset])
        )

    def test_with_valid_comma_seperated_list(self):
        class Filter(filters.Filter):
            number = filters.ListField(min_length=3, child=filters.IntegerField(min_value=0, max_value=100))

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={
                'number': '3,4,5'
            }
        )
        self.assertTrue(
            all([v.number in [3, 4, 5] for v in filtered_queryset])
        )

    def test_with_stringified_list(self):
        class Filter(filters.Filter):
            number = filters.ListField(min_length=3, child=filters.IntegerField(min_value=0, max_value=100))

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={
                'number': '[3,4,5]'
            }
        )
        self.assertTrue(
            all([v.number in [3, 4, 5] for v in filtered_queryset])
        )

    def test_with_different_separator(self):
        class Filter(filters.Filter):
            number = filters.ListField(min_length=3, separator='*', child=filters.IntegerField(min_value=0, max_value=100))

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={
                'number': '3*4*5'
            }
        )
        self.assertTrue(
            all([v.number in [3, 4, 5] for v in filtered_queryset])
        )


class RangeFieldTestCases(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(100):
            baker.make(
                NumberModel,
                number=i,
                float=i,
                decimal=i,
                _quantity=1
            )

    def test_with_more_than_two_numbers(self):
        class Filter(filters.Filter):
            number = filters.RangeField(child=filters.IntegerField(min_value=0, max_value=100))

        message = "{'number': [ErrorDetail(string='Ensure this field has no more than 2 elements.', code='max_length')]}"
        self.validation_error(
            queryset=NumberModel.objects.all(),
            filter_class=Filter,
            query={'number': [1, 2, 3]},
            message=message
        )

    def test_with_less_than_two_numbers(self):
        class Filter(filters.Filter):
            number = filters.RangeField(child=filters.IntegerField(min_value=0, max_value=100))

        message = "{'number': [ErrorDetail(string='Ensure this field has at least 2 elements.', code='min_length')]}"
        self.validation_error(
            queryset=NumberModel.objects.all(),
            filter_class=Filter,
            query={'number': [1]},
            message=message
        )

    def test_with_valid_data(self):
        class Filter(filters.Filter):
            number = filters.RangeField(child=filters.IntegerField(min_value=0, max_value=100))

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={
                'number': [5, 10]
            }
        )
        self.assertTrue(
            all([(5 <= v.number <= 10) for v in filtered_queryset])
        )

    def test_with_valid_data_modified_range_functions(self):
        class Filter(filters.Filter):
            number = filters.RangeField(lookup_expr=['gt', 'lt'], child=filters.IntegerField(min_value=0, max_value=100))

        request, view, filtered_queryset = self.filter_query(
            filter_class=Filter,
            queryset=NumberModel.objects.all(),
            query={
                'number': [5, 10]
            }
        )
        self.assertTrue(
            all([(5 < v.number < 10) for v in filtered_queryset])
        )
