from core.models import Tag
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
