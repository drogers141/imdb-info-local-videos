from django.views import generic

from .models import IMDBTitleSearchData


class TitleListView(generic.ListView):
    title_type = 'Movies' # or 'TV'
    model = IMDBTitleSearchData
    context_object_name = 'title_list'
    template_name = 'imdb_rt_reviews/titles.html'

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
