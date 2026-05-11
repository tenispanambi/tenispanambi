import random

from core.models import (
    InscricaoTorneio,
    Jogo,
    ParticipanteJogo
)


def gerar_chaveamento(
    torneio,
    categoria
):

    jogos_existentes = Jogo.objects.filter(
        torneio=torneio,
        categoria=categoria
    )

    if jogos_existentes.exists():
        return False

    inscricoes = list(

        InscricaoTorneio.objects.filter(
            torneio=torneio,
            categoria=categoria,
            ativo=True
        )

    )

    random.shuffle(inscricoes)

    rodada = 1

    while len(inscricoes) >= 2:

        jogador_a = inscricoes.pop(0)
        jogador_b = inscricoes.pop(0)

        jogo = Jogo.objects.create(
            torneio=torneio,
            categoria=categoria,
            tipo_jogo='SIMPLES',
            rodada=rodada,
            data_jogo=torneio.data_inicio,
            status='PENDENTE'
        )

        ParticipanteJogo.objects.create(
            jogo=jogo,
            jogador=jogador_a.jogador,
            lado='A'
        )

        ParticipanteJogo.objects.create(
            jogo=jogo,
            jogador=jogador_b.jogador,
            lado='B'
        )

    return True