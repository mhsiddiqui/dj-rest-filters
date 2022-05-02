from django.test import TestCase
from rest_framework import exceptions
from rest_framework.test import APIRequestFactory

from djfilters.backend import DjFilterBackend
from tests.views import get_view

factory = APIRequestFactory()


class BaseTestCase(TestCase):
    backend = DjFilterBackend()

    def filter_query(
        self,
        queryset=None,
        filter_class=None,
        pagination_class=None,
        query=None
    ):
        view = get_view(
            queryset=queryset,
            filter_class=filter_class,
            pagination_class=pagination_class
        )
        request = factory.get('/', data=query or {})
        request.query_params = request.GET
        filtered_queryset = self.backend.filter_queryset(request, view.queryset, view)
        return (
            request, view, filtered_queryset
        )

    def validation_error(
        self,
        queryset=None,
        filter_class=None,
        query=None,
        pagination_class=None,
        message='',
        exception=exceptions.ValidationError
    ):
        view = get_view(
            queryset=queryset,
            filter_class=filter_class,
            pagination_class=pagination_class
        )
        request = factory.get('/', data=query)
        request.query_params = request.GET

        with self.assertRaisesMessage(exception, message.strip()):
            self.backend.filter_queryset(request, view.queryset, view)
