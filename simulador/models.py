from django.db import models
from decimal import Decimal

class Ipca(models.Model):
    
    ano_mes = models.CharField(max_length=6, null=False, blank=False, db_index=True)
    indice = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    acumulado = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    
    def __str__(self):
        return self.ano_mes

    @property
    def ano(self):
    	return self.ano_mes[0:4]

    @property
    def mes(self):
    	return self.ano_mes[4:6]

class Contribuinte(models.Model):

    MASCULINO = 'M'
    FEMININO = 'F'
    SEXO = ( 
              (MASCULINO, 'Masculino'),
              (FEMININO, 'Feminino'),
            )
    nome = models.CharField(max_length=100, null=False, blank=False)
    sexo = models.CharField(max_length=1, choices=SEXO, default=MASCULINO, null=False, blank=False)
    data_nascimento = models.DateTimeField(null=False, blank=False)
    data_ingresso_servico_publico = models.DateTimeField(null=False, blank=False)

    data_simulacao = models.DateTimeField(null=True, blank=True)
    beneficio_regra_atual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    beneficio_media_todas_contribuicoes = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    beneficio_inss = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=5645.80)
    beneficio_especial = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    economia = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.nome

    @property
    def economia_sem_imposto(self):
        if self.economia:
            return self.economia * 0.8
        return None

class Contribuicao(models.Model):

    UNIAO = 'U'
    ESTADO = 'E'
    MUNICIPIO = 'M'
    GERAL = 'G'
    TIPOS = ( 
                          (UNIAO, 'Regime prórpio - União'),
                          (ESTADO, 'Regime prórpio - Estado'),
                          (MUNICIPIO, 'Regime prórpio - Município'),
                          (GERAL, 'Regime geral - INSS'),
                        )

    contribuinte = models.ForeignKey(Contribuinte, null=False, blank=False,on_delete=models.CASCADE)
    ano_mes = models.CharField(max_length=6, null=False, blank=False)
    valor_contribuicao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salario_contribuicao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salario_atualizado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo = models.CharField(max_length=1, choices=TIPOS, default=UNIAO, null=False, blank=False)
    decimo_terceiro = models.BooleanField(default=False)

    def __str__(self):
        return self.ano_mes

