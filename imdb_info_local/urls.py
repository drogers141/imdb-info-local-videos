from django.urls import path

from . import views

urlpatterns = [

    path('movies/', views.TitleListView.as_view(), name='movie_list'),
    path('movies/mtime/', views.MtimeTitleListView.as_view(), name='movie_mtime'),
    path('tv/', views.TitleListView.as_view(title_type='TV'), name='tv_list'),
    path('tv/mtime/', views.MtimeTitleListView.as_view(title_type='TV'), name='tv_mtime'),
    path('update/', views.update_title_data, name='title_update')
]