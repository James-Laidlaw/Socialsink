from rest_framework import serializers
from .models import Author, Post
from django.urls import reverse
from rest_framework.request import Request


# https://www.django-rest-framework.org/api-guide/serializers/
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = [ 'github', 'profileImage']

    def update(self, instance, validated_data):
        # its a little hacky to use initial_data here, but I can't figure out how to allow custom fields through the validation
        instance.user.username = self.initial_data.get('displayName', instance.user.username)
        instance.user.save() # serializers dont automatically save related models

        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        request: Request = self.context.get('request')

        if request is None:
            return super().to_representation(instance)

        super_result = super().to_representation(instance)

        author_url = request.build_absolute_uri(reverse('authorReqHandler', args=[instance.id]))
        host_url = request.build_absolute_uri("/")

        super_result['type'] = "author"
        super_result['id'] = author_url
        super_result['url'] = author_url
        super_result['host'] = host_url
        super_result['displayName'] = instance.user.username
        
        return super_result
    
visibility_options = {0: "PUBLIC", 1: "FRIENDS", 2: "PRIVATE"}
#TODO serializer should return comments too
#TODO test
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'description', 'contentType', 'content', 'source', 'origin', 'categories']

    def to_representation(self, instance):
        request: Request = self.context.get('request')

        super_result = super().to_representation(instance)
        author_id = instance.author.id
        post_url = request.build_absolute_uri(reverse('postReqHandler', args=[author_id, instance.id]))
        #TODO comments, likes
        super_result['type'] = "post"
        super_result['id'] = post_url
        super_result['author'] = AuthorSerializer(instance.author, context={'request': request}).data
        super_result['published'] = instance.created_at.isoformat()
        super_result['visibility'] = visibility_options[instance.publicity]
        super_result['unlisted'] = instance.unlisted

        # get categories, if no categories, set to empty list
        categories = instance.categories.split("#") if instance.categories else []
        super_result['categories'] = ' '.join(["#"+i.strip() for i in categories if i != ''])
        
        return super_result
    
    def create(self, validated_data):
        request: Request = self.context.get('request')
        validated_data['author_id'] = Author.objects.get(user=request.user).id
        validated_data['id'] = self.initial_data.get('id', None) # not sure if the best way to do this

        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
