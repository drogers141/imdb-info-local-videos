import json

from django.views import generic
from django.http import JsonResponse

from .models import IMDBTitleSearchData
from .imdb import imdb_title_data


class TitleListView(generic.ListView):
    title_type = 'Movies' # or 'TV'
    model = IMDBTitleSearchData
    context_object_name = 'title_list'
    template_name = 'imdb_info_local/titles.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_type'] = self.title_type
        return context

    def get_queryset(self):
        if self.title_type == 'Movies':
            return IMDBTitleSearchData.objects.filter(type=IMDBTitleSearchData.MOVIE)
        elif self.title_type == 'TV':
            return IMDBTitleSearchData.objects.filter(type=IMDBTitleSearchData.TV)


class MtimeTitleListView(TitleListView):
    def get_queryset(self):
        if self.title_type == 'Movies':
            return IMDBTitleSearchData.objects.filter(type=IMDBTitleSearchData.MOVIE).order_by('-file_mtime')
        elif self.title_type == 'TV':
            return IMDBTitleSearchData.objects.filter(type=IMDBTitleSearchData.TV).order_by('-file_mtime')


def update_title_data(request):
    post_data = json.load(request)['post_data']
    title = post_data['title']
    type = post_data['video_type']
    title_url = post_data['url']
    result = IMDBTitleSearchData.objects.filter(title=title, type=type)
    if result and len(result) == 1:
        target = result[0]
        new_title_data = imdb_title_data(title_url)
        target.rating = new_title_data.rating
        target.blurb = new_title_data.blurb
        target.save()
        return_data = {
            'rating': new_title_data.rating,
            'blurb': new_title_data.blurb
        }
    else:
        return_data = {
            'error': 'Either no match in db or more than 1 title for video type (no bueno).'
        }
    return JsonResponse(return_data)
