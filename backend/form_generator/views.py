import os
from django.http import FileResponse, Http404
from django.conf import settings
from django.views import View

class FrontendAppView(View):
    def get(self, request):
        index_path = os.path.join(settings.STATIC_ROOT, "index.html")
        if os.path.exists(index_path):
            return FileResponse(open(index_path, "rb"))
        raise Http404("index.html not found. Did you build the frontend?")
