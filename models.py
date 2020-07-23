from enum import unique
from urllib.parse import quote_plus
import datetime
from django.db import models

from view.models import Detalhamento,Justificativa
from core.firebase import config_firebase

# Create your models here.



class Celulares(models.Model):

    #Principal
    nome = models.CharField('Nome da Pessoa: ', max_length=70)
    telefone = models.CharField('Nº telefone: ', max_length=20)
    empresa = models.CharField('De Onde: ', max_length=50, blank=True)

    #Geral
    localizacao = models.BooleanField('Permite informar localização ?', default=False)
    aplicativo = models.BooleanField('Aplicativo Ativado ?', default=False)
    envio_sms = models.BooleanField('Enviar SMS oa Bloquear ?', default=False)


    status = models.BooleanField('Aplicativo Ativado ?', max_length=2,  default=False)
    data_cadastro = models.DateTimeField('Data Cadastro', auto_now_add=True)

    #Mensagens
    msgpadrao1 = models.CharField('Mensagem Padrão', max_length=100, blank=False)
    msgpadrao2 = models.CharField('Mensagem ',max_length=100 , blank=False)
    msgcomlocalizacao = models.BooleanField('Permite informar localização nas mensagens?', default=False)


    #KM's
    velmin = models.PositiveIntegerField('Velocidade minima km/h', default=0)
    velmax = models.PositiveIntegerField('Velocidade máxima p/ controle', default=0)
    alerta_velmax = models.BooleanField('Enviar alerta de excesso para controle ?',default=False)
    vel_alerta = models.PositiveIntegerField('Velocidade Alerta',default=0)
    emite_bip = models.BooleanField('Emitir bip ao exceder velocidade ?', default=False)


    #Horarios
    hrini_diautil = models.CharField('Horário inicial dias úteis',max_length=5, blank=True,null=True)
    hrfim_diautil = models.CharField('Horário final dias úteis',max_length=5, blank=True,null=True)
    hrini_fimsemana = models.CharField('Horário inicial final semana', max_length=5, blank=True,null=True)
    hrfim_fimsemana = models.CharField('Horário final final semana', max_length=5, blank=True,null=True)
    seg = models.BooleanField('Segunda.', default=False)
    ter = models.BooleanField('Terça.', default=False)
    qua = models.BooleanField('Quarta.', default=False)
    qui = models.BooleanField('Quinta.', default=False)
    sex = models.BooleanField('Sexta.', default=False)
    sab = models.BooleanField('Sabado.', default=False)
    dom = models.BooleanField('Domingo.', default=False)


    #Contatos
    contvip1 = models.CharField('Contato 1', max_length=40,blank=True,null=True)
    telvip1 = models.CharField('Nº Vip 1', max_length=20, blank=True, null=True)
    contvip2 = models.CharField('Contato 2 ', max_length=40, blank=True, null=True)
    telvip2 = models.CharField('Nº Vip 2', max_length=20, blank=True, null=True)
    contvip3 = models.CharField('Contato 3', max_length=40, blank=True, null=True)
    telvip3 = models.CharField('Nº Vip 3', max_length=20, blank=True, null=True)


    #User
    user = models.ForeignKey('accounts.User',verbose_name='Usuário')
    remoto_ativo = models.CharField('acesso remoto',max_length=1,default='P')


    class Meta:
        verbose_name = 'Telefone'
        verbose_name_plural = 'Telefones'
        unique_together = [
            ('telefone','user')
        ]

    def verifica_app(self):
        celular = self.telefone.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
        celular = '+55' + celular

        db = config_firebase()

        json = db.child("celulares").shallow().get()



        if celular in json.val():
            return True
        else:
            return False


    def envia_solicitacao_firebase(self,usuario):

        celular = self.telefone.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')

        celular = str('+55' + celular)
        celular2 = quote_plus(celular)

        db = config_firebase()
        verif_logs = db.child("celulares").child(celular2).child("log_eventos").get()
        if verif_logs.val() != None:
             db.child("celulares").child(celular2).child("log_eventos").remove()
             db.child("celulares").child(celular2).child("justificativa").remove()
             db.child("celulares").child(celular2).child("km").remove()

        nome_usuario = self.user


        solicitacao = {
            'celulares/'+celular+'/solicitacao':{
                'aceito' : True,
                'nome' : str(nome_usuario),
                'username' : usuario
            }
        }
        db.update(solicitacao)










    def sincroniza_firebase(self,usuario):

        celular = self.telefone.replace(' ','').replace('(','').replace(')','').replace('-','')
        celular = '+55'+celular

        db = config_firebase()
        json = db.child("celulares").order_by_key().equal_to(celular).get()

        firebase = json.val()


        user_ctrl_remoto = firebase[celular]["solicitacao"]
        # print(user_ctrl_remoto)

        if user_ctrl_remoto["username"] == usuario and firebase[celular]['config_geral']['controle_remoto'] == True:

            # config padrao
            celular_ativo = self
            celular_ativo.remoto_ativo = 'A'
            celular_ativo.localizacao = firebase[celular]['config_geral']['informa_local']
            celular_ativo.aplicativo = firebase[celular]['config_geral']['controle_remoto']
            celular_ativo.envio_sms = firebase[celular]['config_geral']['envia_sms']
            celular_ativo.status = firebase[celular]['config_geral']['ativado']

            # msg
            celular_ativo.msgpadrao1 = str(firebase[celular]['msg']['msg'])
            celular_ativo.msgpadrao2 = str(firebase[celular]['msg']['msg_vip'])
            celular_ativo.msgcomlocalizacao = firebase[celular]['msg']['msgcomlocalizacao']

            # km
            celular_ativo.velmin = firebase[celular]['km']['velocidade_min']
            celular_ativo.velmax = firebase[celular]['km']['velocidade_max']
            if 'velocidade_alerta' in firebase[celular]['km']:
                celular_ativo.vel_alerta = firebase[celular]['km']['velocidade_alerta']

            celular_ativo.alerta_velmax = firebase[celular]['km']['envia_alerta']
            celular_ativo.emite_bip = firebase[celular]['km']['emite_bip']

            # horario
            celular_ativo.hrini_diautil = firebase[celular]['horario']['util_inicio']
            celular_ativo.hrfim_diautil = firebase[celular]['horario']['util_fim']
            celular_ativo.hrini_fimsemana = firebase[celular]['horario']['fds_inicio']
            celular_ativo.hrfim_fimsemana = firebase[celular]['horario']['fds_fim']
            celular_ativo.seg =      firebase[celular]['horario']['segunda']
            celular_ativo.ter =      firebase[celular]['horario']['terca']
            celular_ativo.qua =      firebase[celular]['horario']['quarta']
            celular_ativo.qui =      firebase[celular]['horario']['quinta']
            celular_ativo.sex =      firebase[celular]['horario']['sexta']
            celular_ativo.sab =      firebase[celular]['horario']['sabado']
            celular_ativo.dom =      firebase[celular]['horario']['domingo']

            # contatovip
            if 'contatovip' in firebase[celular]:
                if '001' in firebase[celular]['contatovip']:
                    celular_ativo.contvip1 = firebase[celular]['contatovip']['001']['nome']
                    celular_ativo.telvip1 = firebase[celular]['contatovip']['001']['fone']
                if '002' in firebase[celular]['contatovip']:
                    celular_ativo.contvip2 = firebase[celular]['contatovip']['002']['nome']
                    celular_ativo.telvip2 =  firebase[celular]['contatovip']['002']['fone']
                if '003' in firebase[celular]['contatovip']:
                    celular_ativo.contvip3 = firebase[celular]['contatovip']['003']['nome']
                    celular_ativo.telvip3 =  firebase[celular]['contatovip']['003']['fone']
            celular_ativo.save()


            # log
            if 'log_eventos' in firebase[celular]:
                for log in firebase[celular]['log_eventos']:
                    if log is None:
                        continue
                    if Detalhamento.objects.filter(dispositivo=self,firebase_id=log["id"]).exists():
                        continue
                    detalhamento = Detalhamento()
                    detalhamento.dispositivo = self
                    detalhamento.data_evento = datetime.datetime.strptime(log["data_hora"],'%d/%m/%Y %H:%M:%S')
                    detalhamento.evento = log["evento"]
                    detalhamento.desc_evento = log["descricao"]
                    detalhamento.localizacao = log["localizacao"]
                    detalhamento.longitude = log["longitude"]
                    detalhamento.latitude = log["latitude"]
                    detalhamento.firebase_id = log["id"]
                    detalhamento.save()

            # justificativa
            if 'justificativa' in firebase[celular]:
                just_pendente = Justificativa.objects.filter(dispositivo=self,justificado=False)
                just_pendente.delete()

                for just in firebase[celular]['justificativa']:
                    if just is None:
                        continue
                    if Justificativa.objects.filter(dispositivo=self,firebase_id=just["id"]).exists():
                        continue
                    justificativa = Justificativa()
                    justificativa.dispositivo = self
                    justificativa.data_evento = datetime.datetime.strptime(just["data_hora"],'%d/%m/%Y %H:%M:%S')
                    justificativa.evento = just["evento"]
                    justificativa.desc_justificativa = just["desc_justificativa"]
                    justificativa.justificado = just["justificado"]
                    justificativa.latitude = just["latitude"]
                    justificativa.longitude = just["longitude"]
                    justificativa.firebase_id = just["id"]
                    justificativa.save()

    def parametros_celular(self):

        if self.remoto_ativo == 'A':

            celular = self.telefone.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
            celular = '+55' + celular

            db = config_firebase()
            json = db.child("celulares").order_by_key().equal_to(celular).get()

            firebase = json.val()

            celular_ativo = self
            celular_ativo.localizacao = firebase[celular]['config_geral']['informa_local']
            celular_ativo.aplicativo = firebase[celular]['config_geral']['controle_remoto']
            celular_ativo.envio_sms = firebase[celular]['config_geral']['envia_sms']
            celular_ativo.status = firebase[celular]['config_geral']['ativado']

            celular_ativo.msgpadrao1 = str(firebase[celular]['msg']['msg'])
            celular_ativo.msgpadrao2 = str(firebase[celular]['msg']['msg_vip'])
            celular_ativo.msgcomlocalizacao = firebase[celular]['msg']['msgcomlocalizacao']

            celular_ativo.velmin = firebase[celular]['km']['velocidade_min']
            celular_ativo.velmax = firebase[celular]['km']['velocidade_max']
            celular_ativo.alerta_velmax = firebase[celular]['km']['envia_alerta']
            if 'velocidade_alerta' in firebase[celular]['km']:
                celular_ativo.vel_alerta = firebase[celular]['km']['velocidade_alerta']
            celular_ativo.emite_bip = firebase[celular]['km']['emite_bip']

            celular_ativo.hrini_diautil = firebase[celular]['horario']['util_inicio']
            celular_ativo.hrfim_diautil = firebase[celular]['horario']['util_fim']
            celular_ativo.hrini_fimsemana = firebase[celular]['horario']['fds_inicio']
            celular_ativo.hrfim_fimsemana = firebase[celular]['horario']['fds_fim']
            celular_ativo.seg = firebase[celular]['horario']['segunda']
            celular_ativo.ter = firebase[celular]['horario']['terca']
            celular_ativo.qua = firebase[celular]['horario']['quarta']
            celular_ativo.qui = firebase[celular]['horario']['quinta']
            celular_ativo.sex = firebase[celular]['horario']['sexta']
            celular_ativo.sab = firebase[celular]['horario']['sabado']
            celular_ativo.dom = firebase[celular]['horario']['domingo']

            if 'contatovip' in firebase[celular]:
                if '001' in firebase[celular]['contatovip']:
                    celular_ativo.contvip1 = firebase[celular]['contatovip']['001']['nome']
                    celular_ativo.telvip1 = firebase[celular]['contatovip']['001']['fone']
                if '002' in firebase[celular]['contatovip']:
                    celular_ativo.contvip2 = firebase[celular]['contatovip']['002']['nome']
                    celular_ativo.telvip2 = firebase[celular]['contatovip']['002']['fone']
                if '003' in firebase[celular]['contatovip']:
                    celular_ativo.contvip3 = firebase[celular]['contatovip']['003']['nome']
                    celular_ativo.telvip3 = firebase[celular]['contatovip']['003']['fone']
            celular_ativo.save()


    def atualiza_parametros(self):

        if self.remoto_ativo == 'A':
            celular = self.telefone.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
            celular = '+55' + celular

            db = config_firebase()

            autalizacao = {
                'celulares/' + celular + '/config_geral': {
                    'ativado': self.status,
                    'controle_remoto' : self.aplicativo,
                    'envia_sms' : self.envio_sms,
                    'informa_local': self.localizacao

                },
                'celulares/'+ celular + '/msg': {
                    'msg' : self.msgpadrao1,
                    'msg_vip': self.msgpadrao2,
                    'msgcomlocalizacao' : self.msgcomlocalizacao
                },
                'celulares/' + celular + '/km': {
                    'emite_bip' : self.emite_bip,
                    'envia_alerta' : self.alerta_velmax,
                    'velocidade_alerta': self.vel_alerta,
                    'velocidade_max': self.velmax,
                    'velocidade_min': self.velmin,

                },
                'celulares/' + celular + '/horario': {
                    'util_inicio': self.hrini_diautil,
                    'util_fim': self.hrfim_diautil,
                    'fds_inicio': self.hrini_fimsemana,
                    'fds_fim': self.hrfim_fimsemana,
                    'segunda': self.seg,
                    'terca': self.ter,
                    'quarta': self.qua,
                    'quinta': self.qui,
                    'sexta': self.sex,
                    'sabado': self.sab,
                    'domingo': self.dom
                },
                'celulares/'+ celular +'/contatovip/001': {
                    'nome' : self.contvip1,
                    'fone' : self.telvip1
                },
                'celulares/' + celular + '/contatovip/002': {
                    'nome': self.contvip2,
                    'fone': self.telvip2
                },
                'celulares/' + celular + '/contatovip/003': {
                    'nome': self.contvip3,
                    'fone': self.telvip3
                }
            }

            db.update(autalizacao)


    def inativa_celular_firebase(self):
        if self.remoto_ativo == 'A':
            celular = self.telefone.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
            celular = '+55' + celular

            db = config_firebase()

            inativa = {
                'celulares/'+ celular + '/config_geral':{
                  'controle_remoto': False
                },
                'celulares/' + celular + '/solicitacao': {
                    'aceito': False,
                    'nome': '',
                    'username': ''
                },
                'celulares' + celular + '/config_geral':{
                    'controle_remoto' : False
                }
            }
            db.update(inativa)


    def __str__(self):
        return self.telefone




class Horarios(models.Model):

    hrini = models.TimeField('Horario inicial',blank=True)
    hrfim = models.TimeField('Horario Final',blank=True)
    seg = models.BooleanField('Segunda.',default=False)
    ter = models.BooleanField('Terça.', default=False)
    qua = models.BooleanField('Quarta.', default=False)
    qui = models.BooleanField('Quinta.', default=False)
    sex = models.BooleanField('Sexta.', default=False)
    sab = models.BooleanField('Sabado.', default=False)
    dom = models.BooleanField('Domingo.', default=False)
    user = models.ForeignKey('accounts.User', verbose_name='Usuário')
    dispositivo = models.ForeignKey('celulares.Celulares',verbose_name='Cod. Celular Vinculado')


    class Meta:
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'


    #
    # def __str__(self):
    #     return self.dispositivo








class ContVip(models.Model):

    contato = models.CharField('Contato',max_length=40 ,blank=True)
    num_tel = models.CharField('Numero Contato', max_length=20 ,blank=True)
    user = models.ForeignKey('accounts.User', verbose_name='Usuário')
    dispositivo = models.ForeignKey('celulares.Celulares',verbose_name='Cod. Celular Vinculado')


    class Meta:
        verbose_name = 'Contato Vip'
        verbose_name_plural = 'Contatos Vip'



    def __str__(self):
        return self.contato
