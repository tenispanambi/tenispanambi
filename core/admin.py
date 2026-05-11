from django.contrib import admin

from .models import (
    Jogador,
    Torneio,
    CategoriaTorneio,
    InscricaoTorneio,
    Jogo,
    ParticipanteJogo,
    SetJogo,
    RankingJogador,
)


class ParticipanteInline(admin.TabularInline):
    model = ParticipanteJogo
    extra = 4


class SetInline(admin.TabularInline):
    model = SetJogo
    extra = 3


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
    )

    list_filter = (
        'tipo_jogo',
        'categoria',
        'torneio',
    )

    inlines = [
        ParticipanteInline,
        SetInline,
    ]

@admin.register(RankingJogador)
class RankingJogadorAdmin(admin.ModelAdmin):

    list_display = (
    'posicao',
    'jogador',
    'categoria',
    'pontos',
    'vitorias',
    'derrotas',
    'games_feitos',
    'games_sofridos',
    'aproveitamento',
    'status_ranking',
)

    list_filter = (
        'torneio',
        'categoria',
    )

    ordering = (
        'categoria',
        'posicao',
    )

    search_fields = (
        'jogador__nome',
    )

admin.site.register(Jogador)
admin.site.register(Torneio)
admin.site.register(CategoriaTorneio)
admin.site.register(InscricaoTorneio)
