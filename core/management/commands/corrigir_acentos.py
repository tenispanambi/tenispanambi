from django.core.management.base import BaseCommand
from core.models import Jogador, Torneio, RegistroTorneio, ResultadoTorneio


def corrigir_texto(texto):
    if not texto:
        return texto

    novo = texto

    trocas = {
        'Ã¡': 'á',
        'Ã ': 'à',
        'Ã¢': 'â',
        'Ã£': 'ã',
        'Ã©': 'é',
        'Ãª': 'ê',
        'Ã­': 'í',
        'Ã³': 'ó',
        'Ã´': 'ô',
        'Ãµ': 'õ',
        'Ãº': 'ú',
        'Ã§': 'ç',
        'Ã‡': 'Ç',
        '�': 'í',
    }

    for errado, certo in trocas.items():
        novo = novo.replace(errado, certo)

    correcoes_diretas = {
        'Cícero Malheiros': 'Cícero Malheiros',
        'C�cero Malheiros': 'Cícero Malheiros',
        'Fernando Zampr�nio': 'Fernando Zamprônio',
        'F�bio Schirmer': 'Fábio Schirmer',
        'Jo�o Libreloff': 'João Libreloff',
        'Jo�o Stamm': 'João Stamm',
        'Jo�o Vitor': 'João Vitor',
        'Lu�s Corr�a': 'Luís Corrêa',
    }

    for errado, certo in correcoes_diretas.items():
        novo = novo.replace(errado, certo)

    return novo


class Command(BaseCommand):
    help = 'Corrige textos com acentuação quebrada no banco'

    def handle(self, *args, **kwargs):

        total = 0

        modelos_campos = [
            (Jogador, ['nome', 'cidade', 'instagram', 'telefone', 'raquete', 'clube', 'frase_pessoal']),
            (Torneio, ['nome', 'observacoes']),
            (RegistroTorneio, ['nome', 'local', 'observacoes']),
            (ResultadoTorneio, ['categoria', 'campeao', 'vice']),
        ]

        for modelo, campos in modelos_campos:

            for obj in modelo.objects.all():

                alterou = False

                for campo in campos:

                    if not hasattr(obj, campo):
                        continue

                    valor = getattr(obj, campo)

                    if isinstance(valor, str):

                        corrigido = corrigir_texto(valor)

                        if corrigido != valor:
                            setattr(obj, campo, corrigido)
                            alterou = True

                if alterou:
                    obj.save()
                    total += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Corrigido: {modelo.__name__} ID {obj.id}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Correção finalizada. Registros alterados: {total}'
            )
        )