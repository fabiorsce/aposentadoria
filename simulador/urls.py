"""aposentadoria URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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

from django.urls import path
from simulador import views

urlpatterns = [
    path('contribuinte/', views.contribuinte, name='contribuinte'),
    path('contribuinte_detalhe/<int:contribuinte_id>/', views.contribuinte_detalhe, name='contribuinte_detalhe'),
    path('excluir_contribuicoes/<int:contribuinte_id>/', views.excluir_contribuicoes, name='excluir_contribuicoes'),
	path('ipca/', views.ipca, name='ipca'),
    path('importar_ipca/', views.importar_ipca, name='importar_ipca'),
    path('simular_beneficios/<int:contribuinte_id>/', views.simular_beneficios, name='simular_beneficios'),
    path('atualizar_ipca_acumulado/', views.atualizar_ipca_acumulado, name='atualizar_ipca_acumulado'),
]
