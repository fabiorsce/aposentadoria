from django.contrib import admin
from simulador.models import Ipca, Contribuinte, Contribuicao
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class IpcaAdmin(admin.ModelAdmin):
	fields = ('ano_mes', 'indice', 'acumulado')
	list_display = ('ano_mes', 'indice', 'acumulado', 'ano', 'mes')
	order_by = ('-ano_mes')
admin.site.register(Ipca, IpcaAdmin)    

class ContribuinteAdmin(admin.ModelAdmin):
	list_display = ('nome', 'sexo', 'data_nascimento', 'data_simulacao')
admin.site.register(Contribuinte, ContribuinteAdmin)    

class ContribuicaoResource(resources.ModelResource):

    class Meta:
        model = Contribuicao

class ContribuicaoAdmin(ImportExportModelAdmin):
	list_display = ('contribuinte', 'ano_mes','valor_contribuicao', 'salario_contribuicao', 'tipo', 'decimo_terceiro', 'salario_atualizado')
	resource_class = ContribuicaoResource
admin.site.register(Contribuicao, ContribuicaoAdmin)    
