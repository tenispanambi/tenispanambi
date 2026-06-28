from .models import Jogador, Notificacao


def notificacoes_usuario(request):
    if not request.user.is_authenticated:
        return {
            'notificacoes_nao_lidas': 0,
            'ultimas_notificacoes': []
        }

    jogador = Jogador.objects.filter(
        usuario=request.user
    ).first()

    if not jogador:
        return {
            'notificacoes_nao_lidas': 0,
            'ultimas_notificacoes': []
        }

    notificacoes = Notificacao.objects.filter(
        jogador=jogador
    ).order_by('-criada_em')[:5]

    total_nao_lidas = Notificacao.objects.filter(
        jogador=jogador,
        lida=False
    ).count()

    return {
        'notificacoes_nao_lidas': total_nao_lidas,
        'ultimas_notificacoes': notificacoes
    }