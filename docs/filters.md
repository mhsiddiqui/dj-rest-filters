# Filter Guide

## Filters
Writing filters is similar to the serializer. You can write simple filters just for validating query params or also for filtering if queryset is provided in your view. 

**Note**: If a field is not declared in filter, then no error will be raised and no filtering will be applied on queryset on the basis of that provided filter.

### Declaring Filter

Below is the way to declare a simple filter

```python
from djfilters import filters

class MySimpleFilter(filters.Filter):
    id = filters.IntegerField(max_value=100, min_value=1)
    title = filters.CharField(max_length=100, min_length=10)
```
By default all fields will be not required. This can be changed by providing `required=True` to the field. Check [Field Guide](/filter_fields/) for detailed documentation on all fields.
### Validation

This filter will automatically validate `id` and `title` according to min, max value/length. What if we want to add custom validation? Its simple. Just define validation methods as below

```python
class MySimpleFilter(filters.Filter):
    id = filters.IntegerField(max_value=100, min_value=1)
    title = filters.CharField(max_length=100, min_length=10)

    def validate(self, attr):
        # Write your validation logic here
        if your_check_here:
            raise filters.ValidationError('Your error message here')
        return attr

    # Or field validation only
    
    def validate_title(self, title):
        # Write your validation logic here
        if your_check_here:
            raise filters.ValidationError('Your error message here')
        return title
```

### Filtering
Above filter will automatically apply filtering on provided queryset. But for some field there is is need of custom filtering mechanism, it can be done in following way

```python
class MySimpleFilter(filters.Filter):
    id = filters.IntegerField(max_value=100, min_value=1)
    title = filters.CharField(max_length=100, min_length=10)

    def filter(self, validated_data):
        qs = self.queryset.all()
        # write your filtering logic here
        return qs
    
    def filter_title(self, qs, value):
        return qs.filter(title__icontains=value)
```

## Model Filters

Model Filters are very easy to declare similar to Model Serializer. You just need to add model and fields and you are good to go. Consider following models
```python
from django.db import models
from django.contrib.auth.models import User

class Todo(models.Model):
    title = models.CharField(max_length=100)
    detail = models.TextField()
    is_complete = models.BooleanField(default=False)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
```

### Declaring Model Filters
For above model, filter will be declared like this
```python
from djfilters import filters

class TodoFilter(filters.ModelFilter):
    class Meta:
        model = Todo
        fields = '__all__'
```
By default, all fields in filters will be not required. If you want to change any of the default parameter, you can use `extra_kwargs` option like this.

```python
class TodoFilter(filters.ModelFilter):
    class Meta:
        model = Todo
        fields = '__all__'
        extra_kwargs = {
            'title': {'required': True, 'lookup_expr': 'icontains'}
        }
```
Similar to `fields`, `exclude` option can also be used to exclude some fields from filters. 

**Note**: Nested filters are not supported so adding `depth` or any field which is actually a filter will raise an error.

### Validation
Custom validation can applied in same way as for simple filters.

### Filter
Custom filtering can be applied in similar way as for simple filters.

### Foreign Keys

If your model contains foreign keys, then that field will become a choice field which can only have value according to that model object. If other value will be provided, validation error will be raised.

#### Filtering on Foreign Key data
If filtering on the basis of foreign key data is required, then `source` option can be used like this

```python
class TodoFilter(filters.ModelFilter):
    user = filters.CharField(max_length=100, source='user.username')
    class Meta:
        model = Todo
        exclude = ('user',)
```

In above case, `user__username={user}` filter will be applied on queryset. 
