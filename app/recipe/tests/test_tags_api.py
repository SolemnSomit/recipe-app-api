from core.models import Tag, Recipe
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import TagSerializer
from rest_framework import status
from rest_framework.test import APIClient

TAGS_URL = reverse('recipe:tag-list')


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


class PublicTagsApiTest(TestCase):
    """Test the publicly available TAGS Api"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to retreive tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    """Test the APIs that require a user to be logged in"""

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_tags_returned(self):
        """Test that created tags for the logged in user can be retrieved"""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Comfort Foods')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags only belonging to user are returned"""
        test_user = sample_user('test2@test.com', 'testPassword')
        Tag.objects.create(user=test_user, name='Vegan')
        tag = Tag.objects.create(user=self.user, name='Comfort food')
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tags_successful(self):
        """Test creating a new tag"""
        payload = {
            'name': 'Test tag'
        }
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """Test creating a new with invalid payload"""
        payload = {
            'name': ''
        }
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_tags_assigned_to_recipes(self):
        """Filter tags assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name='Tag1')
        tag2 = Tag.objects.create(user=self.user, name='Tag2')
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(tag1)

        res = self.client.get(
            TAGS_URL,
            {'assigned_only': 1}
        )

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_get_tags_assigned_unique(self):
        tag1 = Tag.objects.create(user=self.user, name='Tag1')
        Tag.objects.create(user=self.user, name='Tag2')
        recipe1 = sample_recipe(user=self.user)
        recipe1.tags.add(tag1)
        recipe2 = sample_recipe(user=self.user, title='New Title')
        recipe2.tags.add(tag1)

        res = self.client.get(
            TAGS_URL,
            {'assigned_only': 1}
        )

        self.assertEqual(len(res.data), 1)
