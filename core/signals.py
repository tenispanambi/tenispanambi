from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    SetJogo
)

from .services.ranking import (
    recalcular_ranking
)


@receiver(post_save, sender=SetJogo)
def atualizar_resultado_jogo(
    sender,
    instance,
    **kwargs
):

    jogo = instance.jogo

    vencedor = jogo.vencedor_lado()

    for p in jogo.participantes.all():

        p.vencedor = (
            p.lado == vencedor
        )

        if p.lado == 'A':

            games_feitos = (
                jogo.total_games_lado_a()
            )

        else:

            games_feitos = (
                jogo.total_games_lado_b()
            )

        if p.vencedor:

            p.pontos_ranking = (
                20 + games_feitos
            )

        else:

            p.pontos_ranking = (
                5 + games_feitos
            )

        p.save()

    if (
        jogo.tipo_jogo ==
        'CHAMPIONSHIP_DUPLAS'
    ):

        recalcular_ranking(
            jogo.torneio,
            jogo.categoria
        )