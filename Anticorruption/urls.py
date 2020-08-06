"""Anticorruption URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from home import views

# urlpatterns = [
#     path('admin/', admin.site.urls),
# ]

urlpatterns = [
    path('', views.login, name='login'),
    path('register', views.register, name='register'),
    path('sendotp/', views.sendOtp, name="sendOtp"),

    # path('home', views.home, name='home'),
    path('fir/<user>/', views.home, name='fir'),
    path('noc/<user>/', views.noc, name='noc'),
    path('ncr/<user>/', views.ncr, name='ncr'),
    path('paidbribe/<user>/', views.paidBribe, name='paidbribe'),
    path('hotreport/<user>/', views.hotReport, name='hotreport'),
    path('rti/<user>/', views.rti, name='rti'),
    path('unusual/<user>/', views.unusualBehaviour, name='unusual'),

    # path('details/<user>/<uid>/<case_id>/', views.details, name='details'),
    path('details/<category>/<user>/<uid>/<case_id>/', views.details, name='details'),
    path('logout',views.logout, name='logout'), 
    path('police', views.police, name='police'),
    path('faceevidence/<doc_id>/<rep_id>/',views.faceevidence,name='faceevidence'),
    
]
