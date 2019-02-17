class Diet:
    def __init__(self, ):
        self.title = ""
        self.days = []


class Day:

    def __init__(self):
        self.recipes = []


class Recipes:
    def __init__(self, title, calories, protein, sodium, rating, ingredients, directions, categories, description):
        self.title = title
        self.calories = calories
        self.protein = protein
        self.sodium = sodium
        self.rating = rating
        self.ingredients = ingredients
        self.directions = directions
        self.categories = categories
        self.description = description