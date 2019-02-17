from mongoengine import Document, EmbeddedDocument, fields


class StringListField(fields.ListField):
    child = fields.StringField(required=True)


class Recipes(Document):
    title = fields.StringField(required=True, default="")
    calories = fields.DecimalField(required=True, default=0.0)
    protein = fields.DecimalField(required=True, default=0.0)
    sodium = fields.DecimalField(required=True, default=0.0)
    rating = fields.DecimalField(required=True, default=0.0)
    ingredients = fields.DynamicField(required=True)
    directions = fields.DynamicField(required=True)
    categories = fields.DynamicField(required=True)
    description = fields.StringField(required=True, default="")


class Diet(Document):
    title = fields.StringField(required=False, default="")
    days = fields.DynamicField(required=True)


class Day(Document):
    name = fields.StringField(required=True)
    recipes = fields.DynamicField(required=True)