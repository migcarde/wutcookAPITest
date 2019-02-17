from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from mongoengine.queryset.visitor import Q
from rest_framework.renderers import JSONRenderer
from .models import Recipes
from .helpers import Day, Diet
from .helpers import Recipes as Rec
from .serilalizer import RecipeSerializer, DietSerializer
from bson.json_util import dumps
from sklearn import neighbors
from sklearn.model_selection import train_test_split
from django.core import serializers

import json
import pandas as pd

# Create your views here.
class RecipeView(APIView):
    def get(self, request):
        aux = Recipes.objects.all()
        serializer = RecipeSerializer(Recipes.objects.all(), many=True)
        response = {"recipes": serializer.data}  # error

        return Response(response, status=status.HTTP_200_OK)

    # def post(self, request, format=None):
    #     data = request.data
    #     serializer = RecipeSerializer(data=data)
    #     if serializer.is_valid():
    #         poll = Recipes(**data)
    #         poll.save()
    #         response = serializer.data
    #         return Response(response, status=status.HTTP_200_OK)


class RecipeDetails(APIView):
    def get(self, request, pk):
        # recipe = Recipes.objects.get(pk=pk)
        recipe = Recipes.objects.with_id(pk)
        serializer = RecipeSerializer(recipe, many=False)
        response = {"recipes": serializer.data}

        return Response(response, status=status.HTTP_200_OK)


class RecommendDiet(APIView):
    def get(self, request):
        # recipes = Recipes.objects(protein=18.0)
        # recipes = Recipes.objects(title__contains="Boudin Blanc")
        # Obtiene el json con los filtros de recomendacion desde Android
        recommendFilter = request.data

        # Realiza la consulta con los filtros
        recipes = Recipes.objects(
            Q(calories__lt=recommendFilter["calories"]) & Q(protein__lt=recommendFilter["protein"]) &
            Q(sodium__lt=recommendFilter["sodium"])).order_by(
            "rating")

        if recipes.__len__() == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        elif recipes.__len__() > 1:
            serializer = RecipeSerializer(recipes, many=True)
        else:
            serializer = RecipeSerializer(recipes, many=False)
        # Obtenemos el json
        response = {"recipes": serializer.data}

        # Transformamos los datos con pandas
        data = pd.read_json(response)

        # Obtenemos los datos a entrenar
        train = data[["calories", "protein", "sodium"]]
        train_data = train_test_split(train, test_size=0.2, random_state=42)

        #Entrenamos los datos
        k = 10
        neig = neighbors.NearestNeighbors(k, 'cosine')
        top_k_distances, top_k_items = neig.kneighbors(train_data, return_distance=True)

        # Convertimos los resultados al formato JSON y los enviamos a Android
        result = top_k_items.to_json()

        return Response(response, status=status.HTTP_200_OK)


class Pruebas(APIView):
    def post(self, request, format=None):
        recommendFilter = request.data

        # Realiza la consulta con los filtrosy ordenador por la calificación en orden ascendente
        recipesQuery = Recipes.objects(
            Q(calories__lt=recommendFilter["calories"]) & Q(protein__lt=recommendFilter["protein"]) &
            Q(sodium__lt=recommendFilter["sodium"]) & Q(ingredients__nin=recommendFilter["ingredients"])).order_by(
            "-rating")[:5000] #Mirar como limitar la consulta

        # recipesQuery = Recipes.objects(
        #     Q(calories__lt=recommendFilter["calories"]) & Q(protein__lt=recommendFilter["protein"]) &
        #     Q(sodium__lt=recommendFilter["sodium"])
        # ).order_by("-rating")

        serializer = RecipeSerializer(recipesQuery, many=True)

        # recipes = recipesQuery.data
        #
        # if recipes.__len__() == 0: #No tiene característica __len__()?
        #     return Response(status=status.HTTP_404_NOT_FOUND)
        # elif recipes.__len__() > 1:
        #     serializer = RecipeSerializer(recipes, many=True)
        # else:
        #     serializer = RecipeSerializer(recipes, many=False)
        # Obtenemos el json
        # response = {"recipes": serializer.data}

        # Obtenemos el DataFrame con los datos serializados
        dataframe = pd.DataFrame.from_dict(serializer.data)

        # Obtenemos los datos que queremos entrenar
        train = dataframe[["calories", "protein", "sodium"]]
        data_train, test_train = train_test_split(train, test_size=0.2, random_state=42)

        # Entrenamos los datos
        k = 10 # Número de muestras que nos va a devolver
        neig = neighbors.NearestNeighbors(k, 'cosine') # Aplicamos el algoritmo de vecinos más cercanos
        neig.fit(data_train) #Entrenamos los datos
        top_k_distances, top_k_items = neig.kneighbors(data_train, return_distance=True) # Obtenemos los vecinos más cercanos

        top = []
        for item in top_k_items:
            top.extend(item)
        # a = top_k_items[0] #Escogemos la primera opción
        recipes = dataframe.iloc[top] # Obtenemos los datos del dataframe
        response = {"recipes": recipes.T}  # Creamos un JSON

        # Escogemos las recetas recomendadas y creamos dietas teniendo en cuenta los datos dados por el usuario
        diets = []

        diet = Diet()
        day = Day()

        # diet = Diet()
        # diet.days = []

        countCalories = 0.0
        countSodium = 0.0
        countProteins = 0.0
        morning = 0
        count = 0

        for i in recipes[["id", "title", "calories", "protein", "sodium", "rating", "ingredients", "directions", "categories", "description"]].values: # Obtener para el resto de valores
            cal = float(i[2])
            prot = float(i[3])
            sod = float(i[4])
            rate = float(i[5])

            if diets.__len__() == 10:
                break

            if cal < recommendFilter["calories"] and prot < recommendFilter["protein"]\
                    and sod < recommendFilter["sodium"]\
                    and (countCalories + cal) <= recommendFilter["calories"]\
                    and (countProteins + prot) <= recommendFilter["protein"]\
                    and (countSodium + sod) <= recommendFilter["sodium"]\
                    and diet.days.__len__() <= 7:
                recipe = Rec(i[1], cal, prot, sod, rate, i[6], i[7], i[8], i[9])
                countCalories += cal
                countProteins += prot
                countSodium += sod

                if morning == 0:
                    day.recipes.append(recipe.__dict__)
                    morning = 1
                elif morning == 1:
                    day.name = "Día " + (count + 1).__str__()
                    day.recipes.append(recipe.__dict__)
                    morning = 0
                    count = count + 1

                    diet.days.append(day.__dict__)
                    day = Day()
            if diet.days.__len__() >= 7:
                diets.append(diet.__dict__)
                diet = Diet()

                countCalories = 0.0
                countSodium = 0.0
                countProteins = 0.0
                morning = 0
                count = 0

        response = {"diet": diets}

        # for i in diets:
        #     print(i.__dict__)
        #     print(i)
        #     print(i.__str__())
        #
        # response = json.dumps([di.__dict__ for di in diets])
        # print(response)

        # return JsonResponse()
        return Response(response, status=status.HTTP_200_OK)