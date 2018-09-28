import os
import time

from django.shortcuts import render
from django.http import JsonResponse
from django.views import View

from .models import ScrapeRequest
from .tasks import scrape

# Create your views here.


class HomeView(View):
    template_name = 'home/index.html'
    csv_path = 'csv/requested_files/'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        urls = request.POST.get('urls')
        subject = request.POST.get('subject')

        file_path = self.csv_path + time.strftime("%Y_%m_%d_%H_%M_%S_") + email + '.csv'

        if not os.path.exists(self.csv_path):
            os.makedirs(self.csv_path)

        with open(file_path, 'w') as file:
            file.write(urls)

        scrape_request = ScrapeRequest.objects.create(email=email, csv_path=file_path, subject=subject)
        scrape_request.save()

        # f = scrape(scrape_request.id)
        scrape.delay(scrape_request.id)

        return JsonResponse({
            'status': 'success',
            'message': 'We will send the result as CSV file to your email.'
        })

