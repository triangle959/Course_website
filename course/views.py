from django.shortcuts import render
from django.views import View
# Create your views here.

class NewIndexView(View):
    def get(self, request):
        try:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                request.session['ip'] = x_forwarded_for.split(',')[0]  # 所以这里是真实的ip
            else:
                request.session['ip'] = request.META.get('REMOTE_ADDR')  # 这里获得代理ip
        except:
            request.session['ip'] = None
        return render(request, 'course/index.html', locals())

class DagangView(View):
    def get(self, request):
        return render(request, 'course/dagang.html')


class ContentView(View):
    def get(self, request):
        return render(request, 'course/content.html')

class ShiyanView(View):
    def get(self, request):
        return render(request, 'course/shixun.html')

class KejianView(View):
    def get(self, request):
        return render(request, 'course/kejian.html')

class ShiziView(View):
    def get(self, request):
        return render(request, 'course/shizi.html')

class XitiView(View):
    def get(self, request):
        return render(request, 'course/xiti.html')