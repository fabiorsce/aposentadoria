from django.shortcuts import render, redirect
from django.http import HttpResponse
from simulador.models import Ipca, Contribuinte, Contribuicao
from decimal import Decimal
import csv
import io
from django.contrib import messages
from simulador.forms import ImportarContribuicaoForm, ImportarIpcaForm
from django.db.models import Avg
from datetime import datetime


def importar_ipca(request):

	ipcas = Ipca.objects.all().order_by('ano_mes')

	if request.method == 'POST':
		form = ImportarIpcaForm(request.POST, request.FILES)
		if form.is_valid():
			importar_arquivo_ipca(request.FILES['arquivo'])
			messages.success(request, 'Arquivo importado com sucesso!')
			form = ImportarIpcaForm()
		return render(request, 'ipca.html', {'ipcas':ipcas, 'form': form})
	else:
		form = ImportarIpcaForm()

	return render(request, 'ipca.html', {'ipcas':ipcas, 'form': form})	


def importar_arquivo_ipca(arquivo_csv):

	Ipca.objects.all().delete()

	nome_arquivo = '/tmp/ipca.csv'

	with open(nome_arquivo, 'wb+') as destination:
		for chunk in arquivo_csv.chunks():
			destination.write(chunk)

	with open(nome_arquivo) as csvfile:
		reader = csv.reader(csvfile, delimiter=';')
		for row in reader:
			print(row)
			ano = row[0]
			mes = row[1]
			mes = mes.zfill(2)
			ano_mes = ''.join((ano,mes))
			indice = row[2]
			indice = Decimal(indice.replace(',', '.'))

			i = Ipca(ano_mes=ano_mes, indice=indice)
			i.save()


	# Gambiarra para deixar os anos completos
	ipca_mais_antigo = Ipca.objects.all().order_by('ano_mes')[0]
	ano = ipca_mais_antigo.ano
	mes = ipca_mais_antigo.mes
	for i in range(1,int(mes)):
		ano_mes = ''.join(( ano, str(i).zfill(2) ))
		novo_ipca = Ipca(ano_mes=ano_mes, indice=0)
		novo_ipca.save()

	atualizar_ipca_acumulado()

def atualizar_ipca_acumulado():

	ipcas = Ipca.objects.all().order_by('-ano_mes')

	acumulado = 1
	for i in ipcas:
		i.acumulado = acumulado * (1+i.indice/100)
		i.save()
		acumulado = i.acumulado

def ipca(request):

	form = ImportarIpcaForm()
	ipcas = Ipca.objects.all().order_by('ano_mes')

	return render(request, 'ipca.html', {'ipcas':ipcas, 'form': form})	

def simular_beneficios(request, contribuinte_id):

	# Atualiza os IPCAS
	atualizar_ipca_acumulado()

	# Atualiza os salarios de contribuicao para a data atual
	ipcas = Ipca.objects.all()
	contribuinte = Contribuinte.objects.get(id=contribuinte_id)

	if Contribuicao.objects.filter(contribuinte=contribuinte).count() == 0:
		messages.warning(request, 'Contribuinte não possui contribuições.')
		return redirect('contribuinte')


	for c in Contribuicao.objects.filter(contribuinte=contribuinte):
		ipca = ipcas.filter(ano_mes=c.ano_mes)[0]
		c.salario_atualizado = c.salario_contribuicao * ipca.acumulado
		c.save()

	media_todas_contribuicoes = Contribuicao.objects.filter(
			contribuinte=contribuinte).aggregate(Avg('salario_atualizado'))['salario_atualizado__avg']

	if media_todas_contribuicoes:
		contribuinte.beneficio_media_todas_contribuicoes = Decimal(media_todas_contribuicoes)

	# Calcula a média das 80% maiores cotribuicoes
	numero_contribuicoes = Contribuicao.objects.filter(contribuinte=contribuinte).count()
	qtd_oitenta_por_cento = round(0.8 * numero_contribuicoes)
	melhores_contribuicoes = Contribuicao.objects.filter(contribuinte=contribuinte
								).order_by('-salario_atualizado')[0:qtd_oitenta_por_cento]
	media = melhores_contribuicoes.aggregate(Avg('salario_atualizado'))['salario_atualizado__avg']

	if contribuinte.data_ingresso_servico_publico.isoformat() < datetime(2004,1,1).isoformat():
		ultima_contribuicao = Contribuicao.objects.filter(contribuinte=contribuinte).order_by('-ano_mes')[0]
		contribuinte.beneficio_regra_atual = ultima_contribuicao.salario_atualizado
	else:
		contribuinte.beneficio_regra_atual = media

	
	if not contribuinte.beneficio_inss:
		contribuinte.beneficio_inss = 5645.80

	lista_regime_proprio = [Contribuicao.UNIAO, Contribuicao.ESTADO, Contribuicao.MUNICIPIO]
	ano_mes_ing_ser_pub = contribuinte.data_ingresso_servico_publico.isoformat()[0:7].replace('-','')




	# Calculo do beneficio especial
	qtd_total_contrib_reg_proprio = Contribuicao.objects.filter(
				contribuinte=contribuinte, 
				ano_mes__gte='199407',
				tipo__in=lista_regime_proprio).filter(
						ano_mes__gte=ano_mes_ing_ser_pub).count()

	qtd_oitenta_por_cento = round(0.8 * qtd_total_contrib_reg_proprio)

	melhores_contrib_reg_proprio = Contribuicao.objects.filter(
				contribuinte=contribuinte, 
				ano_mes__gte='199407', 
				tipo__in=lista_regime_proprio).filter(
						ano_mes__gte=ano_mes_ing_ser_pub
						).order_by('-salario_atualizado')[0:qtd_oitenta_por_cento]
	media = melhores_contrib_reg_proprio.aggregate(Avg('salario_atualizado'))['salario_atualizado__avg']

	beneficio_especial = Decimal(media) - contribuinte.beneficio_inss
	if contribuinte.sexo == contribuinte.MASCULINO:
		beneficio_especial = beneficio_especial * qtd_total_contrib_reg_proprio/455
	else:
		beneficio_especial = beneficio_especial * qtd_total_contrib_reg_proprio/390

	contribuinte.beneficio_especial = beneficio_especial

	# Calculo da economia
	ultima_contribuicao = Contribuicao.objects.order_by('-ano_mes')[0]
	economia = (ultima_contribuicao.salario_atualizado * Decimal(0.11)) - (contribuinte.beneficio_inss * Decimal(0.11))
	contribuinte.economia = economia

	contribuinte.data_simulacao = datetime.today()

	contribuinte.save()

	messages.success(request, 'Cálculo realizado com sucesso.')
	return redirect('contribuinte')


def importar_arquivo_contribuicoes(contribuinte_id, arquivo_csv):

	contribuinte = Contribuinte.objects.get(id=contribuinte_id)

	nome_arquivo = ''.join(('/tmp/contri_', contribuinte.nome, '.csv'))

	with open(nome_arquivo, 'wb+') as destination:
		for chunk in arquivo_csv.chunks():
			destination.write(chunk)

	with open(nome_arquivo) as csvfile:
		reader = csv.DictReader(csvfile, delimiter=';')
		for row in reader:
			ano_mes = row['ano_mes']
			salario_contribuicao = Decimal(row['salario_contribuicao'].replace(',', '.'))
			tipo=row['tipo'] or 'U'

			if 'valor_contribuicao' in row and row['valor_contribuicao']:
				valor_contribuicao = Decimal(row['valor_contribuicao'].replace(',', '.'))
			else:
				valor_contribuicao = None
			if 'decimo_terceiro' in row and row['decimo_terceiro'] and row['decimo_terceiro'] in ('S','Y'):
				decimo_terceiro = True
			else:
				decimo_terceiro = False

			i, created = Contribuicao.objects.get_or_create(
					contribuinte=contribuinte,
					ano_mes=ano_mes, 
					tipo=tipo,
					decimo_terceiro=decimo_terceiro
				)
			if i.valor_contribuicao:
				i.valor_contribuicao +=valor_contribuicao
			else:
				i.valor_contribuicao = valor_contribuicao

			if i.salario_contribuicao:
				i.salario_contribuicao += salario_contribuicao
			else:
				i.salario_contribuicao = salario_contribuicao
			'''
			i = Contribuicao(contribuinte=contribuinte,
							ano_mes=ano_mes, 
							valor_contribuicao=valor_contribuicao,
							salario_contribuicao=salario_contribuicao,
							tipo=tipo,
							decimo_terceiro=decimo_terceiro
							)
			'''
			i.save()


def contribuinte(request):

	contribuintes = Contribuinte.objects.filter()
	#contribuinteTable = ContribuinteTable(Contribuinte.objects.all(), prefix='1-')
	#RequestConfig(request).configure(contribuinteTable)
	return render(request, 'contribuinte.html', {'contribuintes': contribuintes })	


def contribuinte_detalhe(request, contribuinte_id):

	contribuinte = Contribuinte.objects.get(id=contribuinte_id)
	contribuicoes = Contribuicao.objects.filter(contribuinte=contribuinte)


	if request.method == 'POST':
		form = ImportarContribuicaoForm(request.POST, request.FILES)
		if form.is_valid():
			importar_arquivo_contribuicoes(contribuinte_id, request.FILES['arquivo'])
			messages.success(request, 'Arquivo importado com sucesso')
			form = ImportarContribuicaoForm()
			contribuicoes = Contribuicao.objects.filter(contribuinte=contribuinte)
		return render(request, 'contribuinte_detalhe.html',{'contribuinte': contribuinte, 
			'contribuicoes': contribuicoes,
			'form': form
			})	
	else:
		form = ImportarContribuicaoForm()


	return render(request, 'contribuinte_detalhe.html',{'contribuinte': contribuinte, 
			'contribuicoes': contribuicoes,
			'form': form
			})	

def excluir_contribuicoes(request, contribuinte_id):

	c = Contribuinte.objects.get(id=contribuinte_id)
	c.data_simulacao = None
	c.beneficio_regra_atual = None
	c.beneficio_media_todas_contribuicoes = None
	c.beneficio_especial = None
	c.economia = None
	c.save()
	Contribuicao.objects.filter(contribuinte=c).delete()

	messages.success(request, 'Contribuições foram excluidas e os calculos foram zerados.')

	contribuintes = Contribuinte.objects.filter()
	return render(request, 'contribuinte.html', {'contribuintes': contribuintes })	