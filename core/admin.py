from django.contrib import admin

from .models import (
    Jogador,
    NovoCadastro,
    Torneio,
    CategoriaTorneio,
    InscricaoTorneio,
    Jogo,
    ParticipanteJogo,
    SetJogo,
    RankingJogador,
    CampeaoTorneio,
    Quadra,
    ConfiguracaoHorarioQuadra,
    ReservaQuadra,
    RegistroTorneio,
    ResultadoTorneio,
    BannerSite,
    EventoCalendario,
    Notificacao,
)

from .services.ranking import recalcular_ranking


class ParticipanteInline(admin.TabularInline):
    model = ParticipanteJogo
    extra = 4


class SetInline(admin.TabularInline):
    model = SetJogo
    extra = 3


@admin.register(Jogador)
class JogadorAdmin(admin.ModelAdmin):
    list_display = (
        'novo_cadastro',
        'nome',
        'categoria',
        'nivel',
        'cidade',
        'criado_em',
        'ativo',
    )

    list_filter = (
        'cadastro_revisado',
        'ativo',
        'categoria',
        'nivel',
        'cidade',
    )

    search_fields = (
        'nome',
        'cidade',
        'email',
        'instagram',
        'usuario__username',
    )

    ordering = (
        'cadastro_revisado',
        '-criado_em',
    )

    list_per_page = 30

    def novo_cadastro(self, obj):
        if not obj.cadastro_revisado:
            return "🟡 Novo cadastro"
        return "✅ Revisado"

    novo_cadastro.short_description = "Status"


@admin.register(NovoCadastro)
class NovoCadastroAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'categoria',
        'nivel',
        'cidade',
        'email',
        'criado_em',
    )

    list_filter = (
        'categoria',
        'nivel',
        'cidade',
    )

    search_fields = (
        'nome',
        'email',
        'cidade',
        'usuario__username',
    )

    ordering = (
        '-criado_em',
    )

    list_per_page = 30

    actions = ['aprovar_jogadores']

    @admin.action(description="✅ Marcar como revisado")
    def aprovar_jogadores(self, request, queryset):
        quantidade = queryset.update(cadastro_revisado=True)

        self.message_user(
            request,
            f"{quantidade} cadastro(s) marcado(s) como revisado(s)."
        )

@admin.register(Torneio)
class TorneioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'edicao', 'ano', 'tipo', 'disputa', 'status', 'ativo')
    list_filter = ('tipo', 'disputa', 'status', 'ativo')
    search_fields = ('nome',)


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
    list_filter = ('categoria', 'torneio')
    actions = ['importar_jogadores_ativos']

    def importar_jogadores_ativos(self, request, queryset):
        total_criados = 0

        for categoria_torneio in queryset:
            jogadores = Jogador.objects.filter(
                ativo=True,
                categoria=categoria_torneio.categoria
            )

            for jogador in jogadores:
                inscricao, criado = InscricaoTorneio.objects.get_or_create(
                    jogador=jogador,
                    torneio=categoria_torneio.torneio,
                    categoria=categoria_torneio,
                    defaults={'ativo': True}
                )

                if criado:
                    total_criados += 1

            recalcular_ranking(
                categoria_torneio.torneio,
                categoria_torneio
            )

        self.message_user(
            request,
            f'{total_criados} jogadores ativos foram inscritos automaticamente.'
        )

    importar_jogadores_ativos.short_description = 'Importar jogadores ativos desta categoria'


@admin.register(InscricaoTorneio)
class InscricaoTorneioAdmin(admin.ModelAdmin):
    list_display = ('jogador', 'torneio', 'categoria', 'ativo')
    list_filter = ('ativo', 'categoria')
    search_fields = ('jogador__nome',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        recalcular_ranking(
            obj.torneio,
            obj.categoria
        )


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
        'status_ranking',
    )

    list_filter = (
        'tipo_jogo',
        'status',
        'torneio',
        'categoria',
        'rodada',
    )

    search_fields = (
        'participantes__jogador__nome',
        'torneio__nome',
    )

    list_per_page = 20
    ordering = ('-data_jogo', '-id')
    inlines = [ParticipanteInline, SetInline]

    def status_ranking(self, obj):
        if obj.status != 'CONFIRMADO':
            return 'Não confirmado'

        if obj.fase:
            return 'Fase final'

        if not obj.torneio or not obj.categoria:
            return 'Histórico'

        participantes = ParticipanteJogo.objects.filter(jogo=obj)
        jogadores_contabilizados = []

        for p in participantes:
            inscrito = InscricaoTorneio.objects.filter(
                torneio=obj.torneio,
                categoria=obj.categoria,
                jogador=p.jogador,
                ativo=True
            ).exists()

            if not inscrito:
                continue

            jogos_rodada = ParticipanteJogo.objects.filter(
                jogo__torneio=obj.torneio,
                jogo__categoria=obj.categoria,
                jogo__rodada=obj.rodada,
                jogo__status='CONFIRMADO',
                jogador=p.jogador
            ).order_by('jogo__id')

            posicao = 0

            for item in jogos_rodada:
                posicao += 1

                if item.jogo.id == obj.id:
                    break

            if posicao <= obj.categoria.max_jogos_por_rodada:
                jogadores_contabilizados.append(p.jogador.id)

        if len(jogadores_contabilizados) == 0:
            return 'Não computado'

        total_participantes = participantes.count()

        if len(jogadores_contabilizados) < total_participantes:
            return 'Parcial'

        return 'Computado'

    status_ranking.short_description = 'Ranking'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.status == 'CONFIRMADO' and obj.torneio and obj.categoria:
            recalcular_ranking(obj.torneio, obj.categoria)

    def delete_model(self, request, obj):
        torneio = obj.torneio
        categoria = obj.categoria

        super().delete_model(request, obj)

        if torneio and categoria:
            recalcular_ranking(torneio, categoria)

    def delete_queryset(self, request, queryset):
        recalculos = []

        for obj in queryset:
            if obj.torneio and obj.categoria:
                recalculos.append((obj.torneio, obj.categoria))

        super().delete_queryset(request, queryset)

        for torneio, categoria in recalculos:
            recalcular_ranking(torneio, categoria)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        torneio_ativo = Torneio.objects.filter(
            ativo=True
        ).order_by(
            '-ano',
            '-edicao',
            '-id'
        ).first()

        if db_field.name == 'torneio':
            kwargs['queryset'] = Torneio.objects.filter(
                ativo=True
            ).order_by(
                '-ano',
                '-edicao',
                '-id'
            )

        elif db_field.name == 'categoria' and torneio_ativo:
            kwargs['queryset'] = CategoriaTorneio.objects.filter(
                torneio=torneio_ativo
            ).order_by('categoria')

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs
        )


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

    list_filter = ('categoria', 'status_ranking')
    search_fields = ('jogador__nome',)


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

    list_filter = ('categoria', 'edicao')

    search_fields = (
        'campeao_1',
        'campeao_2',
        'finalista_1',
        'finalista_2',
    )


@admin.register(ConfiguracaoHorarioQuadra)
class ConfiguracaoHorarioQuadraAdmin(admin.ModelAdmin):
    list_display = (
        'quadra',
        'dia_semana',
        'hora_inicio',
        'hora_fim',
        'ativo',
    )

    list_filter = ('quadra', 'dia_semana', 'ativo')
    ordering = ('quadra', 'dia_semana', 'hora_inicio')


@admin.register(ReservaQuadra)
class ReservaQuadraAdmin(admin.ModelAdmin):
    list_display = (
        'data',
        'horario',
        'reservado_por',
        'status',
        'checkin_realizado',
        'checkin_data_hora',
        'checkin_distancia_metros',
    )

    list_filter = (
        'data',
        'status',
        'checkin_realizado',
    )

    search_fields = (
        'reservado_por__nome',
        'jogadores',
    )

    readonly_fields = (
        'checkin_realizado',
        'checkin_data_hora',
        'checkin_latitude',
        'checkin_longitude',
        'checkin_distancia_metros',
        'criado_em',
    )


@admin.register(Quadra)
class QuadraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativa')
    list_filter = ('ativa',)
    search_fields = ('nome',)


class ResultadoTorneioInline(admin.TabularInline):
    model = ResultadoTorneio
    extra = 1


@admin.register(RegistroTorneio)
class RegistroTorneioAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'tipo',
        'data_inicio',
        'data_fim',
        'local',
        'total_inscritos',
        'total_jogos',
        'total_categorias',
        'ativo',
    )

    list_filter = (
        'tipo',
        'ativo',
        'data_inicio',
    )

    search_fields = (
        'nome',
        'local',
    )

    inlines = [ResultadoTorneioInline]


@admin.register(ResultadoTorneio)
class ResultadoTorneioAdmin(admin.ModelAdmin):
    list_display = (
        'torneio',
        'categoria',
        'campeao',
        'vice',
        'ordem',
    )

    list_filter = (
        'torneio',
        'categoria',
    )

    search_fields = (
        'torneio__nome',
        'categoria',
        'campeao',
        'vice',
    )


@admin.register(BannerSite)
class BannerSiteAdmin(admin.ModelAdmin):
    list_display = (
        'titulo',
        'pagina',
        'ativo',
        'ordem',
        'visualizacoes',
        'cliques',
        'criado_em',
    )

    list_filter = (
        'ativo',
        'pagina',
    )

    search_fields = (
        'titulo',
    )

    ordering = (
        'pagina',
        'ordem',
        '-criado_em',
    )

    readonly_fields = (
        'visualizacoes',
        'cliques',
        'criado_em',
    )

@admin.register(EventoCalendario)
class EventoCalendarioAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'tipo_evento',
        'data_inicio',
        'data_fim',
        'status',
        'ativo',
        'destaque',
    )

    list_filter = (
        'tipo_evento',
        'status',
        'ativo',
        'destaque',
        'data_inicio',
    )

    search_fields = (
        'nome',
        'subtitulo',
        'categorias',
        'local',
        'endereco',
    )

    ordering = (
        'data_inicio',
    )

    fieldsets = (
        (
            '🏆 Informações Gerais',
            {
                'fields': (
                    'nome',
                    'subtitulo',
                    'tipo_evento',
                    'descricao',
                    'categorias',
                )
            }
        ),
        (
            '📍 Local',
            {
                'fields': (
                    'local',
                    'endereco',
                )
            }
        ),
        (
            '📅 Datas',
            {
                'fields': (
                    'data_abertura_inscricoes',
                    'data_fechamento_inscricoes',
                    'data_inicio',
                    'data_fim',
                )
            }
        ),
        (
            '📝 Inscrições',
            {
                'fields': (
                    'valor_inscricao',
                    'limite_vagas',
                    'link_inscricao',
                )
            }
        ),
        (
            '🖼️ Imagens e Arquivos',
            {
                'fields': (
                    'banner',
                    'logo',
                    'regulamento',
                )
            }
        ),
        (
            '⚙️ Configurações',
            {
                'fields': (
                    'status',
                    'ativo',
                    'destaque',
                    'cor_evento',
                )
            }
        ),
    )

@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = (
        'jogador',
        'titulo',
        'lida',
        'criada_em',
    )

    list_filter = (
        'lida',
        'criada_em',
    )

    search_fields = (
        'jogador__nome',
        'titulo',
        'mensagem',
    )

    ordering = (
        '-criada_em',
    )    