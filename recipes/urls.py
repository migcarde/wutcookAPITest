from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.RecipeView.as_view()),
    url(r'test/$', views.Pruebas.as_view()),
    url(r'recommend/$', views.RecommendDiet.as_view()),
    url(r'^(?P<pk>[\w\-]+)/$', views.RecipeDetails.as_view()),
]