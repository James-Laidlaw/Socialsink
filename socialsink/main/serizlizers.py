from rest_framework import serializers
from .models import Author
from django.urls import reverse
from rest_framework.request import Request


# https://www.django-rest-framework.org/api-guide/serializers/
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = [ 'github', 'profileImage']

    def update(self, instance, validated_data):
        instance.user.username = validated_data.get('displayName', instance.user.username)
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        request: Request = self.context.get('request')

        if request is None:
            print("Need request to add host to author")
            return super().to_representation(instance)

        super_result = super().to_representation(instance)

        author_url = request.build_absolute_uri(reverse('authorDetail', args=[instance.id]))
        host_url = request.build_absolute_uri("/")

        super_result['id'] = author_url
        super_result['url'] = author_url
        super_result['host'] = host_url
        super_result['displayName'] = instance.user.username
        
        return super_result