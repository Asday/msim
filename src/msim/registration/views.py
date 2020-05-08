from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import FormView


class Register(FormView):
    form_class = UserCreationForm
    success_url = reverse_lazy('mortgages:list')
    template_name = "registration/register.html"

    def form_valid(self, form):
        login(self.request, form.save())

        return super().form_valid(form)
