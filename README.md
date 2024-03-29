CMPUT404-project-socialdistribution
===================================

CMPUT 404 Project: Social Distribution

[Project requirements](https://github.com/uofa-cmput404/project-socialdistribution/blob/master/project.org) 

Contributors / Licensing
========================

Authors:
    
* Riley Zilka
* James Laildaw
* Jaskirat Singh Saggu
* Yevhen Kaznovskyi
* Abdullah Khadeli

Generally everything is LICENSE'D under the APACHE 2 License.


===================

Venv setup
```
virtualenv venv --python=python3
source venv/bin/activate
pip install -r requirements.txt
```

Venv Windows
```
python3 -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
```

Run App
```
python manage.py runserver
```

Video:
[https://youtu.be/RXm9XA4EiyQ]

Requirements
- [x] As an author I want to make public posts.
- [x] As an author I want to edit public posts.
- [x] As an author, posts I create can be images.
- [x] As a server admin, images can be hosted on my server.
- [x] As an author, posts I create can be private to my friends
- [x] As an author, I can share other author’s public posts
- [x] As an author, I can re-share other author’s friend posts to my friends
- [x] As an author, posts I make can be in simple plain text
- [x] As an author, I want a consistent identity per server
- [x] As a server admin, I want to host multiple authors on my server
- [x] As a server admin, I want to share public images with users on other servers.
- [x] As an author, I want to pull in my github activity to my “stream”
- [x] As an author, I want to post posts to my “stream”
- [x] As an author, I want to delete my own public posts.
- [x] As an author, I want to befriend local authors
- [x] As an author, I want to befriend remote authors
- [x] As an author, I want to feel safe about sharing images and posts with my friends – images shared to friends should only be visible to friends. [public images are public]
- [x] As an author, when someone sends me a friends only-post I want to see the likes.
- [x] As an author, comments on friend posts are private only to me the original author.
- [x] As an author, I want un-befriend local and remote authors
- [x] As an author, I want to be able to use my web-browser to manage my profile
- [x] As a server admin, I want to be able add, modify, and remove authors.
- [x] As a server admin, I want to OPTIONALLY be able allow users to sign up but require my OK to finally be on my server
- [x] As a server admin, I don’t want to do heavy setup to get the posts of my author’s friends.
- [x] As a server admin, I want a restful interface for most operations
- [x] As an author, other authors cannot modify my public post
- [x] As an author, other authors cannot modify my shared to friends post.
- [x] As an author, I want to comment on posts that I can access
- [x] As an author, I want to like posts that I can access
- [x] As an author, my server will know about my friends
- [x] As an author, When I befriend someone (they accept my friend request) I follow them, only when the other author befriends me do I count as a real friend – a bi-directional follow is a true friend.
- [x] As an author, I want to know if I have friend requests.
- [x] As a server admin, I want to be able to add nodes to share with
- [x] As a server admin, I want to be able to remove nodes and stop sharing with them.
- [x] As a server admin, I can limit nodes connecting to me via authentication.
- [x] As a server admin, node to node connections can be authenticated with HTTP Basic Auth
- [x] As a server admin, I can disable the node to node interfaces for connections that are not authenticated!
- [x] As an author, posts I make can be in CommonMark
- [x] As an author, I want to be able to make posts that are unlisted, that are publicly shareable by URI alone (or for embedding images)
- [x] As an author, I want to be able to use my web-browser to manage/author my posts
- [ ] As an author, posts I create can link to images.
- [ ] As an author, posts I create can be private to another author
- [ ] As an author I should be able to browse the public posts of everyone

TOTAL: 43  

Done: 40  

Not Done: 3  

Percentage: 93%  


GROUP CONNECTIONS  

Example user for our app  

https://socialsync-404-project-6469dd163e44.herokuapp.com  

username: food  

password: 123  



https://frontend-21-average-f45e3b82895c.herokuapp.com/homePage  

username: jayz  

password: Password123_  


What we can do with them:
	- Send posts to them
	- Send comments to them
	- Receive comments
	- Send likes to them
	- Send follows to them
	- Perform followings and true friends
	- Send friends only posts
	- Sharing posts
	- Image posts

What we cant do with them:
	- They are unable to send us posts
		- This means we cant like their posts or comment
	- They are unable to like our posts

https://super-coding-team-89a5aa34a95f.herokuapp.com/  

username: antman  

password: Password123_  


What we can do with them:
	- Send and receive posts
	- Send and receive likes on posts and comments
	- Sending likes takes a long time, have to refresh for some reason
	- Send friends only posts to them
	- Receive comments
	- Send and receive follows
	- Perform followings and true friends
	- Sharing posts
	- Image Posts

What we cant do with them:
	- Get a 404 when sending comments, then their URL is not found for comments.
		- This is a response from their end, URL has been tested


Notes:
	- Both teams set the source of a post even if its not reshared, so any post that comes to our app from them is registered as a shared post
