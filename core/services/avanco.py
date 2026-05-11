from core.models import (
    Jogo,
    ParticipanteJogo
)


FASES = [
    'OITAVAS',
    'QUARTAS',
    'SEMI',
    'FINAL'
]


def proxima_fase(fase):

    try:

        indice = FASES.index(fase)

        return FASES[indice + 1]

    except:

        return None


def avancar_vencedor(jogo):

    vencedores = jogo.participantes.filter(
        vencedor=True
    )

    if not vencedores.exists():
        return

    vencedor = vencedores.first()

    nova_fase = proxima_fase(
        jogo.fase
    )

    if not nova_fase:
        return

    jogo_existente = Jogo.objects.filter(
        torneio=jogo.torneio,
        categoria=jogo.categoria,
        fase=nova_fase
    ).order_by(
        '-id'
    ).first()

    if (
        not jogo_existente
        or
        jogo_existente.participantes.count() >= 2
    ):

        jogo_existente = Jogo.objects.create(
            torneio=jogo.torneio,
            categoria=jogo.categoria,
            tipo_jogo=jogo.tipo_jogo,
            rodada=(jogo.rodada or 1) + 1,
            fase=nova_fase,
            data_jogo=jogo.data_jogo,
            status='PENDENTE'
        )

    lado = 'A'

    if jogo_existente.participantes.count() == 1:
        lado = 'B'

    ParticipanteJogo.objects.create(
        jogo=jogo_existente,
        jogador=vencedor.jogador,
        lado=lado
    )

    return jogo_existente