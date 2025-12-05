from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic

from .forms import ProjectForm
from .models import Project, Task


class ProjectAccessMixin(LoginRequiredMixin):
    """Restrict project access to owners and members."""

    def get_queryset(self):
        base_qs = super().get_queryset()
        user = self.request.user
        return base_qs.filter(Q(owner=user) | Q(members=user)).distinct()


class TaskAccessMixin(LoginRequiredMixin):
    """Restrict task access through related project membership."""

    def get_queryset(self):
        base_qs = super().get_queryset()
        user = self.request.user
        return base_qs.filter(
            Q(project__owner=user) | Q(project__members=user)
        ).select_related("project", "assignee")


class ProjectListView(ProjectAccessMixin, generic.ListView):
    model = Project
    template_name = "boards/project_list.html"
    context_object_name = "projects"


class ProjectDetailView(ProjectAccessMixin, generic.DetailView):
    model = Project
    template_name = "boards/project_detail.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = self.object.tasks.select_related("assignee")
        context["status_columns"] = [
            (status, label, tasks.filter(status=status))
            for status, label in Task.STATUS_CHOICES
        ]
        context["is_owner"] = self.request.user == self.object.owner
        return context


class ProjectOwnerAccessMixin(ProjectAccessMixin):
    """Restrict actions to project owners only."""

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class ProjectCreateView(LoginRequiredMixin, generic.CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "boards/project_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("boards:project-detail", args=[self.object.pk])


class ProjectUpdateView(ProjectOwnerAccessMixin, generic.UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "boards/project_form.html"

    def get_success_url(self):
        return reverse("boards:project-detail", args=[self.object.pk])


class ProjectDeleteView(ProjectOwnerAccessMixin, generic.DeleteView):
    model = Project
    template_name = "boards/project_confirm_delete.html"
    context_object_name = "project"
    success_url = reverse_lazy("boards:project-list")


class TaskCreateView(LoginRequiredMixin, generic.CreateView):
    model = Task
    fields = ["title", "description", "status", "priority", "deadline", "assignee"]
    template_name = "boards/task_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs["project_pk"])
        if not self._user_can_access(request.user, self.project):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.project = self.project
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["action"] = "Create"
        return context

    def get_success_url(self):
        return reverse("boards:project-detail", args=[self.project.pk])

    @staticmethod
    def _user_can_access(user, project: Project) -> bool:
        return project.owner_id == user.id or project.members.filter(id=user.id).exists()


class TaskUpdateView(TaskAccessMixin, generic.UpdateView):
    model = Task
    fields = ["title", "description", "status", "priority", "deadline", "assignee"]
    template_name = "boards/task_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        context["action"] = "Update"
        return context

    def get_success_url(self):
        return reverse("boards:project-detail", args=[self.object.project_id])


class TaskDeleteView(TaskAccessMixin, generic.DeleteView):
    model = Task
    template_name = "boards/task_confirm_delete.html"
    context_object_name = "task"

    def get_success_url(self):
        return reverse("boards:project-detail", args=[self.object.project_id])


class TaskStatusUpdateView(TaskAccessMixin, generic.UpdateView):
    model = Task
    fields = ["status"]
    template_name = "boards/task_status_form.html"

    def get_success_url(self):
        return reverse("boards:project-detail", args=[self.object.project_id])
