from rest_framework_mongoengine import serializers
from .models import Recipes, Diet


class RecipeSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Recipes
        #fields = ('title', "calories", "protein", "sodium", "rating", "ingredients") #error al intentar serializar un array, ver como corregirlo
        fields = '__all__'

class DietSerializer(serializers.DocumentSerializer):
    class Meta:
        model = Diet
        fields = '__all__'