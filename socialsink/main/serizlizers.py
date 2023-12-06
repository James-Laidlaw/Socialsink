from rest_framework import serializers
from .models import Author, Post, Comment, Like, Inbox
from django.urls import reverse, resolve
from rest_framework.request import Request
import json
import pprint
#should also be able to handle passing in a correct id
def get_object_id_from_url(url):
    #not the most robust URL parsing but it might be good enough 
    # TODO consider improving/figuring out how django does this
    stripped_url = url.rstrip('/')#remove trailing slash
    return stripped_url.split('/')[-1]

#TODO check if incoming ids are in URL, if so, extract
# file heavily made use of: https://www.django-rest-framework.org/api-guide/serializers/
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
        super_result['id'] = author_url.rstrip('/')
        super_result['url'] = author_url.rstrip('/')
        super_result['host'] = host_url
        super_result['displayName'] = instance.user.username
        
        return super_result
    
visibility_options = {0: "PUBLIC", 1: "FRIENDS", 2: "UNLISTED"}
#TODO serializer should return comments too
#TODO test
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'description', 'contentType', 'content', 'source', 'origin', 'categories']

    def to_representation(self, instance):
        request: Request = self.context.get('request')

        super_result = super().to_representation(instance)
        author_id = instance.author_endpoint.split('/')[-1]
        post_url = request.build_absolute_uri(reverse('postReqHandler', args=[author_id, instance.id])).rstrip('/')

        super_result['type'] = "post"
        super_result['id'] = post_url.rstrip('/')
        super_result['author'] = json.loads(instance.author_data)
        super_result['published'] = instance.created_at.isoformat()
        super_result['visibility'] = visibility_options[instance.publicity]
        super_result['unlisted'] = instance.unlisted
        super_result['comments'] = post_url + "comments"
        
        #get first 5 comments
        post_comments = Comment.objects.filter(post_endpoint=post_url)[:5]
        comment_representations = []
        for comment in post_comments:
            comment_representations.append(CommentSerializer(comment, context={'request': request}).data)
        
        super_result['commentsSrc'] = comment_representations

        # get categories, if no categories, set to empty list
        categories = instance.categories.split("#") if instance.categories else []
        super_result['categories'] = ' '.join(["#"+i.strip() for i in categories if i != ''])
        
        return super_result
    
    def create(self, validated_data):
        request: Request = self.context.get('request')
        validated_data['author_endpoint'] = request.build_absolute_uri(reverse('authorReqHandler', args=[request.user.author.id]))
        author = Author.objects.get(user=request.user)
        validated_data['author_data'] = json.dumps(AuthorSerializer(author).data)
        validated_data['id'] = self.initial_data.get('id', None) # not sure if the best way to do this

        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content']

    def to_representation(self, instance):
        request: Request = self.context.get('request')
        super_result = super().to_representation(instance)
        post_url = instance.post_endpoint.rstrip('/')
        comment_url = request.build_absolute_uri(reverse('commentReqHandler', args=[post_url.split('/')[-3], post_url.split('/')[-1]])) + '/' + str(instance.id)

        super_result['type'] = "comment"
        super_result['id'] = comment_url
        super_result['author'] = json.loads(instance.author_data)
        super_result['published'] = instance.created_at.isoformat()
        super_result['comment'] = instance.content
        super_result['contentType'] = "text/plain" #Spec wants us to specify content type but doens't say we have to support anything other than plaintext

        return super_result
    
    def create(self, validated_data):
        request: Request = self.context.get('request')
        
        #author can be a JSON representation or the model object, for reasons i hate
        author = self.initial_data.get('author', None)
        authorRawID = None
        if isinstance(author, Author):
            authorRawID = str(author.id)
        else:
            authorRawID = author.get('id', None)  

        host_url = request.build_absolute_uri("/")
        is_foreign = (host_url not in authorRawID)
        validated_data['is_foreign'] = is_foreign

        if is_foreign:
            validated_data['foreign_author_id'] = authorRawID
        else:
            validated_data['author_id'] = get_object_id_from_url(authorRawID)
            validated_data['author'] = Author.objects.get(id=validated_data['author_id'])

        validated_data['post_id'] = self.initial_data.get('post_id', None)
        
        if 'comment' in validated_data:
            validated_data['content'] = validated_data.pop('comment')

        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data['content'] = self.initial_data.get('comment', None)
        return super().update(instance, validated_data)

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = []

    def to_representation(self, instance):
        request: Request = self.context.get('request')
        super_result = super().to_representation(instance)
        super_result['type'] = "like"

        super_result['author'] = json.loads(instance.author_data)

        if instance.post_endpoint != '':
            super_result['object'] = instance.post_endpoint.rstrip('/')
            super_result['summary'] = instance.summary
        elif instance.comment_endpoint != '':
            super_result['object'] = instance.comment_endpoint.rstrip('/')
            super_result['summary'] = instance.summary

        super_result['@context'] = instance.context
        return super_result
    
    def create(self, validated_data):
        #unclear if this will be object containing author id or just the id
        authorObj = self.initial_data.get('author', None)

        authorURL = None
        if isinstance(authorObj, str):
            authorURL = authorObj
        else:
            authorURL = authorObj.get('id', None)    

        validated_data['author_endpoint'] = authorURL

        # Extract the id from the "object" input URL
        object_url = self.initial_data.get('object', None)
        if object_url:
            object_id = get_object_id_from_url(object_url)
            validated_data['post_endpoint'] = object_id if 'post' in object_url else None
            validated_data['comment_endpoint'] = object_id if 'comment' in object_url else None
        
        validated_data['context'] = self.initial_data.get('@context', None)
        return super().create(validated_data)
    

class InboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inbox
        fields = []

    def to_representation(self, instance):
        data = {}
        data['endpoint'] = instance.endpoint.rstrip('/')
        data['type'] = instance.type

        return data
    
