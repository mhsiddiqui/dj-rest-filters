from rest_framework import generics

from djfilters.backend import DjFilterBackend


def get_view(
    queryset=[],
    serializer_class=None,
    filter_class=None,
    pagination_class=None
):
    class MyView(generics.GenericAPIView):
        queryset = None
        serializer_class = None
        filter_backends = (DjFilterBackend,)
        filter_class = None
        pagination_class = None

    view = MyView
    view.queryset = queryset
    view.serializer_class = serializer_class
    view.filter_class = filter_class
    if pagination_class:
        view.pagination_class = pagination_class
        view.paginator = view.pagination_class()

    return view
