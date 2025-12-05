import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Project, Task
from .forms import ProjectForm

User = get_user_model()


class TaskModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass123")
        self.project = Project.objects.create(name="Demo", owner=self.owner)

    def test_create_task_defaults(self):
        task = Task.objects.create(title="Example", project=self.project)
        self.assertEqual(task.status, Task.STATUS_TODO)
        self.assertEqual(task.priority, Task.PRIORITY_MEDIUM)
        self.assertIsNone(task.assignee)

    def test_invalid_status_rejected(self):
        task = Task(title="Bad status", project=self.project, status="invalid")
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_overdue_property(self):
        yesterday = timezone.now().date() - datetime.timedelta(days=1)
        task = Task.objects.create(
            title="Overdue task", project=self.project, deadline=yesterday
        )
        self.assertTrue(task.is_overdue)


class ProjectViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="owner", password="pass123")
        self.member = User.objects.create_user(username="member", password="pass123")
        self.outsider = User.objects.create_user(username="outsider", password="pass123")

        self.project = Project.objects.create(name="Project Alpha", owner=self.owner)
        self.project.members.add(self.member)
        self.task = Task.objects.create(
            title="Initial task",
            project=self.project,
            assignee=self.member,
            deadline=timezone.now().date(),
        )

    def test_project_list_filters_by_membership(self):
        self.client.login(username="owner", password="pass123")
        response = self.client.get(reverse("boards:project-list"))
        self.assertContains(response, self.project.name)

        self.client.logout()
        self.client.login(username="outsider", password="pass123")
        response = self.client.get(reverse("boards:project-list"))
        self.assertNotContains(response, self.project.name)

    def test_project_create_sets_owner_and_members(self):
        self.client.login(username="owner", password="pass123")
        response = self.client.post(
            reverse("boards:project-create"),
            {
                "name": "New Project",
                "description": "Test proj",
                "members": [self.member.pk],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        project = Project.objects.get(name="New Project")
        self.assertEqual(project.owner, self.owner)
        # Owner is auto-added as member
        self.assertTrue(project.members.filter(id=self.owner.id).exists())

    def test_project_update_restricted_to_owner(self):
        self.client.login(username="member", password="pass123")
        response = self.client.get(reverse("boards:project-update", args=[self.project.pk]))
        self.assertEqual(response.status_code, 404)

        self.client.logout()
        self.client.login(username="owner", password="pass123")
        response = self.client.post(
            reverse("boards:project-update", args=[self.project.pk]),
            {"name": "Renamed", "description": "Updated", "members": [self.member.pk]},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Renamed")

    def test_project_delete_restricted_to_owner(self):
        self.client.login(username="member", password="pass123")
        response = self.client.post(reverse("boards:project-delete", args=[self.project.pk]))
        self.assertEqual(response.status_code, 404)

        self.client.logout()
        self.client.login(username="owner", password="pass123")
        response = self.client.post(
            reverse("boards:project-delete", args=[self.project.pk]), follow=True
        )
        self.assertRedirects(response, reverse("boards:project-list"))
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_project_detail_access_control(self):
        self.client.login(username="member", password="pass123")
        response = self.client.get(reverse("boards:project-detail", args=[self.project.pk]))
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        self.client.login(username="outsider", password="pass123")
        response = self.client.get(reverse("boards:project-detail", args=[self.project.pk]))
        self.assertEqual(response.status_code, 404)

    def test_create_task_view(self):
        self.client.login(username="owner", password="pass123")
        response = self.client.post(
            reverse("boards:task-create", args=[self.project.pk]),
            {
                "title": "New task",
                "description": "Details",
                "status": Task.STATUS_TODO,
                "priority": Task.PRIORITY_HIGH,
                "deadline": timezone.now().date(),
                "assignee": self.member.pk,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Task.objects.filter(title="New task").exists())

    def test_update_task_view(self):
        self.client.login(username="member", password="pass123")
        response = self.client.post(
            reverse("boards:task-update", args=[self.task.pk]),
            {
                "title": "Updated task",
                "description": "Updated details",
                "status": Task.STATUS_DOING,
                "priority": Task.PRIORITY_LOW,
                "deadline": timezone.now().date(),
                "assignee": self.member.pk,
            },
        )
        self.assertRedirects(
            response, reverse("boards:project-detail", args=[self.project.pk])
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Updated task")
        self.assertEqual(self.task.status, Task.STATUS_DOING)

    def test_delete_task_view(self):
        self.client.login(username="owner", password="pass123")
        response = self.client.post(
            reverse("boards:task-delete", args=[self.task.pk]),
            follow=True,
        )
        self.assertRedirects(
            response, reverse("boards:project-detail", args=[self.project.pk])
        )
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_status_update_view(self):
        self.client.login(username="member", password="pass123")
        response = self.client.post(
            reverse("boards:task-status", args=[self.task.pk]),
            {"status": Task.STATUS_DONE},
        )
        self.assertRedirects(
            response, reverse("boards:project-detail", args=[self.project.pk])
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.STATUS_DONE)

    def test_access_blocked_for_non_members(self):
        self.client.login(username="outsider", password="pass123")
        response = self.client.get(reverse("boards:task-update", args=[self.task.pk]))
        self.assertEqual(response.status_code, 404)
