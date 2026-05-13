from .services.ranking import recalcular_ranking

from django.contrib import admin

from .models import (
    Jogador,
    Torneio,
    CategoriaTorneio,
    Jogo,
    ParticipanteJogo,
    RankingJogador,
    InscricaoTorneio,
)


class ParticipanteJogoInline(admin.TabularInline):
    model = ParticipanteJogo
    extra = 4
    autocomplete_fields = ['jogador']


@admin.register(Jogador)
class JogadorAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'categoria',
        'nivel',
        'cidade',
        'ativo',
    )

    list_filter = (
        'categoria',
        'nivel',
        'ativo',
    )

    search_fields = (
        'nome',
        'cidade',
        'instagram',
        'categoria',
    )

    ordering = (
        'categoria',
        'nome',
    )


@admin.register(Torneio)
class TorneioAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'tipo',
        'status',
        'data_inicio',
    )

    list_filter = (
        'tipo',
        'status',
    )

    search_fields = (
        'nome',
    )


@admin.register(CategoriaTorneio)
class CategoriaTorneioAdmin(admin.ModelAdmin):

    list_display = (
        'torneio',
        'categoria',
        'quantidade_jogadores',
        'classificados_finais',
        'rebaixados',
        'promovidos',
    )

    list_filter = (
        'categoria',
    )


@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'descricao_confronto',
        'tipo_jogo',
        'torneio',
        'categoria',
        'rodada',
        'data_jogo',
        'status',
    )

    list_filter = (
        'tipo_jogo',
        'categoria',
        'torneio',
        'rodada',
        'status',
    )

    search_fields = (
        'participantes__jogador__nome',
        'torneio__nome',
        'categoria__categoria',
    )

    inlines = [
        ParticipanteJogoInline
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if (
            obj.status == 'CONFIRMADO'
            and obj.tipo_jogo == 'CHAMPIONSHIP_DUPLAS'
            and obj.torneio
            and obj.categoria
        ):
            recalcular_ranking(
                obj.torneio,
                obj.categoria
            )


@admin.register(RankingJogador)
class RankingJogadorAdmin(admin.ModelAdmin):

    list_display = (
        'posicao',
        'jogador',
        'categoria',
        'pontos',
        'vitorias',
        'derrotas',
        'status_ranking',
    )

    list_filter = (
        'categoria',
        'status_ranking',
    )

    ordering = (
        'categoria',
        'posicao',
    )


@admin.register(InscricaoTorneio)
class InscricaoTorneioAdmin(admin.ModelAdmin):

    list_display = (
        'jogador',
        'torneio',
        'categoria',
        'ativo',
    )

    list_filter = (
        'categoria',
        'ativo',
    )

    search_fields = (
        'jogador__nome',
        'torneio__nome',
    )