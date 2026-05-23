from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy('admin_login')

    def test_func(self):
        return self.request.user.is_staff