from dataclasses import dataclass

@dataclass
class Recipe:
    id: int
    name: str

@dataclass
class Ingredient:
    id: int
    name: str
    unit: str

@dataclass
class RecipeIngredient:
    recipe_id: int
    ingredient_id: int
    amount: float
