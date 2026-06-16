from django.core.management.base import BaseCommand
from core.models import Jogador, Torneio, RegistroTorneio, ResultadoTorneio


def corrigir_texto(texto):
    if not texto:
        return texto

    trocas = {
        'Ã¡': 'á',
        'Ã ': 'à',
        'Ã¢': 'â',
        'Ã£': 'ã',
        'Ã¤': 'ä',

        'Ã©': 'é',
        'Ãª': 'ê',
        'Ã¨': 'è',

        'Ã­': 'í',
        'Ã®': 'î',

        'Ã³': 'ó',
        'Ã´': 'ô',
        'Ãµ': 'õ',
        'Ã²': 'ò',

        'Ãº': 'ú',
        'Ã¼': 'ü',

        'Ã§': 'ç',

        'Ã': 'Á',
        'Ã€': 'À',
        'Ã‚': 'Â',
        'Ãƒ': 'Ã',
        'Ã‰': 'É',
        'ÃŠ': 'Ê',
        'Ã': 'Í',
        'Ã“': 'Ó',
        'Ã”': 'Ô',
        'Ã•': 'Õ',
        'Ãš': 'Ú',
        'Ã‡': 'Ç',

        '┬¥': 'í',
        '├í': 'á',
        '├ó': 'ó',
        '├ú': 'ú',
        '├º': 'ç',
        '├úo': 'ão',
        '├úes': 'ões',
        'þÒ': 'çã',

        'Ç': 'C',
'├®': 'é',
'├íbio': 'ábio',
'├®nio': 'ânio',
'├®o': 'ão',
'├¡': 'í',
'├⌐': 'é',
'Ãº': 'ú',
'Ã©': 'é',
'Ã£': 'ã',
'Ã§': 'ç',
'Ã´': 'ô',
    }

    novo = texto

    for errado, certo in trocas.items():
        novo = novo.replace(errado, certo)

        correcoes_diretas = {
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