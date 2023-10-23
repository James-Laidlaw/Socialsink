from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Author

from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.
@login_required
def homepage(request):
    return render(request=request,
                  template_name='main/home.html',
                  context={})

def login(request):
    return render(request=request,
                  template_name='main/login.html',
                  context={})


@api_view(['POST'])
def loginRequest(request):
    print("Request received")

    username = request.data['username']
    password = request.data['password']

    exists = Author.objects.filter(username=username, password=password).first()

    if exists != None:
        
        return HttpResponse(201)

    return HttpResponse(403)