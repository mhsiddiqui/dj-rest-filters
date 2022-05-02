from djfilters import filters

from .models import (BooleanModel, DateFieldModel, EmailModel, IpModel,
                     NumberModel, RelatedIntIdModel, RelatedSlugIdModel,
                     TextModel)

# Simple Filters


class TextFieldFilter(filters.Filter):
    text = filters.CharField(max_length=10, required=False)


class BooleanFilter(filters.Filter):
    flag = filters.BooleanField()


class CharFieldWithRequiredFilter(filters.Filter):
    char = filters.CharField()


# Model filters

class TextModelFilter(filters.ModelFilter):
    class Meta:
        model = TextModel
        fields = '__all__'


class IpModelFilter(filters.ModelFilter):
    class Meta:
        model = IpModel
        fields = '__all__'


class EmailModelFilter(filters.ModelFilter):
    class Meta:
        model = EmailModel
        fields = '__all__'


class NumberModelFilter(filters.ModelFilter):
    class Meta:
        model = NumberModel
        fields = '__all__'


class BooleanModelFilter(filters.ModelFilter):
    class Meta:
        model = BooleanModel
        fields = '__all__'


class DateFieldModelFilter(filters.ModelFilter):
    class Meta:
        model = DateFieldModel
        fields = '__all__'


class RelatedIntIdModelFilter(filters.ModelFilter):
    class Meta:
        model = RelatedIntIdModel
        fields = '__all__'


class RelatedSlugIdModelFilter(filters.ModelFilter):
    class Meta:
        model = RelatedSlugIdModel
        fields = '__all__'


class NoFieldFilter(filters.Filter):
    pass


def get_model_filter(
    filter_class,
    fields='__all__',
    extra_kwargs={}
):
    filter_class.Meta.fields = fields
    if extra_kwargs:
        filter_class.Meta.extra_kwargs = extra_kwargs
    return filter_class


def get_simple_filter(fields):
    class Filter(filters.Filter):
        def __init__(self, *args, **kwargs):
            for name, field in fields.items():
                self.fields[name] = field
            super(Filter, self).__init__(*args, **kwargs)
    return Filter
