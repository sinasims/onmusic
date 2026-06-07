from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse
from .models import BlogPost, Category
from django.db.models import Prefetch
from main.models import Comment
from django.contrib.contenttypes.models import ContentType


class BlogListView(ListView):
    model = BlogPost
    template_name = 'blog/list.html'
    context_object_name = 'posts'
    paginate_by = 12

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True)

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('ajax'):
            html = render_to_string('blog/_post_items.html', context, self.request)
            return JsonResponse({'html': html, 'has_next': context['page_obj'].has_next()})
        return super().render_to_response(context, **response_kwargs)


class BlogDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = Comment.objects.filter(
            content_type=ContentType.objects.get_for_model(BlogPost),
            object_id=self.object.id, is_approved=True, parent__isnull=True
        ).prefetch_related(Prefetch('replies', queryset=Comment.objects.filter(is_approved=True)))
        context['content_type_id'] = ContentType.objects.get_for_model(BlogPost).id
        context['object_id'] = self.object.id
        return context
