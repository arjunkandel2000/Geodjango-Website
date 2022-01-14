from django.shortcuts import render
from .models import Shp
from tiff.models import Tiff

# Create your views here.
def index(request):
    shp = Shp.objects.all()
    context = {shp : 'shp'}
    tiff = Tiff.objects.all()
    context = {tiff : 'tiff'}
    return render(request,'index.html',context)
    # ,{shp : 'shp', tiff : 'tiff'}


    
    