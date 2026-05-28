from django.urls import path

from .views import ImageProxyView, SearchAllView, SearchView, TaskStatusView

urlpatterns = [
    path('search/', SearchView.as_view(), name='search'),
    path('search/all/', SearchAllView.as_view(), name='search-all'),
    path('status/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
    path('image/', ImageProxyView.as_view(), name='image-proxy'),
]
