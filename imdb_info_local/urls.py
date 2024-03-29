from django.urls import path

from . import views

urlpatterns = [

    path('', views.home, name='home'),
    path('movies/', views.TitleListView.as_view(), name='movie_list'),
    path('movies/mtime/', views.MtimeTitleListView.as_view(), name='movie_mtime'),
    path('movies/ratings/', views.RatingsTitleListView.as_view(), name='movie_ratings'),
    path('tv/', views.TitleListView.as_view(title_type='TV'), name='tv_list'),
    path('tv/mtime/', views.MtimeTitleListView.as_view(title_type='TV'), name='tv_mtime'),
    path('tv/ratings/', views.RatingsTitleListView.as_view(title_type='TV'), name='tv_ratings'),
    path('update/', views.update_title_data, name='title_update'),
    path('search/', views.SearchResultsListView.as_view(), name='search_results'),
]