"""machine URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import datetime
from django.contrib import admin
from django.urls import path, register_converter

from . import views

class DateConverter:
    regex = '\d{4}-\d{2}-\d{2}'

    def to_python(self, value):
        return datetime.datetime.strptime(value, '%Y-%m-%d')

    def to_url(self, value):
        return value.strftime(value, '%Y-%m-%d')

register_converter(DateConverter, 'reverse_date')

urlpatterns = [
    path('decode/<slug:message>/<reverse_date:date>/', views.decode_view),
    path('encode/<slug:message>/<reverse_date:date>/<slug:indicator_indicator>/<slug:message_indicator>/', views.encode_view)
]
