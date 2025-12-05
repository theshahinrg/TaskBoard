from django import forms
from django.contrib.auth import get_user_model

from .models import Project

User = get_user_model()


class ProjectForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple,
        help_text="Select users who can access this project.",
    )

    class Meta:
        model = Project
        fields = ["name", "description", "members"]

    def save(self, commit=True):
        project = super().save(commit=False)
        if commit:
            project.save()
            self.save_m2m()
            # Ensure owner is always a member for visibility
            if project.owner_id and not project.members.filter(id=project.owner_id).exists():
                project.members.add(project.owner)
        return project
