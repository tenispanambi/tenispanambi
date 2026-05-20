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
    CampeaoTorneio,
)

from .services.ranking import recalcular_ranking


# =========================
# INLINES
# =========================

class ParticipanteInline(admin.TabularInline):
    model = ParticipanteJogo
    extra = 4


class SetInline(admin.TabularInline):
    model = SetJogo
    extra = 3


# =========================
# JOGADOR
# =========================

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
    )


# =========================
# TORNEIO
# =========================

@admin.register(Torneio)
class TorneioAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'edicao',
        'ano',
        'tipo',
        'disputa',
        'status',
    )

    list_filter = (
        'tipo',
        'disputa',
        'status',
    )

    search_fields = (
        'nome',
    )


# =========================
# CATEGORIA TORNEIO
# =========================

@admin.register(CategoriaTorneio)
class CategoriaTorneioAdmin(admin.ModelAdmin):

    list_display = (
        'torneio',
        'categoria',
        'quantidade_jogadores',
        'classificados_finais',
        'melhores_resultados',
        'max_jogos_por_rodada',
    )

    list_filter = (
        'categoria',
        'torneio',
    )


# =========================
# INSCRIÇÃO
# =========================

@admin.register(InscricaoTorneio)
class InscricaoTorneioAdmin(admin.ModelAdmin):

    list_display = (
        'jogador',
        'torneio',
        'categoria',
        'ativo',
    )

    list_filter = (
        'ativo',
        'categoria',
    )

    search_fields = (
        'jogador__nome',
    )


# =========================
# JOGOS
# =========================

@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):

    list_display = (
        'descricao_confronto',
        'tipo_jogo',
        'torneio',
        'categoria',
        'fase',
        'data_jogo',
        'rodada',
        'status',
    )

    list_filter = (
        'tipo_jogo',
        'status',
        'fase',
        'rodada',
        'torneio',
        'categoria',
    )

    search_fields = (
        'participantes__jogador__nome',
    )

    inlines = [
        ParticipanteInline,
        SetInline,
    ]

    def save_model(self, request, obj, form, change):

        super().save_model(
            request,
            obj,
            form,
            change
        )

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


# =========================
# RANKING
# =========================

@admin.register(RankingJogador)
class RankingJogadorAdmin(admin.ModelAdmin):

    list_display = (
        'jogador',
        'categoria',
        'pontos',
        'vitorias',
        'derrotas',
        'aproveitamento',
        'posicao',
        'status_ranking',
    )

    list_filter = (
        'categoria',
        'status_ranking',
    )

    search_fields = (
        'jogador__nome',
    )


# =========================
# MURAL DOS CAMPEÕES
# =========================

@admin.register(CampeaoTorneio)
class CampeaoTorneioAdmin(admin.ModelAdmin):

    list_display = (
        'categoria',
        'edicao',
        'data_final',
        'campeao_1',
        'campeao_2',
        'placar',
    )

    list_filter = (
        'categoria',
        'edicao',
    )

    search_fields = (
        'campeao_1',
        'campeao_2',
        'finalista_1',
        'finalista_2',
    )