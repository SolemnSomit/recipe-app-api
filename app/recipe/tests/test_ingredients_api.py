from core.models import Ingredient, Recipe
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import IngredientSerializer
from rest_framework import status
from rest_framework.test import APIClient

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def sample_user(email='test@test.com', password='testPassword'):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample Recipe',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicIngredientApiTests(TestCase):
    """Testing the publicly available API end points for ingredients"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the endpoint"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Testing the privately avaialable end points that require a login"""

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        """Test if we can retreive the list"""
        Ingredient.objects.create(user=self.user, name='Mirch')
        Ingredient.objects.create(user=self.user, name='Masala')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """
        Test that only ingredients related to  the
        authenticated user are returned
        """
        test_user = sample_user(email='test2@test.com')
        Ingredient.objects.create(user=test_user, name='Avacado')
        ingredient = Ingredient.objects.create(user=self.user, name='Bread')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test create a new ingredient"""
        payload = {'name': 'Cabbage'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test creating invalid ingredients fail"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ingredients_assigned_to_recipes(self):
        """Test filtering ingredients by those assigned to recipes"""
        ing1 = Ingredient.objects.create(user=self.user, name='ing1')
        ing2 = Ingredient.objects.create(user=self.user, name='ing2')
        recipe = sample_recipe(user=self.user)
        recipe.ingredients.add(ing1)

        res = self.client.get(
            INGREDIENTS_URL,
            {'assigned_only': 1}
        )

        serializer1 = IngredientSerializer(ing1)
        serializer2 = IngredientSerializer(ing2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredient_assigned_unique(self):
        """Test filtering ingredients by assigned returns unique items"""
        ing = Ingredient.objects.create(user=self.user, name='ing1')
        Ingredient.objects.create(user=self.user, name='ing2')
        recipe1 = sample_recipe(user=self.user)
        recipe1.ingredients.add(ing)
        recipe2 = sample_recipe(user=self.user, title='New Recipe')
        recipe2.ingredients.add(ing)
        res = self.client.get(
            INGREDIENTS_URL,
            {'assigned_only': 1}
        )

        self.assertEqual(len(res.data), 1)
