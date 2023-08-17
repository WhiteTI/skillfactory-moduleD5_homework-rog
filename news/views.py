from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, CreateView, UpdateView, DetailView, FormView, TemplateView
from django.contrib.auth.models import Group

from .models import Post
from .filters import PostFilter
from .forms import PostForm, RegisterForm, LoginForm


class PostList(ListView):
    model = Post
    template_name = 'news/posts.html'
    context_object_name = 'posts'
    ordering = ['-rating']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = PostFilter(self.request.GET, queryset=self.get_queryset())
        context['choices'] = Post.CATEGORY_CHOICES
        context['form'] = PostForm()
        context['is_not_author'] = not self.request.user.groups.filter(name='author').exists()
        return context

    def post(self, request, *args, **kwargs):
        form = PostForm(request.POST)
        if form.is_valid():
            form.save()
        return super().get(request, *args, **kwargs)


@login_required
def upgrade_me(request):
    user = request.user
    premium_group = Group.objects.get(name='author')
    if not request.user.groups.filter(name='author').exists():
        premium_group.user_set.add(user)
    return redirect('/posts/')


class PostDetail(DetailView):
    template_name = 'news/post.html'
    queryset = Post.objects.all()


class PostCreate(CreateView):
    template_name = 'news/post_create.html'
    form_class = PostForm


class PostUpdate(LoginRequiredMixin, UpdateView, PermissionRequiredMixin):
    template_name = 'news/post_create.html'
    form_class = PostForm
    permission_required = ('news.change _post',)

    def get_object(self, **kwargs):
        id = self.kwargs.get('pk')
        return Post.objects.get(pk=id)


class PostDelete(DeleteView):
    template_name = 'news/post_delete.html'
    queryset = Post.objects.all()
    success_url = reverse_lazy('news:posts')


class RegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = 'news/register.html'
    success_url = '/'

    def form_valid(self, form):
        user = form.save()
        group = Group.objects.get(name='basic')
        user.groups.add(group)
        user.save()
        return super().form_valid(form)


class LoginView(FormView):
    model = User
    form_class = LoginForm
    template_name = 'news/login.html'
    success_url = '/posts/'

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
        return super().form_valid(form)


class LogoutView(LoginRequiredMixin, TemplateView):
    template_name = 'news/logout.html'

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)
