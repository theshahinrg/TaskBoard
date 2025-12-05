from django.urls import path

from . import views

app_name = "boards"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="project-list"),
    path("projects/add/", views.ProjectCreateView.as_view(), name="project-create"),
    path("projects/<int:pk>/edit/", views.ProjectUpdateView.as_view(), name="project-update"),
    path("projects/<int:pk>/delete/", views.ProjectDeleteView.as_view(), name="project-delete"),
    path("projects/<int:pk>/", views.ProjectDetailView.as_view(), name="project-detail"),
    path(
        "projects/<int:project_pk>/tasks/add/",
        views.TaskCreateView.as_view(),
        name="task-create",
    ),
    path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task-update"),
    path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task-delete"),
    path(
        "tasks/<int:pk>/status/",
        views.TaskStatusUpdateView.as_view(),
        name="task-status",
    ),
]
