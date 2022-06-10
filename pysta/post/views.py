from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import post, comment, reply
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import PostForm, CommentForm, ReplyForm, EditForm
import os,datetime
from message.models import messages, thread
from django.db.models import Q
from django.contrib.auth.models import User

@login_required(login_url="/login")
def home(request):
    five_minutes_ago = timezone.now() + datetime.timedelta(minutes=-5)
    messages_x = messages.objects.filter(Q(from_user=request.user) | Q(to_user=request.user)).filter(time__gte=five_minutes_ago)
    context = {
        'posts':post.objects.all(),
        'new_messages':messages_x,
    }

    return render(request, 'post/home.html', context)

def live_like_data(request,post_id):
    postx = post.objects.all().filter(id=post_id)[0]
    likes = postx.user_liked.count()
    user_liked = request.user in postx.user_liked.all() 
    return JsonResponse({'data':likes,'user_liked':user_liked})
def live_data(request):
    five_minutes_ago = timezone.now() + datetime.timedelta(seconds=-1)
    messages_x = messages.objects.filter(Q(from_user=request.user) | Q(to_user=request.user)).filter(time__gte=five_minutes_ago)
    if len(messages_x) != 0:
        return JsonResponse({'recent_messages':list(messages_x.values())})
    else:
        return JsonResponse({'recent_messages':'none'})

def welcome_page(request):
    return render(request, 'post/welcome_page.html')

@login_required(login_url="/login")
def explore(request):
    context = {
        'posts':post.objects.all()
    }
    return render(request, 'post/explore.html', context)

@login_required(login_url="/login")
def post_detail_view(request, id):
    post_x = post.objects.all().filter(id=id)[0]
    post_x.views += 1
    post_x.save()
    comments = post_x.comment_set.all()
    for i in comments:
        replys = i.reply_set.all()
        i.replys.set(replys)
        i.save()
    for i in post_x.comment_set.all():
        i.likes = i.likess()
        i.save()
    comments = post_x.comment_set.all()  

    if request.method == 'POST':
        commentform = CommentForm(request.POST)
        if commentform.is_valid():
            user = request.user
            text = commentform.cleaned_data['text']
            cmt = comment(user=user, post=post_x, text=text)
            cmt.save()
            post_x.comments.add(cmt)
            post_x.save()
            return redirect('post-detail', id)
    else:
        commentform = CommentForm()

    context = {
        'post':post_x,
        'comments':comments,
        'commentform': commentform,
    }
    return render(request, 'post/post_detail.html', context)

@login_required(login_url="/login")
def like(request, id):
    post_x = post.objects.all().filter(id=id)[0]
    already_liked = False 
    for i in post_x.user_liked.all():
        if i == request.user:
            already_liked = True 
    
    if already_liked == False:
        post_x.user_liked.add(request.user)
    else:
        post_x.user_liked.remove(request.user)
    return HttpResponse('<script>history.back()</script>')

@login_required(login_url="/login")
def like_detail(request, id):
    post_x = post.objects.all().filter(id=id)[0]
    already_liked = False 
    for i in post_x.user_liked.all():
        if i == request.user:
            already_liked = True 
    
    if already_liked == False:
        post_x.user_liked.add(request.user)
    else:
        post_x.user_liked.remove(request.user)

    return redirect('post-detail', id)

@login_required(login_url="/login")   
def comment_like(request, id, comment_id):
    comment_x = comment.objects.all().filter(id=comment_id)[0]
    already_liked = False 
    for i in comment_x.user_liked.all():
        if i == request.user:
            already_liked = True 
    
    if already_liked == False:
        comment_x.user_liked.add(request.user)
    else:
        comment_x.user_liked.remove(request.user)
    

    return redirect('post-detail', id) 

@login_required(login_url="/login")
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            description = form.cleaned_data['description']
            image = request.FILES['image']
            video = False        
            if image.name[-3:] == "mov" or image.name[-3:] == "mp4" or image.name[-3:] == "avi":
                video = True
            p = post(user=user,video_file=video, description=description, file=image)
            p.save()
            
            return redirect('post-detail', p.id)
    else:
        form = PostForm()

    return render(request, 'post/create_post.html', {'form': form})

@login_required(login_url="/login")
def delete_post(request, id):
    post_to_delete = post.objects.all().filter(id=id)[0]
    if request.user == post_to_delete.user:
        post_to_delete.delete()
        return redirect('home')

@login_required(login_url="/login")
def comment_detail(request, comment_id):
    comment_x = comment.objects.all().filter(id=comment_id)[0]
    if request.method == 'POST':
        form = ReplyForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            text = form.cleaned_data['relpytext']
            comment(user=user,text=text,comment=comment_x).save()
    else:
        form = ReplyForm()

    return render(request, 'post/comment_detail.html', {'comment':comment_x,'form': form})

@login_required(login_url="/login")
def edit_post(request, id):
    post_to_edit = post.objects.all().filter(id=id)[0]
    if post_to_edit.user == request.user:
        if request.method == 'POST':
            form = EditForm(request.POST)
            if form.is_valid():
                description = form.cleaned_data['description']
                post_to_edit.description = description
                post_to_edit.save()
                return redirect('home')
        else:
            form = EditForm()

        return render(request, "post/edit_profile.html", {"post_to_edit":post_to_edit,"form":form})
    else:
        return redirect("home")