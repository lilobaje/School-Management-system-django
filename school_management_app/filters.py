from dataclasses import fields
import django_filters
from .models import Staffs

class StaffsFilter(django_filters.FilterSet):

    class Meta:
        model = Staffs
        fields = {'address':['exact']}