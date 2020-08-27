from core.models import Tag, Ingredient
from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer):
    """Serializer for the tag object"""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for the ingredient object"""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)
