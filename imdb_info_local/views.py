import json
import logging

from django.shortcuts import render
from django.views import generic
from django.http import JsonResponse
from django.db.models import Q

from .models import IMDBTitleSearchData, update_image_file
from .imdb import imdb_title_data

logger = logging.getLogger(__name__)


class TitleListView(generic.ListView):
    title_type = 'Movies' # or 'TV'
    model = IMDBTitleSearchData
    context_object_name = 'title_list'
    template_name = 'imdb_info_local/titles.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_type'] = self.title_type
        context['count'] = self.get_queryset().count()
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
    type_ = post_data['video_type']
    title_url = post_data['url']
    result = IMDBTitleSearchData.objects.filter(title=title, type=type_)
    if result and len(result) == 1:
        target = result[0]
        new_title_data = imdb_title_data(title_url)
        target.rating = new_title_data.rating
        target.blurb = new_title_data.blurb
        print(f'target.image.url: {target.image.url}')

        # target.image = add_image_file(target, new_title_data.image_file)
        update_image_file(target, new_title_data.image_file)
        target.save()
        print(f'new target.image.url: {target.image.url}')
        return_data = {
            'rating': new_title_data.rating,
            'blurb': new_title_data.blurb,
            'image-url': target.image.url
        }
    else:
        return_data = {
            'error': ('Either no match in db or more than 1 title for video type.  Check the README.md ' +
                      'for requirements.')
        }
    return JsonResponse(return_data)


class SearchResultsListView(generic.ListView):
    context_object_name = 'results_list'
    model = IMDBTitleSearchData
    template_name = 'imdb_info_local/search_results.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        return IMDBTitleSearchData.objects.filter(
            Q(title__icontains=query) | Q(blurb__icontains=query)
        )


def home(request):
    titles = IMDBTitleSearchData.objects.count()
    tv = IMDBTitleSearchData.objects.filter(type=IMDBTitleSearchData.TV).count()
    movies = IMDBTitleSearchData.objects.filter(type=IMDBTitleSearchData.MOVIE).count()
    context = {'total_titles': titles,
               'tv_count': tv,
               'movie_count': movies}
    return render(request, 'imdb_info_local/home.html', context)
