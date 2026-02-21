from django.test import TestCase
from django.urls import reverse
from .models import CustomUser, JobCard, JobDetail

class JobCardTests(TestCase):
    def setUp(self):
        self.technician = CustomUser.objects.create_user(username='tech', password='password', role='technician')
        self.manager = CustomUser.objects.create_user(username='manager', password='password', role='manager')
        self.admin = CustomUser.objects.create_user(username='admin_user', password='password', role='admin')

    def test_jobcard_creation(self):
        self.client.login(username='tech', password='password')
        response = self.client.post(reverse('create_jobcard'), {
            'client_name': 'Test Client',
            'company_name': 'Test Company'
        })
        self.assertEqual(response.status_code, 302) # Redirects to detail
        self.assertEqual(JobCard.objects.count(), 1)
        jobcard = JobCard.objects.first()
        self.assertEqual(jobcard.technician, self.technician)
        self.assertTrue(jobcard.jobcard_id.startswith('JC-'))

    def test_technician_dashboard(self):
        self.client.login(username='tech', password='password')
        response = self.client.get(reverse('technician_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_manager_access(self):
        self.client.login(username='manager', password='password')
        response = self.client.get(reverse('manager_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_role_redirect(self):
        self.client.login(username='tech', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('technician_dashboard'))
