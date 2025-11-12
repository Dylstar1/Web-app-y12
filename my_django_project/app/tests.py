from django.test import TestCase
from django.urls import reverse

class IndexPageTests(TestCase):
    def test_index_page_status_code(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_index_page_template_used(self):
        response = self.client.get(reverse('index'))
        self.assertTemplateUsed(response, 'index.html')

    def test_index_page_contains_correct_html(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'welcome to the index page')