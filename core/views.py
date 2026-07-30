from django.shortcuts import (
    render,
    get_object_or_404,
    redirect
)

import math
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Max
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.db.models import Sum

from .services.ranking import recalcular_ranking
from .services.avanco import avancar_vencedor
from .services.chaveamento import gerar_chaveamento
from datetime import date, datetime, timedelta
from django.utils import timezone
from collections import Counter
from django.contrib.admin.views.decorators import staff_member_required

from .models import (
    RankingJogador,
    Jogador,
    ParticipanteJogo,
    Jogo,
    SetJogo,
    Torneio,
    InscricaoTorneio,
    CategoriaTorneio,
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

def home(request):

    torneio_ativo = Torneio.objects.filter(
        ativo=True
    ).order_by(
        '-ano',
        '-edicao',
        '-id'
    ).first()

    total_jogadores = Jogador.objects.count()
    total_torneios = Torneio.objects.count()

    total_jogos_geral = Jogo.objects.filter(
        status='CONFIRMADO'
    ).count()

    total_jogos_duplas = Jogo.objects.filter(
        status='CONFIRMADO',
        tipo_jogo='CHAMPIONSHIP_DUPLAS'
    ).count()

    total_jogos_simples = Jogo.objects.filter(
        status='CONFIRMADO',
        tipo_jogo='SIMPLES'
    ).count()

    total_jogos = 0
    jogos_ultima_rodada = 0
    ultima_rodada_geral = None
    ultimos_jogos = []
    ranking_a = []
    ranking_b = []
    ranking_c = []

    destaques_a = {
        'rodada': None,
        'jogadores': []
    }

    destaques_b = {
        'rodada': None,
        'jogadores': []
    }

    destaques_c = {
        'rodada': None,
        'jogadores': []
    }

    placares_mais_comuns = []

    if torneio_ativo:

        total_jogos = Jogo.objects.filter(
            torneio=torneio_ativo,
            status='CONFIRMADO'
        ).count()

        # ====================================
        # PLACARES MAIS COMUNS
        # Soma 6x2 e 2x6 como o mesmo placar
        # ====================================

        resultados_validos = [
            '7x6',
            '7x5',
            '6x4',
            '6x3',
            '6x2',
            '6x1',
            '6x0',
        ]

        contador_placares = {
            placar: 0
            for placar in resultados_validos
        }

        jogos_duplas = Jogo.objects.filter(
            status='CONFIRMADO',
            tipo_jogo='CHAMPIONSHIP_DUPLAS'
        )

        for jogo in jogos_duplas:

            placar = jogo.placar_resumido()

            if not placar or 'x' not in placar:
                continue

            try:
                a, b = placar.split('x')

                a = int(a.strip())
                b = int(b.strip())

                maior = max(a, b)
                menor = min(a, b)

                placar_normalizado = f'{maior}x{menor}'

                if placar_normalizado in contador_placares:
                    contador_placares[placar_normalizado] += 1

            except Exception:
                pass

        placares_mais_comuns = sorted(
            contador_placares.items(),
            key=lambda item: item[1],
            reverse=True
        )

        ultima_rodada_geral = Jogo.objects.filter(
            torneio=torneio_ativo,
            status='CONFIRMADO',
            tipo_jogo='CHAMPIONSHIP_DUPLAS',
            rodada__isnull=False
        ).order_by(
            '-rodada'
        ).values_list(
            'rodada',
            flat=True
        ).first()

        if ultima_rodada_geral:

            jogos_ultima_rodada = Jogo.objects.filter(
                torneio=torneio_ativo,
                status='CONFIRMADO',
                tipo_jogo='CHAMPIONSHIP_DUPLAS',
                rodada=ultima_rodada_geral
            ).count()

        # Últimos jogos gerais do histórico
        ultimos_jogos = Jogo.objects.filter(
            status='CONFIRMADO'
        ).order_by(
            '-data_jogo',
            '-id'
        )[:15]

        ranking_a = RankingJogador.objects.filter(
            torneio=torneio_ativo,
            categoria__categoria='A'
        ).order_by(
            'posicao'
        )[:5]

        ranking_b = RankingJogador.objects.filter(
            torneio=torneio_ativo,
            categoria__categoria='B'
        ).order_by(
            'posicao'
        )[:5]

        ranking_c = RankingJogador.objects.filter(
            torneio=torneio_ativo,
            categoria__categoria='C'
        ).order_by(
            'posicao'
        )[:5]

        def destaques_ultima_rodada(categoria_letra):

            ultima_rodada = Jogo.objects.filter(
                torneio=torneio_ativo,
                status='CONFIRMADO',
                tipo_jogo='CHAMPIONSHIP_DUPLAS',
                categoria__categoria=categoria_letra,
                rodada__isnull=False
            ).order_by(
                '-rodada'
            ).values_list(
                'rodada',
                flat=True
            ).first()

            if not ultima_rodada:
                return {
                    'rodada': None,
                    'jogadores': []
                }

            jogos_rodada = Jogo.objects.filter(
                torneio=torneio_ativo,
                status='CONFIRMADO',
                tipo_jogo='CHAMPIONSHIP_DUPLAS',
                categoria__categoria=categoria_letra,
                rodada=ultima_rodada
            ).prefetch_related(
                'participantes',
                'participantes__jogador'
            ).order_by(
                'data_jogo',
                'id'
            )

            dados = {}
            controle_jogos_jogador = {}

            for jogo in jogos_rodada:

                for p in jogo.participantes.all():

                    jogador = p.jogador

                    if jogador.id not in controle_jogos_jogador:
                        controle_jogos_jogador[jogador.id] = 0

                    if controle_jogos_jogador[jogador.id] >= 2:
                        continue

                    controle_jogos_jogador[jogador.id] += 1

                    if jogador.id not in dados:
                        dados[jogador.id] = {
                            'nome': jogador.nome,
                            'vitorias': 0,
                            'derrotas': 0,
                            'pontos': 0,
                        }

                    if p.lado == 'A':
                        games = jogo.total_games_lado_a()
                    else:
                        games = jogo.total_games_lado_b()

                    if p.vencedor:
                        dados[jogador.id]['vitorias'] += 1
                        dados[jogador.id]['pontos'] += 20 + games
                    else:
                        dados[jogador.id]['derrotas'] += 1
                        dados[jogador.id]['pontos'] += 5 + games

            jogadores = sorted(
                dados.values(),
                key=lambda x: x['pontos'],
                reverse=True
            )[:5]

            return {
                'rodada': ultima_rodada,
                'jogadores': jogadores
            }

        destaques_a = destaques_ultima_rodada('A')
        destaques_b = destaques_ultima_rodada('B')
        destaques_c = destaques_ultima_rodada('C')

    else:

        ultimos_jogos = Jogo.objects.filter(
            status='CONFIRMADO'
        ).order_by(
            '-data_jogo',
            '-id'
        )[:15]

    proximos_torneios = Torneio.objects.filter(
        data_inicio__gte=date.today()
    ).order_by(
        'data_inicio'
    )[:3]

    banners_home = BannerSite.objects.filter(
    ativo=True,
    pagina='HOME'
).order_by(
    'ordem',
    '-criado_em'
)

    return render(
        request,
        'core/index.html',
        {
            'torneio_ativo': torneio_ativo,
            'total_jogadores': total_jogadores,
            'total_jogos': total_jogos,
            'total_torneios': total_torneios,
            'jogos_ultima_rodada': jogos_ultima_rodada,
            'ultima_rodada_geral': ultima_rodada_geral,
            'ultimos_jogos': ultimos_jogos,
            'ranking_a': ranking_a,
            'ranking_b': ranking_b,
            'ranking_c': ranking_c,
            'proximos_torneios': proximos_torneios,
            'destaques_a': destaques_a,
            'destaques_b': destaques_b,
            'destaques_c': destaques_c,
            'placares_mais_comuns': placares_mais_comuns,
            'total_jogos_geral': total_jogos_geral,
            'total_jogos_duplas': total_jogos_duplas,
            'total_jogos_simples': total_jogos_simples,
            'banners_home': banners_home,
        }
    )


def cadastro(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if senha != confirmar_senha:
            return render(
            request,
            'registration/cadastro.html',
            {    
                'erro': 'As senhas não conferem.'
            }
    )

        if User.objects.filter(username=username).exists():
            return render(
                request,
                'registration/cadastro.html',
                {
                    'erro': 'Este usuário já existe.'
                }
            )

        if User.objects.filter(email=email).exists():
            return render(
                request,
                'registration/cadastro.html',
                {
                    'erro': 'Já existe um usuário cadastrado com este e-mail.'
                }
            )

        jogador_existente = Jogador.objects.filter(
            email=email
        ).first()

        user = User.objects.create_user(
            username=username,
            email=email,
            password=senha
        )

        user.is_active = False
        user.save()

        if jogador_existente:

            if jogador_existente.usuario:
                user.delete()

                return render(
                    request,
                    'registration/cadastro.html',
                    {
                        'erro': 'Este jogador já possui login cadastrado. Entre em contato com a organização.'
                    }
                )

            jogador_existente.usuario = user
            jogador_existente.ativo = False
            jogador_existente.save()

        else:

            Jogador.objects.create(
                usuario=user,
                nome=nome,
                email=email,
                categoria='C',
                ativo=False
            )

        return render(
            request,
            'registration/cadastro.html',
            {
                'sucesso': (
                    'Cadastro enviado com sucesso. '
                    'Aguarde aprovação do administrador '
                    'para acessar o sistema.'
                )
            }
        )

    return render(
        request,
        'registration/cadastro.html'
    )


def ranking(request):

    torneio_ativo = Torneio.objects.filter(
        ativo=True
    ).order_by(
        '-ano',
        '-edicao',
        '-id'
    ).first()

    if not torneio_ativo:

        ranking_a = []
        ranking_b = []
        ranking_c = []

    else:

        ranking_a = RankingJogador.objects.filter(
            torneio=torneio_ativo,
            categoria__categoria='A'
        ).order_by('posicao')

        ranking_b = RankingJogador.objects.filter(
            torneio=torneio_ativo,
            categoria__categoria='B'
        ).order_by('posicao')

        ranking_c = RankingJogador.objects.filter(
            torneio=torneio_ativo,
            categoria__categoria='C'
        ).order_by('posicao')

    def aplicar_variacao(lista):

        for r in lista:

            r.variacao_posicao = 0
            r.direcao_posicao = 'igual'

            if r.posicao_anterior and r.posicao_anterior > 0:

                if r.posicao < r.posicao_anterior:
                    r.variacao_posicao = r.posicao_anterior - r.posicao
                    r.direcao_posicao = 'subiu'

                elif r.posicao > r.posicao_anterior:
                    r.variacao_posicao = r.posicao - r.posicao_anterior
                    r.direcao_posicao = 'desceu'

        return lista

    ranking_a = aplicar_variacao(list(ranking_a))
    ranking_b = aplicar_variacao(list(ranking_b))
    ranking_c = aplicar_variacao(list(ranking_c))

    return render(
        request,
        'ranking/lista.html',
        {
            'torneio_ativo': torneio_ativo,
            'ranking_a': ranking_a,
            'ranking_b': ranking_b,
            'ranking_c': ranking_c,
        }
    )

def detalhe_torneio(request, torneio_id):

    torneio = get_object_or_404(
        Torneio,
        id=torneio_id
    )

    total_jogos = Jogo.objects.filter(
        torneio=torneio,
        status='CONFIRMADO'
    ).count()

    ultimos_jogos = Jogo.objects.filter(
        torneio=torneio,
        status='CONFIRMADO'
    ).order_by(
        '-data_jogo',
        '-id'
    )[:20]

    resultados_validos = [
        '7x6',
        '7x5',
        '6x4',
        '6x3',
        '6x2',
        '6x1',
        '6x0',
    ]

    contador_placares = {
        placar: 0
        for placar in resultados_validos
    }

    jogos_duplas = Jogo.objects.filter(
        torneio=torneio,
        status='CONFIRMADO',
        tipo_jogo='CHAMPIONSHIP_DUPLAS'
    )

    for jogo in jogos_duplas:

        placar = jogo.placar_resumido()

        if not placar or 'x' not in placar:
            continue

        try:
            a, b = placar.split('x')

            a = int(a.strip())
            b = int(b.strip())

            maior = max(a, b)
            menor = min(a, b)

            placar_normalizado = f'{maior}x{menor}'

            if placar_normalizado in contador_placares:
                contador_placares[placar_normalizado] += 1

        except Exception:
            pass

    placares_mais_comuns = sorted(
        contador_placares.items(),
        key=lambda item: item[1],
        reverse=True
    )

    jogos_por_rodada = Jogo.objects.filter(
        torneio=torneio,
        status='CONFIRMADO',
        rodada__isnull=False
    ).values(
        'rodada'
    ).annotate(
        total=Count('id')
    ).order_by(
        'rodada'
    )

    torneios_historico = Torneio.objects.all().order_by(
        '-ano',
        '-edicao',
        '-id'
    )

    def montar_matriz_categoria(categoria_letra):

        categoria = CategoriaTorneio.objects.filter(
            torneio=torneio,
            categoria=categoria_letra
        ).first()

        if not categoria:
            return {
                'categoria': categoria_letra,
                'rodadas': [],
                'jogadores': [],
                'config': None
            }

        jogos = Jogo.objects.filter(
            torneio=torneio,
            categoria=categoria,
            status='CONFIRMADO',
            tipo_jogo='CHAMPIONSHIP_DUPLAS'
        ).filter(
            fase__isnull=True
        ).order_by(
            'rodada',
            'id'
        )

        maior_rodada = jogos.aggregate(
            maior=Max('rodada')
        )['maior'] or 0

        rodadas_numeros = list(
            range(1, maior_rodada + 1)
        )

        inscricoes = InscricaoTorneio.objects.filter(
            torneio=torneio,
            categoria=categoria,
            ativo=True
        ).select_related(
            'jogador'
        )

        dados_jogadores = {}

        for inscricao in inscricoes:

            jogador = inscricao.jogador

            dados_jogadores[jogador.id] = {
                'jogador': jogador,
                'rodadas': {},
                'total': 0,
                'posicao': '-',
            }

        ranking = RankingJogador.objects.filter(
            torneio=torneio,
            categoria=categoria
        ).select_related(
            'jogador'
        )

        for r in ranking:

            if r.jogador.id not in dados_jogadores:
                dados_jogadores[r.jogador.id] = {
                    'jogador': r.jogador,
                    'rodadas': {},
                    'total': r.pontos,
                    'posicao': r.posicao,
                }
            else:
                dados_jogadores[r.jogador.id]['total'] = r.pontos
                dados_jogadores[r.jogador.id]['posicao'] = r.posicao

        controle_rodadas = {}

        for jogo in jogos:

            rodada = jogo.rodada or 0

            if rodada == 0:
                continue

            participantes = ParticipanteJogo.objects.filter(
                jogo=jogo
            ).select_related(
                'jogador'
            )

            for p in participantes:

                jogador = p.jogador

                if jogador.id not in dados_jogadores:
                    continue

                chave = f'{jogador.id}_{rodada}'

                if chave not in controle_rodadas:
                    controle_rodadas[chave] = 0

                if controle_rodadas[chave] >= categoria.max_jogos_por_rodada:
                    continue

                controle_rodadas[chave] += 1

                if p.lado == 'A':
                    games_feitos = jogo.total_games_lado_a()
                else:
                    games_feitos = jogo.total_games_lado_b()

                if p.vencedor:
                    pontos = 20 + games_feitos
                else:
                    pontos = 5 + games_feitos

                if rodada not in dados_jogadores[jogador.id]['rodadas']:
                    dados_jogadores[jogador.id]['rodadas'][rodada] = {
                        'pontos': 0,
                        'conta': False,
                    }

                dados_jogadores[jogador.id]['rodadas'][rodada]['pontos'] += pontos

        for dados in dados_jogadores.values():

            lista_rodadas = []

            for rodada, info in dados['rodadas'].items():
                lista_rodadas.append({
                    'rodada': rodada,
                    'pontos': info['pontos']
                })

            melhores = sorted(
                lista_rodadas,
                key=lambda item: item['pontos'],
                reverse=True
            )[:categoria.rodadas_contabilizadas]

            rodadas_contam = [
                item['rodada']
                for item in melhores
            ]

            for rodada, info in dados['rodadas'].items():
                if rodada in rodadas_contam:
                    info['conta'] = True

            linha_rodadas = []

            for numero in rodadas_numeros:

                if numero in dados['rodadas']:

                    info = dados['rodadas'][numero]

                    linha_rodadas.append({
                        'rodada': numero,
                        'pontos': info['pontos'],
                        'conta': info['conta'],
                        'jogou': True,
                    })

                else:

                    linha_rodadas.append({
                        'rodada': numero,
                        'pontos': '-',
                        'conta': False,
                        'jogou': False,
                    })

            dados['linha_rodadas'] = linha_rodadas

        jogadores = sorted(
            dados_jogadores.values(),
            key=lambda item: (
                item['posicao'] if item['posicao'] != '-' else 9999,
                item['jogador'].nome
            )
        )

        return {
            'categoria': categoria_letra,
            'config': categoria,
            'rodadas': rodadas_numeros,
            'jogadores': jogadores
        }

    matriz_a = montar_matriz_categoria('A')
    matriz_b = montar_matriz_categoria('B')
    matriz_c = montar_matriz_categoria('C')

    return render(
        request,
        'torneios/detalhe.html',
        {
            'torneio': torneio,
            'total_jogos': total_jogos,
            'ultimos_jogos': ultimos_jogos,
            'placares_mais_comuns': placares_mais_comuns,
            'jogos_por_rodada': jogos_por_rodada,
            'torneios_historico': torneios_historico,
            'matriz_a': matriz_a,
            'matriz_b': matriz_b,
            'matriz_c': matriz_c,
        }
    )
@login_required
def jogador(request, jogador_id):
    jogador = get_object_or_404(
        Jogador,
        id=jogador_id
    )

    jogos_todos = ParticipanteJogo.objects.filter(
        jogador=jogador
    ).select_related(
        'jogo'
    ).order_by(
        '-jogo__data_jogo'
    )

    jogos_contabilizados = []
    controle_rodadas = {}

    for j in jogos_todos:
        chave = (
            j.jogo.categoria_id,
            j.jogo.rodada
        )

        if chave not in controle_rodadas:
            controle_rodadas[chave] = 0

        controle_rodadas[chave] += 1

        if controle_rodadas[chave] <= 2:
            j.contabilizado = True
            jogos_contabilizados.append(j)
        else:
            j.contabilizado = False

    vitorias = len([
        j for j in jogos_contabilizados
        if j.vencedor
    ])

    derrotas = len([
        j for j in jogos_contabilizados
        if not j.vencedor
    ])

    total = vitorias + derrotas

    aproveitamento = 0

    if total > 0:
        aproveitamento = round(
            (vitorias / total) * 100,
            2
        )

    return render(
        request,
        'jogador/perfil.html',
        {
            'jogador': jogador,
            'jogos': jogos_todos,
            'vitorias': vitorias,
            'derrotas': derrotas,
            'total': total,
            'aproveitamento': aproveitamento,
        }
    )


def headtohead(request):

    jogadores = Jogador.objects.all().exclude(
        usuario__is_staff=True
    ).exclude(
        usuario__is_superuser=True
    ).order_by('nome')

    torneio_ativo = Torneio.objects.filter(
        ativo=True
    ).order_by(
        '-ano',
        '-edicao',
        '-id'
    ).first()

    jogador1_id = request.GET.get('j1')
    jogador2_id = request.GET.get('j2')
    modalidade = request.GET.get('modalidade', 'TODOS')

    jogador1 = None
    jogador2 = None
    confrontos = []

    vitorias1 = 0
    vitorias2 = 0
    total_h2h = 0

    percentual_h2h_1 = 0
    percentual_h2h_2 = 0

    sets1 = 0
    sets2 = 0
    games1 = 0
    games2 = 0

    ranking1 = '-'
    ranking2 = '-'

    titulos1 = 0
    titulos2 = 0
    vices1 = 0
    vices2 = 0

    stats1 = {
        'simples_jogos': 0,
        'simples_vitorias': 0,
        'simples_derrotas': 0,
        'duplas_jogos': 0,
        'duplas_vitorias': 0,
        'duplas_derrotas': 0,
    }

    stats2 = {
        'simples_jogos': 0,
        'simples_vitorias': 0,
        'simples_derrotas': 0,
        'duplas_jogos': 0,
        'duplas_vitorias': 0,
        'duplas_derrotas': 0,
    }

    if jogador1_id:
        jogador1 = get_object_or_404(
            Jogador,
            id=jogador1_id
        )

        if torneio_ativo:
            r1 = RankingJogador.objects.filter(
                jogador=jogador1,
                torneio=torneio_ativo
            ).order_by(
                'posicao'
            ).first()

            if r1:
                ranking1 = f'{r1.posicao}º'

        titulos1 = jogador1.titulos_cd
        vices1 = jogador1.vice_cd

    if jogador2_id:
        jogador2 = get_object_or_404(
            Jogador,
            id=jogador2_id
        )

        if torneio_ativo:
            r2 = RankingJogador.objects.filter(
                jogador=jogador2,
                torneio=torneio_ativo
            ).order_by(
                'posicao'
            ).first()

            if r2:
                ranking2 = f'{r2.posicao}º'

        titulos2 = jogador2.titulos_cd
        vices2 = jogador2.vice_cd

    def calcular_stats(jogador):

        simples = ParticipanteJogo.objects.filter(
            jogador=jogador,
            jogo__status='CONFIRMADO',
            jogo__tipo_jogo='SIMPLES'
        )

        duplas = ParticipanteJogo.objects.filter(
            jogador=jogador,
            jogo__status='CONFIRMADO'
        ).exclude(
            jogo__tipo_jogo='SIMPLES'
        )

        return {
            'simples_jogos': simples.count(),
            'simples_vitorias': simples.filter(vencedor=True).count(),
            'simples_derrotas': simples.filter(vencedor=False).count(),
            'duplas_jogos': duplas.count(),
            'duplas_vitorias': duplas.filter(vencedor=True).count(),
            'duplas_derrotas': duplas.filter(vencedor=False).count(),
        }

    if jogador1:
        stats1 = calcular_stats(jogador1)

        stats1['duplas_jogos'] += jogador1.jogos_historicos
        stats1['duplas_vitorias'] += jogador1.vitorias_historicas
        stats1['duplas_derrotas'] += jogador1.derrotas_historicas

    if jogador2:
        stats2 = calcular_stats(jogador2)

        stats2['duplas_jogos'] += jogador2.jogos_historicos
        stats2['duplas_vitorias'] += jogador2.vitorias_historicas
        stats2['duplas_derrotas'] += jogador2.derrotas_historicas

    if jogador1 and jogador2:

        jogos = Jogo.objects.filter(
            status='CONFIRMADO'
        ).prefetch_related(
            'participantes',
            'sets'
        ).order_by(
            '-data_jogo',
            '-id'
        )

        if modalidade == 'SIMPLES':
            jogos = jogos.filter(
                tipo_jogo='SIMPLES'
            )

        elif modalidade == 'DUPLAS':
            jogos = jogos.exclude(
                tipo_jogo='SIMPLES'
            )

        for jogo in jogos:

            participantes = jogo.participantes.all()

            p1 = None
            p2 = None

            for p in participantes:

                if p.jogador.id == jogador1.id:
                    p1 = p

                if p.jogador.id == jogador2.id:
                    p2 = p

            if p1 and p2 and p1.lado != p2.lado:

                total_h2h += 1

                if p1.vencedor:
                    vitorias1 += 1
                else:
                    vitorias2 += 1

                if p1.lado == 'A':
                    games_j1 = jogo.total_games_lado_a()
                    games_j2 = jogo.total_games_lado_b()
                else:
                    games_j1 = jogo.total_games_lado_b()
                    games_j2 = jogo.total_games_lado_a()

                games1 += games_j1
                games2 += games_j2

                sets_j1 = 0
                sets_j2 = 0

                for s in jogo.sets.all():

                    if p1.lado == 'A':

                        if s.games_lado_a > s.games_lado_b:
                            sets_j1 += 1
                        else:
                            sets_j2 += 1

                    else:

                        if s.games_lado_b > s.games_lado_a:
                            sets_j1 += 1
                        else:
                            sets_j2 += 1

                sets1 += sets_j1
                sets2 += sets_j2

                jogo.vencedor_nome = jogador1.nome if p1.vencedor else jogador2.nome
                jogo.jogadores_partida = jogo.descricao_confronto()

                confrontos.append(jogo)

        if total_h2h > 0:
            percentual_h2h_1 = round(
                (vitorias1 / total_h2h) * 100,
                1
            )

            percentual_h2h_2 = round(
                (vitorias2 / total_h2h) * 100,
                1
            )

    return render(
        request,
        'headtohead/index.html',
        {
            'jogadores': jogadores,
            'jogador1': jogador1,
            'jogador2': jogador2,
            'modalidade': modalidade,
            'torneio_ativo': torneio_ativo,

            'confrontos': confrontos,

            'vitorias1': vitorias1,
            'vitorias2': vitorias2,
            'total_h2h': total_h2h,

            'percentual_h2h_1': percentual_h2h_1,
            'percentual_h2h_2': percentual_h2h_2,

            'sets1': sets1,
            'sets2': sets2,
            'games1': games1,
            'games2': games2,

            'ranking1': ranking1,
            'ranking2': ranking2,

            'titulos1': titulos1,
            'titulos2': titulos2,
            'vices1': vices1,
            'vices2': vices2,

            'stats1': stats1,
            'stats2': stats2,
        }
    )     

    
@login_required
def meu_painel(request):

    jogador = Jogador.objects.filter(
        usuario=request.user
    ).first()

    if not jogador:
        return redirect('/meu-perfil/')

    participacoes_confirmadas = ParticipanteJogo.objects.filter(
        jogador=jogador,
        jogo__status='CONFIRMADO'
    ).select_related(
        'jogo'
    ).prefetch_related(
        'jogo__participantes',
        'jogo__participantes__jogador'
    )

    jogos_sistema = participacoes_confirmadas.count()
    vitorias_sistema = participacoes_confirmadas.filter(vencedor=True).count()
    derrotas_sistema = participacoes_confirmadas.filter(vencedor=False).count()

    total_jogos = jogador.jogos_historicos + jogos_sistema
    total_vitorias = jogador.vitorias_historicas + vitorias_sistema
    total_derrotas = jogador.derrotas_historicas + derrotas_sistema

    aproveitamento = 0

    if total_jogos > 0:
        aproveitamento = round(
            (total_vitorias / total_jogos) * 100,
            1
        )

    torneio_ativo = Torneio.objects.filter(
        ativo=True
    ).order_by(
        '-ano',
        '-edicao',
        '-id'
    ).first()

    ranking = None

    if torneio_ativo:
        ranking = RankingJogador.objects.filter(
            jogador=jogador,
            torneio=torneio_ativo
        ).order_by(
            'posicao'
        ).first()

    if not ranking:
        ranking = RankingJogador.objects.filter(
            jogador=jogador
        ).order_by(
            'posicao'
        ).first()

    jogos = ParticipanteJogo.objects.filter(
        jogador=jogador
    ).select_related(
        'jogo'
    ).prefetch_related(
        'jogo__participantes',
        'jogo__participantes__jogador'
    ).order_by(
        '-jogo__data_jogo',
        '-jogo__id'
    )[:10]

    parceiros = {}
    adversarios = {}

    def criar_registro():
        return {
            'jogos': 0,
            'vitorias': 0,
            'derrotas': 0,
        }

    for p in participacoes_confirmadas:

        participantes = p.jogo.participantes.all()

        for outro in participantes:

            if outro.jogador == jogador:
                continue

            nome = outro.jogador.nome

            # PARCEIRO = mesmo lado
            if outro.lado == p.lado:

                if nome not in parceiros:
                    parceiros[nome] = criar_registro()

                parceiros[nome]['jogos'] += 1

                if p.vencedor:
                    parceiros[nome]['vitorias'] += 1
                else:
                    parceiros[nome]['derrotas'] += 1

            # ADVERSÁRIO = lado diferente
            else:

                if nome not in adversarios:
                    adversarios[nome] = criar_registro()

                adversarios[nome]['jogos'] += 1

                if p.vencedor:
                    adversarios[nome]['vitorias'] += 1
                else:
                    adversarios[nome]['derrotas'] += 1

    parceiros_ordenados = sorted(
        parceiros.items(),
        key=lambda x: x[1]['jogos'],
        reverse=True
    )[:5]

    maior_fregues_detalhe = None
    maior_rival_detalhe = None
    melhor_parceiro_detalhe = None
    pior_parceiro_detalhe = None

    # ==========================================
    # MAIOR FREGUÊS
    # Adversário contra quem o jogador mais venceu,
    # mas somente se tiver saldo positivo.
    # Exemplo: 2 vitórias e 4 derrotas NÃO é freguês.
    # ==========================================
    adversarios_com_saldo_positivo = {
        nome: dados
        for nome, dados in adversarios.items()
        if dados['vitorias'] > dados['derrotas']
    }

    if adversarios_com_saldo_positivo:

        nome_fregues, dados_fregues = max(
            adversarios_com_saldo_positivo.items(),
            key=lambda x: (
                x[1]['vitorias'],
                x[1]['vitorias'] - x[1]['derrotas'],
                x[1]['jogos']
            )
        )

        maior_fregues_detalhe = {
            'nome': nome_fregues,
            'jogos': dados_fregues['jogos'],
            'vitorias': dados_fregues['vitorias'],
            'derrotas': dados_fregues['derrotas'],
        }

    # ==========================================
    # MAIOR RIVAL
    # Adversário contra quem o jogador mais perdeu.
    # ==========================================
    if adversarios:

        nome_rival, dados_rival = max(
            adversarios.items(),
            key=lambda x: (
                x[1]['derrotas'],
                x[1]['derrotas'] - x[1]['vitorias'],
                x[1]['jogos']
            )
        )

        maior_rival_detalhe = {
            'nome': nome_rival,
            'jogos': dados_rival['jogos'],
            'vitorias': dados_rival['vitorias'],
            'derrotas': dados_rival['derrotas'],
        }

    # ==========================================
    # MELHOR PARCEIRO
    # Parceiro com mais vitórias junto.
    # ==========================================
    if parceiros:

        parceiros_com_vitoria = {
            nome: dados
            for nome, dados in parceiros.items()
            if dados['vitorias'] > 0
        }

        if parceiros_com_vitoria:

            nome_melhor, dados_melhor = max(
                parceiros_com_vitoria.items(),
                key=lambda x: (
                    x[1]['vitorias'],
                    x[1]['vitorias'] - x[1]['derrotas'],
                    x[1]['jogos']
                )
            )

            melhor_parceiro_detalhe = {
                'nome': nome_melhor,
                'jogos': dados_melhor['jogos'],
                'vitorias': dados_melhor['vitorias'],
                'derrotas': dados_melhor['derrotas'],
            }

        nome_pior, dados_pior = max(
            parceiros.items(),
            key=lambda x: (
                x[1]['derrotas'],
                x[1]['derrotas'] - x[1]['vitorias'],
                x[1]['jogos']
            )
        )

        pior_parceiro_detalhe = {
            'nome': nome_pior,
            'jogos': dados_pior['jogos'],
            'vitorias': dados_pior['vitorias'],
            'derrotas': dados_pior['derrotas'],
        }

    return render(
        request,
        'jogador/painel_v2.html',
        {
            'jogador': jogador,
            'ranking': ranking,
            'jogos': jogos,

            'total_jogos': total_jogos,
            'total_vitorias': total_vitorias,
            'total_derrotas': total_derrotas,
            'aproveitamento': aproveitamento,

            'parceiros_ordenados': parceiros_ordenados,

            'maior_fregues_detalhe': maior_fregues_detalhe,
            'maior_rival_detalhe': maior_rival_detalhe,
            'melhor_parceiro_detalhe': melhor_parceiro_detalhe,
            'pior_parceiro_detalhe': pior_parceiro_detalhe,

            'maior_fregues': maior_fregues_detalhe['nome'] if maior_fregues_detalhe else None,
            'maior_rival': maior_rival_detalhe['nome'] if maior_rival_detalhe else None,
        }
    )


@login_required
def meus_jogos(request):

    jogador = Jogador.objects.filter(
        usuario=request.user
    ).first()

    if not jogador:
        return redirect('meu_perfil')

    participacoes = ParticipanteJogo.objects.filter(
        jogador=jogador
    ).select_related(
        'jogo',
        'jogo__torneio',
        'jogo__categoria'
    ).order_by(
        'jogo__rodada',
        'jogo__id'
    )

    controle_rodadas = {}
    rodadas_validas = {}

    for p in participacoes:

        jogo = p.jogo
        categoria = jogo.categoria
        rodada = jogo.rodada or 0

        p.contabilizado = False
        p.historico_valido = False
        p.motivo_desconsiderado = ''
        p.pontos_calculados = 0
        p.pontos_rodada = 0

        if jogo.tipo_jogo != 'CHAMPIONSHIP_DUPLAS':
            p.historico_valido = True
            p.motivo_desconsiderado = 'Jogo amistoso/simples: vale para histórico, mas não soma ranking.'
            continue

        if jogo.status != 'CONFIRMADO':
            p.motivo_desconsiderado = 'Jogo ainda não confirmado.'
            continue

        if not categoria:
            p.motivo_desconsiderado = 'Jogo sem categoria.'
            continue

        if rodada > categoria.rodadas_contabilizadas:
            p.motivo_desconsiderado = 'Rodada fora do limite contabilizado.'
            continue

        chave = f'{jogador.id}_{categoria.id}_{rodada}'

        if chave not in controle_rodadas:
            controle_rodadas[chave] = 0

        if controle_rodadas[chave] >= categoria.max_jogos_por_rodada:
            p.motivo_desconsiderado = 'Excedeu o limite de jogos contabilizados nesta rodada.'
            continue

        controle_rodadas[chave] += 1
        p.historico_valido = True

        if p.lado == 'A':
            games_feitos = jogo.total_games_lado_a()
        else:
            games_feitos = jogo.total_games_lado_b()

        if p.vencedor:
            p.pontos_calculados = 20 + games_feitos
        else:
            p.pontos_calculados = 5 + games_feitos

        chave_rodada = f'{categoria.id}_{rodada}'

        if chave_rodada not in rodadas_validas:
            rodadas_validas[chave_rodada] = {
                'categoria': categoria,
                'rodada': rodada,
                'pontos': 0,
                'participacoes': []
            }

        rodadas_validas[chave_rodada]['pontos'] += p.pontos_calculados
        rodadas_validas[chave_rodada]['participacoes'].append(p)

    rodadas_por_categoria = {}

    for dados_rodada in rodadas_validas.values():

        categoria = dados_rodada['categoria']

        if categoria.id not in rodadas_por_categoria:
            rodadas_por_categoria[categoria.id] = []

        rodadas_por_categoria[categoria.id].append(dados_rodada)

    for categoria_id, lista_rodadas in rodadas_por_categoria.items():

        lista_rodadas_ordenadas = sorted(
            lista_rodadas,
            key=lambda r: r['pontos'],
            reverse=True
        )

        if lista_rodadas_ordenadas:
            categoria = lista_rodadas_ordenadas[0]['categoria']
            limite = categoria.melhores_resultados
        else:
            limite = 0

        melhores_rodadas = lista_rodadas_ordenadas[:limite]

        chaves_melhores = set()

        for r in melhores_rodadas:
            chaves_melhores.add(
                f"{r['categoria'].id}_{r['rodada']}"
            )

        for r in lista_rodadas_ordenadas:

            chave_rodada = f"{r['categoria'].id}_{r['rodada']}"

            for p in r['participacoes']:

                p.pontos_rodada = r['pontos']

                if chave_rodada in chaves_melhores:
                    p.contabilizado = True
                    p.motivo_desconsiderado = ''
                else:
                    p.contabilizado = False
                    p.motivo_desconsiderado = 'Rodada fora dos melhores resultados.'

    participacoes = sorted(
        participacoes,
        key=lambda p: (
            -(p.jogo.data_jogo.toordinal() if p.jogo.data_jogo else 0),
            -(p.jogo.id or 0)
        )
    )

    return render(
        request,
        'jogador/meus_jogos.html',
        {
            'participacoes': participacoes
        }
    )

@login_required
def lancar_resultado(request, jogo_id):

    jogador = Jogador.objects.get(
        usuario=request.user
    )

    jogo = get_object_or_404(
        Jogo,
        id=jogo_id
    )

    participantes = jogo.participantes.all()

    adversarios = []

    for p in participantes:
        if p.jogador.id != jogador.id:
            adversarios.append(p.jogador)

    if request.method == 'POST':

        sets_recebidos = []

        for numero in [1, 2, 3]:

            games_a = request.POST.get(f'set{numero}_a')
            games_b = request.POST.get(f'set{numero}_b')

            if games_a not in [None, ''] and games_b not in [None, '']:

                sets_recebidos.append({
                    'numero': numero,
                    'games_a': int(games_a),
                    'games_b': int(games_b),
                })

        if not sets_recebidos:
            messages.error(
                request,
                'Informe pelo menos o placar do Set 1.'
            )

            return redirect(
                'lancar_resultado',
                jogo_id=jogo.id
            )

        jogo.sets.all().delete()

        sets_a = 0
        sets_b = 0

        for item in sets_recebidos:

            SetJogo.objects.create(
                jogo=jogo,
                numero_set=item['numero'],
                games_lado_a=item['games_a'],
                games_lado_b=item['games_b']
            )

            if item['games_a'] > item['games_b']:
                sets_a += 1
            else:
                sets_b += 1

        vencedor_lado = 'A'

        if sets_b > sets_a:
            vencedor_lado = 'B'

        for p in participantes:
            p.vencedor = (
                p.lado == vencedor_lado
            )
            p.save()

        jogo.status = 'PENDENTE'
        jogo.save()

        return redirect('meus_jogos')

    return render(
        request,
        'jogador/lancar_resultado.html',
        {
            'jogo': jogo,
            'adversarios': adversarios,
        }
    )


@login_required
def resultados_pendentes(request):
    jogador = Jogador.objects.get(
        usuario=request.user
    )

    pendentes = ParticipanteJogo.objects.filter(
        jogador=jogador,
        jogo__status='PENDENTE'
    ).select_related('jogo')

    return render(
        request,
        'jogador/pendentes.html',
        {
            'pendentes': pendentes
        }
    )


@login_required
def confirmar_resultado(request, jogo_id):
    jogo = get_object_or_404(
        Jogo,
        id=jogo_id
    )

    jogo.status = 'CONFIRMADO'
    jogo.save()

    if jogo.fase:
        avancar_vencedor(jogo)

    if jogo.tipo_jogo == 'CHAMPIONSHIP_DUPLAS':
        recalcular_ranking(
            jogo.torneio,
            jogo.categoria
        )

    return redirect('resultados_pendentes')


@login_required
def contestar_resultado(request, jogo_id):

    jogador_logado = Jogador.objects.filter(
        usuario=request.user
    ).first()

    if not jogador_logado:
        messages.error(
            request,
            'Não foi encontrado um jogador vinculado ao seu usuário.'
        )
        return redirect('/meu-perfil/')

    jogo = get_object_or_404(
        Jogo.objects.prefetch_related(
            'participantes',
            'participantes__jogador',
            'sets'
        ),
        id=jogo_id
    )

    participacao = ParticipanteJogo.objects.filter(
        jogo=jogo,
        jogador=jogador_logado
    ).first()

    if not participacao:
        messages.error(
            request,
            'Você não participa deste jogo.'
        )
        return redirect('/meus-jogos/')

    if jogo.status == 'CONFIRMADO':
        messages.error(
            request,
            'Este jogo já foi confirmado e não pode mais ser contestado.'
        )
        return redirect('/meus-jogos/')

    if jogo.status == 'CONTESTADO':
        Notificacao.objects.filter(
            jogador=jogador_logado,
            link=f'/resultado-pendente/{jogo.id}/'
        ).delete()

        messages.info(
            request,
            'Este resultado já foi contestado.'
        )
        return redirect('/meus-jogos/')

    if participacao.lado != 'B':
        messages.error(
            request,
            'A contestação deve ser realizada por um dos adversários.'
        )
        return redirect('/meus-jogos/')

    jogo.status = 'CONTESTADO'
    jogo.save(update_fields=['status'])

    Notificacao.objects.filter(
        link=f'/resultado-pendente/{jogo.id}/'
    ).delete()

    confronto = jogo.descricao_confronto()
    placar = jogo.placar_resumido()

    jogadores_lado_a = ParticipanteJogo.objects.filter(
        jogo=jogo,
        lado='A'
    ).select_related(
        'jogador'
    )

    for participante_a in jogadores_lado_a:
        notificacao = Notificacao.objects.create(
            jogador=participante_a.jogador,
            titulo='❌ Resultado contestado',
            mensagem=(
                f'{jogador_logado.nome} contestou o resultado lançado.\n\n'
                f'{confronto}\n'
                f'Placar informado: {placar}\n\n'
                'O resultado precisa ser revisado antes de ser contabilizado.'
            )
        )

        notificacao.link = f'/abrir-notificacao/{notificacao.id}/'
        notificacao.save(update_fields=['link'])

    messages.warning(
        request,
        'Resultado contestado. Os responsáveis pelo lançamento foram avisados.'
    )

    return redirect('/meus-jogos/')


@login_required
def torneios(request):
    torneios = Torneio.objects.filter(
        status='ABERTO'
    ).order_by('-data_inicio')

    return render(
        request,
        'torneios/lista.html',
        {
            'torneios': torneios
        }
    )


@login_required
def inscrever_torneio(request, torneio_id, categoria_id):
    jogador = Jogador.objects.get(
        usuario=request.user
    )

    torneio = get_object_or_404(
        Torneio,
        id=torneio_id
    )

    categoria = get_object_or_404(
        CategoriaTorneio,
        id=categoria_id
    )

    existe = InscricaoTorneio.objects.filter(
        jogador=jogador,
        torneio=torneio,
        categoria=categoria
    ).exists()

    if not existe:
        InscricaoTorneio.objects.create(
            jogador=jogador,
            torneio=torneio,
            categoria=categoria
        )

    return redirect('torneios')


@login_required
def gerar_torneio(request, torneio_id, categoria_id):
    torneio = get_object_or_404(
        Torneio,
        id=torneio_id
    )

    categoria = get_object_or_404(
        CategoriaTorneio,
        id=categoria_id
    )

    gerar_chaveamento(
        torneio,
        categoria
    )

    return redirect('torneios')


@login_required
def chaveamento(request, torneio_id, categoria_id):
    torneio = get_object_or_404(
        Torneio,
        id=torneio_id
    )

    categoria = get_object_or_404(
        CategoriaTorneio,
        id=categoria_id
    )

    jogos = Jogo.objects.filter(
        torneio=torneio,
        categoria=categoria
    ).prefetch_related(
        'participantes'
    ).order_by(
        'rodada',
        'id'
    )

    rodadas = {}

    for jogo in jogos:
        rodada = jogo.rodada

        if rodada not in rodadas:
            rodadas[rodada] = []

        rodadas[rodada].append(jogo)

    return render(
        request,
        'torneios/chaveamento.html',
        {
            'torneio': torneio,
            'categoria': categoria,
            'rodadas': rodadas,
        }
    )

@login_required
def meu_perfil(request):

    jogador = Jogador.objects.filter(
        usuario=request.user
    ).first()

    if not jogador:
        jogador = Jogador.objects.create(
            usuario=request.user,
            nome=request.user.username,
            email=request.user.email,
            categoria='C',
            ativo=True
        )

    if request.method == 'POST':

        jogador.nome = request.POST.get('nome')
        jogador.telefone = request.POST.get('telefone')
        jogador.cidade = request.POST.get('cidade')
        jogador.mao_dominante = request.POST.get('mao_dominante')
        jogador.raquete = request.POST.get('raquete')
        jogador.instagram = request.POST.get('instagram')
        jogador.ano_inicio = request.POST.get('ano_inicio') or None
        jogador.clube = request.POST.get('clube')
        jogador.backhand = request.POST.get('backhand')
        jogador.estilo_jogo = request.POST.get('estilo_jogo')
        jogador.jogador_favorito = request.POST.get('jogador_favorito')
        jogador.frase_pessoal = request.POST.get('frase_pessoal')

        print('POST RECEBIDO:', request.POST)

        if request.FILES.get('foto'):
            jogador.foto = request.FILES.get('foto')

        jogador.save()

        print('SALVO:', jogador.nome, jogador.cidade, jogador.raquete, jogador.clube)

        return redirect('meu_perfil')

    ranking = RankingJogador.objects.filter(
        jogador=jogador
    ).order_by(
        'posicao'
    ).first()

    participacoes_confirmadas = ParticipanteJogo.objects.filter(
        jogador=jogador,
        jogo__status='CONFIRMADO'
    )

    jogos_sistema = participacoes_confirmadas.count()

    vitorias_sistema = participacoes_confirmadas.filter(
        vencedor=True
    ).count()

    derrotas_sistema = participacoes_confirmadas.filter(
        vencedor=False
    ).count()

    total_jogos = jogador.jogos_historicos + jogos_sistema

    total_vitorias = (
        jogador.vitorias_historicas +
        vitorias_sistema
    )

    total_derrotas = (
        jogador.derrotas_historicas +
        derrotas_sistema
    )

    aproveitamento = 0

    if total_jogos > 0:
        aproveitamento = round(
            (total_vitorias / total_jogos) * 100,
            1
        )

    return render(
        request,
        'jogador/meu_perfil.html',
        {
            'jogador': jogador,
            'ranking': ranking,
            'total_jogos': total_jogos,
            'total_vitorias': total_vitorias,
            'total_derrotas': total_derrotas,
            'aproveitamento': aproveitamento,
        }
    )


def login_view(request):

    if request.user.is_authenticated:
        return redirect('/meu-painel/')

    if request.method == 'POST':

        usuario_digitado = (
            request.POST.get('username') or
            request.POST.get('usuario') or
            request.POST.get('email')
        )

        senha_digitada = (
            request.POST.get('password') or
            request.POST.get('senha')
        )

        username_final = usuario_digitado

        if usuario_digitado and '@' in usuario_digitado:
            usuario_obj = User.objects.filter(
                email=usuario_digitado
            ).first()

            if usuario_obj:
                username_final = usuario_obj.username

        user = authenticate(
            request,
            username=username_final,
            password=senha_digitada
        )

        if user is not None:

            if user.is_active:
                login(request, user)
                return redirect('/meu-painel/')

            messages.error(
                request,
                'Usuário ainda não foi aprovado pelo administrador.'
            )

        else:
            messages.error(
                request,
                'Usuário ou senha inválidos.'
            )

    return render(
        request,
        'registration/login.html'
    )


def logout_view(request):

    logout(request)
    return redirect('/')


@login_required
def lancar_jogo(request):

    jogador_logado = Jogador.objects.filter(
        usuario=request.user
    ).first()

    if not jogador_logado:
        return redirect('/meu-perfil/')

    jogadores_todos = Jogador.objects.filter(
    ativo=True,
    usuario__is_staff=False,
    usuario__is_superuser=False
).exclude(
    id=jogador_logado.id
).order_by('nome')

    jogadores_categoria = Jogador.objects.filter(
    ativo=True,
    categoria=jogador_logado.categoria,
    usuario__is_staff=False,
    usuario__is_superuser=False
).exclude(
    id=jogador_logado.id
).order_by('nome')

    torneio_duplas_categoria = CategoriaTorneio.objects.filter(
        torneio__tipo='RANKING',
        torneio__disputa='DUPLAS',
        categoria=jogador_logado.categoria,
        torneio__status__in=[
            'ABERTO',
            'EM_ANDAMENTO',
            'FASE_FINAIS'
        ]
    ).select_related(
        'torneio'
    ).order_by(
        '-torneio__ano',
        '-torneio__edicao',
        '-id'
    ).first()

    torneio_duplas = None

    if torneio_duplas_categoria:
        torneio_duplas = torneio_duplas_categoria.torneio

    if request.method == 'POST':

        tipo_jogo_form = request.POST.get('tipo_jogo')
        data_jogo_str = request.POST.get('data_jogo')
        rodada = request.POST.get('rodada')
        fase = request.POST.get('fase')

        parceiro_a_id = request.POST.get('parceiro_a')
        adversario_1_id = request.POST.get('adversario_1')
        adversario_2_id = request.POST.get('adversario_2')

        if not data_jogo_str:
            messages.error(request, 'Informe a data do jogo.')
            return redirect('/lancar-jogo/')

        data_jogo = date.fromisoformat(data_jogo_str)

        sets_recebidos = []

        for numero in [1, 2, 3]:

            games_a = request.POST.get(f'set{numero}_a')
            games_b = request.POST.get(f'set{numero}_b')

            if games_a not in [None, ''] and games_b not in [None, '']:
                sets_recebidos.append({
                    'numero': numero,
                    'games_a': int(games_a),
                    'games_b': int(games_b),
                })

        if not sets_recebidos:
            messages.error(request, 'Informe pelo menos o placar do Set 1.')
            return redirect('/lancar-jogo/')

        torneio = None
        categoria = None
        tipo_jogo_salvar = 'SIMPLES'

        parceiro = None
        adversario_1 = None
        adversario_2 = None

        if tipo_jogo_form == 'CHAMPIONSHIP_DUPLAS':

            if not torneio_duplas_categoria:
                messages.error(
                    request,
                    'Não existe torneio de ranking em duplas aberto ou em fase finais para sua categoria.'
                )
                return redirect('/lancar-jogo/')

            categoria = torneio_duplas_categoria
            torneio = categoria.torneio

            hoje = timezone.localdate()
            controle = (torneio.controle_lancamento or '').strip().upper()

            if controle in ['SABADO', 'SÁBADO'] and not request.user.is_staff:

                if torneio.data_inicio and hoje < torneio.data_inicio:
                    messages.error(
                        request,
                        f'Os lançamentos deste torneio serão liberados somente a partir de {torneio.data_inicio.strftime("%d/%m/%Y")}.'
                    )
                    return redirect('/lancar-jogo/')

                if hoje.weekday() != 5:
                    messages.error(
                        request,
                        'Os jogos do Championship Duplas só podem ser lançados aos sábados.'
                    )
                    return redirect('/lancar-jogo/')

                if data_jogo != hoje:
                    messages.error(
                        request,
                        'A data do jogo precisa ser a data de hoje. Não é permitido lançar jogo de outra data.'
                    )
                    return redirect('/lancar-jogo/')

            if controle == 'MANUAL' and not request.user.is_staff:
                messages.error(
                    request,
                    'Os lançamentos deste torneio estão bloqueados pela organização.'
                )
                return redirect('/lancar-jogo/')

            if torneio.status == 'ENCERRADO':
                messages.error(request, 'Este torneio está encerrado definitivamente.')
                return redirect('/lancar-jogo/')

            if torneio.status in ['ABERTO', 'EM_ANDAMENTO']:

                if fase:
                    messages.error(request, 'As finais ainda não foram liberadas para este torneio.')
                    return redirect('/lancar-jogo/')

                if not rodada:
                    messages.error(request, 'Informe a rodada do jogo classificatório.')
                    return redirect('/lancar-jogo/')

                rodada = int(rodada)
                fase = None

            elif torneio.status == 'FASE_FINAIS':

                if not fase:
                    messages.error(
                        request,
                        'A classificatória está encerrada. Escolha Semifinal ou Final.'
                    )
                    return redirect('/lancar-jogo/')

                rodada = None

            if not parceiro_a_id or not adversario_1_id or not adversario_2_id:
                messages.error(
                    request,
                    'Para jogo de duplas, informe parceiro, adversário 1 e adversário 2.'
                )
                return redirect('/lancar-jogo/')

            parceiro = Jogador.objects.get(id=parceiro_a_id)
            adversario_1 = Jogador.objects.get(id=adversario_1_id)
            adversario_2 = Jogador.objects.get(id=adversario_2_id)

            jogadores_duplas = [
                jogador_logado,
                parceiro,
                adversario_1,
                adversario_2
            ]

            for jogador in jogadores_duplas:
                if jogador.categoria != jogador_logado.categoria:
                    messages.error(
                        request,
                        'Em jogos do Championship, todos os jogadores precisam ser da mesma categoria.'
                    )
                    return redirect('/lancar-jogo/')

            tipo_jogo_salvar = 'CHAMPIONSHIP_DUPLAS'

        elif tipo_jogo_form == 'AMISTOSO_DUPLAS':

            rodada = None
            fase = None
            torneio = None
            categoria = None
            tipo_jogo_salvar = 'AMISTOSO_DUPLAS'

            if not parceiro_a_id or not adversario_1_id or not adversario_2_id:
                messages.error(
                    request,
                    'Para jogo de duplas amistoso, informe parceiro, adversário 1 e adversário 2.'
                )
                return redirect('/lancar-jogo/')

            parceiro = Jogador.objects.get(id=parceiro_a_id)
            adversario_1 = Jogador.objects.get(id=adversario_1_id)
            adversario_2 = Jogador.objects.get(id=adversario_2_id)

        else:

            rodada = None
            fase = None
            torneio = None
            categoria = None
            tipo_jogo_salvar = 'SIMPLES'

            if not adversario_1_id:
                messages.error(request, 'Informe o adversário.')
                return redirect('/lancar-jogo/')

            adversario_1 = Jogador.objects.get(id=adversario_1_id)

        jogo = Jogo.objects.create(
            tipo_jogo=tipo_jogo_salvar,
            torneio=torneio,
            categoria=categoria,
            data_jogo=data_jogo,
            rodada=rodada,
            fase=fase,
            status='PENDENTE'
        )

        ParticipanteJogo.objects.create(
            jogo=jogo,
            jogador=jogador_logado,
            lado='A'
        )

        if tipo_jogo_form in ['AMISTOSO_DUPLAS', 'CHAMPIONSHIP_DUPLAS']:
            ParticipanteJogo.objects.create(
                jogo=jogo,
                jogador=parceiro,
                lado='A'
            )

        ParticipanteJogo.objects.create(
            jogo=jogo,
            jogador=adversario_1,
            lado='B'
        )

        if tipo_jogo_form in ['AMISTOSO_DUPLAS', 'CHAMPIONSHIP_DUPLAS']:
            ParticipanteJogo.objects.create(
                jogo=jogo,
                jogador=adversario_2,
                lado='B'
            )

        sets_a = 0
        sets_b = 0

        for item in sets_recebidos:

            SetJogo.objects.create(
                jogo=jogo,
                numero_set=item['numero'],
                games_lado_a=item['games_a'],
                games_lado_b=item['games_b']
            )

            if item['games_a'] > item['games_b']:
                sets_a += 1
            else:
                sets_b += 1

        lado_vencedor = 'A'

        if sets_b > sets_a:
            lado_vencedor = 'B'

        participantes = ParticipanteJogo.objects.filter(
            jogo=jogo
        )

             
        for p in participantes:
            p.vencedor = p.lado == lado_vencedor
            p.save()

        # ==========================================================
        # NOTIFICA OS ADVERSÁRIOS
        # Apenas jogadores do lado B precisam confirmar
        # ==========================================================

        nome_lancador = jogador_logado.nome
        confronto = jogo.descricao_confronto()
        placar = jogo.placar_resumido()

        adversarios = participantes.filter(
            lado='B'
        ).select_related(
            'jogador'
        )

        for participante in adversarios:
            Notificacao.objects.create(
                jogador=participante.jogador,
                titulo='🎾 Novo resultado aguardando confirmação',
                mensagem=(
                    f'{nome_lancador} lançou o resultado do jogo.\n\n'
                    f'{confronto}\n'
                    f'Placar: {placar}\n\n'
                    'Confira o resultado e confirme ou conteste.'
                ),
                link=f'/resultado-pendente/{jogo.id}/'
            )

        messages.success(
            request,
            'Jogo lançado com sucesso. Os adversários foram notificados.'
        )

        return redirect('/meus-jogos/')

    return render(
        request,
        'jogador/lancar_jogo.html',
        {
            'jogadores_todos': jogadores_todos,
            'jogadores_categoria': jogadores_categoria,
            'torneio_duplas': torneio_duplas
        }
    )

def mural_campeoes(request):

    campeoes_a = CampeaoTorneio.objects.filter(
        categoria='A'
    ).order_by('-edicao')

    campeoes_b = CampeaoTorneio.objects.filter(
        categoria='B'
    ).order_by('-edicao')

    campeoes_c = CampeaoTorneio.objects.filter(
        categoria='C'
    ).order_by('-edicao')

    return render(
        request,
        'jogador/mural_campeoes.html',
        {
            'campeoes_a': campeoes_a,
            'campeoes_b': campeoes_b,
            'campeoes_c': campeoes_c,
        }
    )
@login_required
def confirmar_resultado_usuario(request, jogo_id):

    jogador_logado = Jogador.objects.filter(
        usuario=request.user
    ).first()

    if not jogador_logado:
        messages.error(
            request,
            'Não foi encontrado um jogador vinculado ao seu usuário.'
        )
        return redirect('/meu-perfil/')

    jogo = get_object_or_404(
        Jogo.objects.prefetch_related(
            'participantes',
            'participantes__jogador',
            'sets'
        ),
        id=jogo_id
    )

    participacao = ParticipanteJogo.objects.filter(
        jogo=jogo,
        jogador=jogador_logado
    ).first()

    if not participacao:
        messages.error(
            request,
            'Você não participa deste jogo.'
        )
        return redirect('/meus-jogos/')

    if jogo.status == 'CONFIRMADO':

        # Remove uma eventual notificação antiga que tenha ficado salva
        Notificacao.objects.filter(
            jogador=jogador_logado,
            link=f'/resultado-pendente/{jogo.id}/'
        ).delete()

        messages.info(
            request,
            'Este resultado já foi confirmado.'
        )
        return redirect('/meus-jogos/')

    if jogo.status == 'CONTESTADO':

        Notificacao.objects.filter(
            jogador=jogador_logado,
            link=f'/resultado-pendente/{jogo.id}/'
        ).delete()

        messages.warning(
            request,
            'Este resultado já foi contestado.'
        )
        return redirect('/meus-jogos/')

    if participacao.lado != 'B':
        messages.error(
            request,
            'A confirmação deve ser realizada por um dos adversários.'
        )
        return redirect('/meus-jogos/')

    # ======================================================
    # CONFIRMA O RESULTADO
    # ======================================================

    jogo.status = 'CONFIRMADO'
    jogo.save(update_fields=['status'])

    jogo.atualizar_participantes()

    if (
        jogo.tipo_jogo == 'CHAMPIONSHIP_DUPLAS'
        and jogo.torneio
        and jogo.categoria
    ):
        recalcular_ranking(
            jogo.torneio,
            jogo.categoria
        )

    # ======================================================
    # REMOVE TODAS AS NOTIFICAÇÕES PENDENTES DESTE JOGO
    # Dessa forma, em duplas, a notificação desaparece
    # para os dois adversários quando um deles confirma.
    # ======================================================

    Notificacao.objects.filter(
        link=f'/resultado-pendente/{jogo.id}/'
    ).delete()

    confronto = jogo.descricao_confronto()
    placar = jogo.placar_resumido()

    # ======================================================
    # AVISA OS JOGADORES DO LADO A
    # Quem lançou e seu parceiro recebem a confirmação.
    # ======================================================

    jogadores_lado_a = ParticipanteJogo.objects.filter(
        jogo=jogo,
        lado='A'
    ).select_related(
        'jogador'
    )

    for participante_a in jogadores_lado_a:

        notificacao = Notificacao.objects.create(
            jogador=participante_a.jogador,
            titulo='✅ Resultado confirmado',
            mensagem=(
                f'{jogador_logado.nome} confirmou o resultado.\n\n'
                f'{confronto}\n'
                f'Placar: {placar}\n\n'
                'O jogo já está confirmado e contabilizado.'
            )
        )

        notificacao.link = (
            f'/abrir-notificacao/{notificacao.id}/'
        )
        notificacao.save(update_fields=['link'])

    messages.success(
        request,
        'Resultado confirmado com sucesso. O jogo já foi contabilizado.'
    )

    return redirect('/meus-jogos/')

@login_required
def quadras(request):

    hoje = date.today()
    agora = timezone.localtime().time()

    proximos_dias = []

    quadras = Quadra.objects.filter(
        ativa=True
    ).order_by('nome')

    for i in range(0, 14):

        dia = hoje + timedelta(days=i)

        quadras_dia = []
        possui_horarios = False
        pode_reservar_dia = dia == hoje

        for quadra in quadras:

            horarios = ConfiguracaoHorarioQuadra.objects.filter(
                ativo=True,
                quadra=quadra,
                dia_semana=dia.weekday()
            ).order_by('hora_inicio')

            reservas = ReservaQuadra.objects.filter(
                data=dia,
                status='AGENDADA'
            )

            lista_horarios = []

            for horario in horarios:

                reserva = reservas.filter(
                    horario=horario
                ).first()

                horario_passado = False

                if dia == hoje and horario.hora_inicio <= agora:
                    horario_passado = True

                lista_horarios.append({
                    'horario': horario,
                    'reserva': reserva,
                    'horario_passado': horario_passado,
                    'pode_reservar': pode_reservar_dia and not horario_passado,
                })

            if lista_horarios:
                possui_horarios = True

            quadras_dia.append({
                'quadra': quadra,
                'horarios': lista_horarios,
            })

        if possui_horarios:
            proximos_dias.append({
                'data': dia,
                'quadras': quadras_dia,
                'pode_reservar': pode_reservar_dia,
            })

    return render(
        request,
        'quadras/index.html',
        {
            'proximos_dias': proximos_dias
        }
    )


@login_required
def reservar_quadra(request, horario_id):

    jogador = Jogador.objects.filter(
        usuario=request.user
    ).first()

    if not jogador:
        return redirect('/meu-perfil/')

    horario = get_object_or_404(
        ConfiguracaoHorarioQuadra,
        id=horario_id,
        ativo=True
    )

    data_reserva_str = (
        request.GET.get('data') or
        request.POST.get('data_reserva')
    )

    if not data_reserva_str:
        messages.error(
            request,
            'Data da reserva não informada.'
        )
        return redirect('/quadras/')

    data_reserva = date.fromisoformat(data_reserva_str)

    hoje = date.today()
    agora = timezone.localtime().time()

    if data_reserva != hoje:
        messages.error(
            request,
            'As reservas só podem ser feitas no próprio dia.'
        )
        return redirect('/quadras/')

    if horario.hora_inicio <= agora:
        messages.error(
            request,
            'Este horário já passou e não pode mais ser reservado.'
        )
        return redirect('/quadras/')

    if data_reserva.weekday() != horario.dia_semana:
        messages.error(
            request,
            'Este horário não pertence ao dia da semana selecionado.'
        )
        return redirect('/quadras/')

    reserva_existente = ReservaQuadra.objects.filter(
        data=data_reserva,
        horario=horario,
        status='AGENDADA'
    ).exists()

    if reserva_existente:
        messages.error(
            request,
            'Este horário já está reservado.'
        )
        return redirect('/quadras/')

    ja_reservou_no_dia = ReservaQuadra.objects.filter(
        reservado_por=jogador,
        data=data_reserva,
        status='AGENDADA'
    ).exists()

    if ja_reservou_no_dia:
        messages.error(
            request,
            'Você já possui uma reserva neste dia.'
        )
        return redirect('/quadras/')

    jogadores_lista = Jogador.objects.filter(
        ativo=True
    ).order_by(
        'nome'
    )

    if request.method == 'POST':

        jogadores_ids = request.POST.getlist('jogadores')
        observacao = request.POST.get('observacao')

        jogadores_selecionados = Jogador.objects.filter(
            id__in=jogadores_ids
        ).order_by(
            'nome'
        )

        jogadores_nomes = '\n'.join(
            [j.nome for j in jogadores_selecionados]
        )

        if not jogadores_nomes:
            messages.error(
                request,
                'Selecione pelo menos um jogador.'
            )
            return redirect(
                f'/quadras/reservar/{horario.id}/?data={data_reserva}'
            )

        ReservaQuadra.objects.create(
            data=data_reserva,
            horario=horario,
            reservado_por=jogador,
            jogadores=jogadores_nomes,
            observacao=observacao,
            status='AGENDADA'
        )

        messages.success(
            request,
            'Reserva realizada com sucesso.'
        )

        return redirect('/quadras/')

    return render(
        request,
        'quadras/reservar.html',
        {
            'horario': horario,
            'jogador': jogador,
            'data_reserva': data_reserva,
            'jogadores_lista': jogadores_lista,
        }
    )


@login_required
def cancelar_reserva_quadra(request, reserva_id):

    jogador = Jogador.objects.filter(
        usuario=request.user
    ).first()

    reserva = get_object_or_404(
        ReservaQuadra,
        id=reserva_id
    )

    if reserva.reservado_por != jogador and not request.user.is_staff:

        messages.error(
            request,
            'Você não tem permissão para cancelar esta reserva.'
        )

        return redirect('/quadras/')

    if reserva.checkin_realizado:

        messages.error(
            request,
            'Não é possível cancelar uma reserva após o check-in.'
        )

        return redirect('/quadras/')

    if reserva.status == 'CANCELADA':

        messages.error(
            request,
            'Esta reserva já foi cancelada.'
        )

        return redirect('/quadras/')

    reserva.status = 'CANCELADA'
    reserva.save()

    messages.success(
        request,
        'Reserva cancelada com sucesso.'
    )

    return redirect('/quadras/')


@staff_member_required
def gerar_horarios_quadra(request):

    quadras = Quadra.objects.filter(
        ativa=True
    ).order_by('nome')

    dias_semana = ConfiguracaoHorarioQuadra.DIAS_SEMANA

    if request.method == 'POST':

        quadra_id = request.POST.get('quadra')
        dias = request.POST.getlist('dias')
        hora_inicio_str = request.POST.get('hora_inicio')
        hora_fim_str = request.POST.get('hora_fim')
        intervalo = int(request.POST.get('intervalo', 60))

        quadra = get_object_or_404(
            Quadra,
            id=quadra_id
        )

        hora_inicio = datetime.strptime(
            hora_inicio_str,
            '%H:%M'
        )

        hora_fim = datetime.strptime(
            hora_fim_str,
            '%H:%M'
        )

        total_criados = 0
        total_existentes = 0

        for dia in dias:

            dia_int = int(dia)

            atual = hora_inicio

            while atual < hora_fim:

                proximo = atual + timedelta(
                    minutes=intervalo
                )

                if proximo > hora_fim:
                    break

                _, criado = ConfiguracaoHorarioQuadra.objects.get_or_create(
                    quadra=quadra,
                    dia_semana=dia_int,
                    hora_inicio=atual.time(),
                    hora_fim=proximo.time(),
                    defaults={
                        'ativo': True
                    }
                )

                if criado:
                    total_criados += 1
                else:
                    total_existentes += 1

                atual = proximo

        messages.success(
            request,
            f'{total_criados} horários criados. {total_existentes} já existiam.'
        )

        return redirect('/gerar-horarios-quadra/')

    return render(
        request,
        'quadras/gerar_horarios.html',
        {
            'quadras': quadras,
            'dias_semana': dias_semana,
        }
    )

@login_required
def checkin_quadra(request, reserva_id):

    jogador = Jogador.objects.filter(
        usuario=request.user
    ).first()

    reserva = get_object_or_404(
        ReservaQuadra,
        id=reserva_id,
        reservado_por=jogador,
        status='AGENDADA'
    )

    if reserva.checkin_realizado:
        return JsonResponse({
            'ok': False,
            'mensagem': 'Check-in já realizado.'
        })

    hoje = date.today()

    if reserva.data != hoje:
        return JsonResponse({
            'ok': False,
            'mensagem': 'O check-in só pode ser feito no dia da reserva.'
        })

    agora = timezone.localtime()

    inicio_reserva = timezone.make_aware(
        datetime.combine(
            reserva.data,
            reserva.horario.hora_inicio
        )
    )

    fim_reserva = timezone.make_aware(
        datetime.combine(
            reserva.data,
            reserva.horario.hora_fim
        )
    )

    liberado_a_partir = inicio_reserva - timedelta(minutes=30)

    if agora < liberado_a_partir:
        return JsonResponse({
            'ok': False,
            'mensagem': 'Check-in liberado somente 30 minutos antes do horário.'
        })

    if agora > fim_reserva:
        return JsonResponse({
            'ok': False,
            'mensagem': 'O horário da reserva já encerrou.'
        })

    try:
        latitude = float(request.POST.get('latitude'))
        longitude = float(request.POST.get('longitude'))
    except:
        return JsonResponse({
            'ok': False,
            'mensagem': 'Localização inválida.'
        })

    # TROQUE PELAS COORDENADAS REAIS DO CLUBE
    LAT_CLUBE = -28.29805
    LNG_CLUBE = -53.50565

    RAIO_PERMITIDO = 100

    def calcular_distancia(lat1, lon1, lat2, lon2):

        raio_terra = 6371000

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)

        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2 +
            math.cos(phi1) *
            math.cos(phi2) *
            math.sin(delta_lambda / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        return raio_terra * c

    distancia = calcular_distancia(
        latitude,
        longitude,
        LAT_CLUBE,
        LNG_CLUBE
    )

    if distancia > RAIO_PERMITIDO:
        return JsonResponse({
            'ok': False,
            'mensagem': f'Você está a {int(distancia)} metros da quadra. O limite é {RAIO_PERMITIDO} metros.'
        })

    reserva.checkin_realizado = True
    reserva.checkin_data_hora = timezone.now()
    reserva.checkin_latitude = latitude
    reserva.checkin_longitude = longitude
    reserva.checkin_distancia_metros = round(distancia, 2)
    reserva.status = 'CHECKIN'
    reserva.save()

    return JsonResponse({
        'ok': True,
        'mensagem': f'Check-in realizado com sucesso! Distância registrada: {int(distancia)} metros.'
    })

from django.db.models import Count


@staff_member_required
def relatorio_quadras(request):

    hoje = date.today()

    reservas_mes = ReservaQuadra.objects.filter(
        data__year=hoje.year,
        data__month=hoje.month
    )

    total_reservas = reservas_mes.count()

    total_checkin = reservas_mes.filter(
        status='CHECKIN'
    ).count()

    total_canceladas = reservas_mes.filter(
        status='CANCELADA'
    ).count()

    total_agendadas = reservas_mes.filter(
        status='AGENDADA'
    ).count()

    total_no_show = reservas_mes.filter(
        status='NO_SHOW'
    ).count()

    reservas_por_quadra = reservas_mes.values(
        'horario__quadra__nome'
    ).annotate(
        total=Count('id')
    ).order_by(
        '-total'
    )

    top_jogadores = reservas_mes.values(
        'reservado_por__nome'
    ).annotate(
        total=Count('id')
    ).order_by(
        '-total'
    )[:10]

    ultimas_reservas = reservas_mes.select_related(
        'reservado_por',
        'horario',
        'horario__quadra'
    ).order_by(
        '-data',
        '-criado_em'
    )[:30]

    return render(
        request,
        'quadras/relatorio.html',
        {
            'total_reservas': total_reservas,
            'total_checkin': total_checkin,
            'total_canceladas': total_canceladas,
            'total_agendadas': total_agendadas,
            'total_no_show': total_no_show,
            'reservas_por_quadra': reservas_por_quadra,
            'top_jogadores': top_jogadores,
            'ultimas_reservas': ultimas_reservas,
        }
    )

def torneios_historico(request):

    torneios = RegistroTorneio.objects.filter(
        ativo=True
    ).order_by(
        '-data_inicio',
        '-id'
    )

    totais = torneios.aggregate(
        total_inscritos_geral=Sum('total_inscritos'),
        total_jogos_geral=Sum('total_jogos'),
        total_categorias_geral=Sum('total_categorias'),
    )

    return render(
        request,
        'historico_torneios/lista.html',
        {
            'torneios': torneios,
            'total_torneios_geral': torneios.count(),
            'total_inscritos_geral': totais['total_inscritos_geral'] or 0,
            'total_jogos_geral': totais['total_jogos_geral'] or 0,
            'total_categorias_geral': totais['total_categorias_geral'] or 0,
        }
    )


def detalhe_torneio_historico(request, torneio_id):

    torneio = get_object_or_404(
        RegistroTorneio,
        id=torneio_id,
        ativo=True
    )

    resultados = ResultadoTorneio.objects.filter(
        torneio=torneio
    ).order_by(
        'ordem',
        'categoria'
    )

    return render(
        request,
        'historico_torneios/detalhe.html',
        {
            'torneio': torneio,
            'resultados': resultados
        }
    )

def calendario(request):

    eventos = EventoCalendario.objects.filter(
        ativo=True
    ).order_by(
        'data_inicio',
        'nome'
    )

    return render(
        request,
        'calendario/index.html',
        {
            'eventos': eventos,
        }
    )

def estatisticas_championship(request):

    jogadores_ids_sistema = ParticipanteJogo.objects.filter(
        jogo__status='CONFIRMADO',
        jogo__tipo_jogo='CHAMPIONSHIP_DUPLAS'
    ).values_list(
        'jogador_id',
        flat=True
    ).distinct()

    jogadores = Jogador.objects.filter(
        id__in=jogadores_ids_sistema
    ) | Jogador.objects.filter(
        jogos_historicos__gt=0
    ) | Jogador.objects.filter(
        vitorias_historicas__gt=0
    ) | Jogador.objects.filter(
        derrotas_historicas__gt=0
    ) | Jogador.objects.filter(
        titulos_cd__gt=0
    ) | Jogador.objects.filter(
        vice_cd__gt=0
    )

    jogadores = jogadores.distinct().exclude(
        usuario__is_staff=True
    ).exclude(
        usuario__is_superuser=True
    ).order_by('nome')

    estatisticas = []

    for jogador in jogadores:

        participacoes = ParticipanteJogo.objects.filter(
            jogador=jogador,
            jogo__status='CONFIRMADO',
            jogo__tipo_jogo='CHAMPIONSHIP_DUPLAS'
        )

        jogos_sistema = participacoes.count()
        vitorias_sistema = participacoes.filter(vencedor=True).count()
        derrotas_sistema = participacoes.filter(vencedor=False).count()

        total_jogos = jogador.jogos_historicos + jogos_sistema
        total_vitorias = jogador.vitorias_historicas + vitorias_sistema
        total_derrotas = jogador.derrotas_historicas + derrotas_sistema

        aproveitamento = 0

        if total_jogos > 0:
            aproveitamento = round(
                (total_vitorias / total_jogos) * 100,
                1
            )

        estatisticas.append({
            'jogador': jogador,
            'jogos': total_jogos,
            'vitorias': total_vitorias,
            'derrotas': total_derrotas,
            'aproveitamento': aproveitamento,
            'titulos': jogador.titulos_cd,
            'vices': jogador.vice_cd,
            'semifinais': jogador.semifinal_cd,
        })

    estatisticas = sorted(
        estatisticas,
        key=lambda item: (
            item['titulos'],
            item['jogos'],
            item['vitorias'],
            item['aproveitamento'],
            item['jogador'].nome
        ),
        reverse=True
    )

    campeoes_diferentes = len([
        item for item in estatisticas
        if item['titulos'] > 0
    ])

    jogadores_mais_100_vitorias = len([
        item for item in estatisticas
        if item['vitorias'] >= 100
    ])

    jogadores_minimo_50 = [
        item for item in estatisticas
        if item['jogos'] >= 50
    ]

    melhor_aproveitamento = None

    if jogadores_minimo_50:
        melhor_aproveitamento = sorted(
            jogadores_minimo_50,
            key=lambda item: (
                item['aproveitamento'],
                item['vitorias'],
                item['jogos']
            ),
            reverse=True
        )[0]

    return render(
        request,
        'estatisticas/championship.html',
        {
            'estatisticas': estatisticas,
            'total_jogadores': len(estatisticas),
            'campeoes_diferentes': campeoes_diferentes,
            'jogadores_mais_100_vitorias': jogadores_mais_100_vitorias,
            'melhor_aproveitamento': melhor_aproveitamento,
        }
    )
    
def selos_championship(request):

    jogadores_ids_sistema = ParticipanteJogo.objects.filter(
        jogo__status='CONFIRMADO',
        jogo__tipo_jogo='CHAMPIONSHIP_DUPLAS'
    ).values_list(
        'jogador_id',
        flat=True
    ).distinct()

    jogadores = Jogador.objects.filter(
        id__in=jogadores_ids_sistema
    ) | Jogador.objects.filter(
        jogos_historicos__gt=0
    ) | Jogador.objects.filter(
        vitorias_historicas__gt=0
    ) | Jogador.objects.filter(
        derrotas_historicas__gt=0
    ) | Jogador.objects.filter(
        titulos_cd__gt=0
    ) | Jogador.objects.filter(
        vice_cd__gt=0
    )

    jogadores = jogadores.distinct().exclude(
        usuario__is_staff=True
    ).exclude(
        usuario__is_superuser=True
    ).order_by('nome')

    lista_jogadores = []

    conquistas_contadores = {
        'campeao': 0,
        'bicampeao': 0,
        'tricampeao': 0,
        'vitorias_100': 0,
        'vitorias_200': 0,
        'vitorias_300': 0,
        'jogos_100': 0,
        'jogos_200': 0,
        'jogos_300': 0,
        'elite': 0,
    }

    for jogador in jogadores:

        participacoes = ParticipanteJogo.objects.filter(
            jogador=jogador,
            jogo__status='CONFIRMADO',
            jogo__tipo_jogo='CHAMPIONSHIP_DUPLAS'
        )

        jogos_sistema = participacoes.count()
        vitorias_sistema = participacoes.filter(vencedor=True).count()
        derrotas_sistema = participacoes.filter(vencedor=False).count()

        total_jogos = jogador.jogos_historicos + jogos_sistema
        total_vitorias = jogador.vitorias_historicas + vitorias_sistema
        total_derrotas = jogador.derrotas_historicas + derrotas_sistema

        aproveitamento = 0
        if total_jogos > 0:
            aproveitamento = round((total_vitorias / total_jogos) * 100, 1)

        selos = []

        if jogador.titulos_cd >= 1:
            selos.append({'classe': 'selo-campeao', 'texto': '🏆 Campeão'})
            conquistas_contadores['campeao'] += 1

        if jogador.titulos_cd >= 2:
            selos.append({'classe': 'selo-bicampeao', 'texto': '⭐ Bicampeão'})
            conquistas_contadores['bicampeao'] += 1

        if jogador.titulos_cd >= 3:
            selos.append({'classe': 'selo-tricampeao', 'texto': '👑 Tricampeão'})
            conquistas_contadores['tricampeao'] += 1

        if total_vitorias >= 100:
            selos.append({'classe': 'selo-v100', 'texto': '🔥 100+ Vitórias'})
            conquistas_contadores['vitorias_100'] += 1

        if total_vitorias >= 200:
            selos.append({'classe': 'selo-v200', 'texto': '🔥 200+ Vitórias'})
            conquistas_contadores['vitorias_200'] += 1

        if total_vitorias >= 300:
            selos.append({'classe': 'selo-v300', 'texto': '🔥 300+ Vitórias'})
            conquistas_contadores['vitorias_300'] += 1

        if total_jogos >= 100:
            selos.append({'classe': 'selo-j100', 'texto': '🎾 100+ Jogos'})
            conquistas_contadores['jogos_100'] += 1

        if total_jogos >= 200:
            selos.append({'classe': 'selo-j200', 'texto': '🎾 200+ Jogos'})
            conquistas_contadores['jogos_200'] += 1

        if total_jogos >= 300:
            selos.append({'classe': 'selo-j300', 'texto': '🏟️ 300+ Jogos'})
            conquistas_contadores['jogos_300'] += 1

        if aproveitamento >= 70 and total_jogos >= 100:
            selos.append({'classe': 'selo-elite', 'texto': '🎯 Elite'})
            conquistas_contadores['elite'] += 1

        if selos:
            lista_jogadores.append({
                'jogador': jogador,
                'jogos': total_jogos,
                'vitorias': total_vitorias,
                'derrotas': total_derrotas,
                'titulos': jogador.titulos_cd,
                'aproveitamento': aproveitamento,
                'selos': selos,
                'total_selos': len(selos),
            })

    lista_jogadores = sorted(
        lista_jogadores,
        key=lambda item: (
            item['total_selos'],
            item['titulos'],
            item['vitorias'],
            item['jogos']
        ),
        reverse=True
    )

    return render(
        request,
        'estatisticas/selos_championship.html',
        {
            'jogadores': lista_jogadores,
            'contadores': conquistas_contadores,
        }
    )    

from django.db.models import Count


def selos_championship(request):

    jogadores_ids_sistema = ParticipanteJogo.objects.filter(
        jogo__status='CONFIRMADO',
        jogo__tipo_jogo='CHAMPIONSHIP_DUPLAS'
    ).values_list(
        'jogador_id',
        flat=True
    ).distinct()

    jogadores = Jogador.objects.filter(
        id__in=jogadores_ids_sistema
    ) | Jogador.objects.filter(
        jogos_historicos__gt=0
    ) | Jogador.objects.filter(
        vitorias_historicas__gt=0
    ) | Jogador.objects.filter(
        derrotas_historicas__gt=0
    ) | Jogador.objects.filter(
        titulos_cd__gt=0
    ) | Jogador.objects.filter(
        vice_cd__gt=0
    )

    jogadores = jogadores.distinct().exclude(
        usuario__is_staff=True
    ).exclude(
        usuario__is_superuser=True
    ).order_by('nome')

    lista_jogadores = []

    contadores = {
        'campeao': 0,
        'bicampeao': 0,
        'tricampeao': 0,
        'vitorias_100': 0,
        'vitorias_200': 0,
        'vitorias_300': 0,
        'jogos_100': 0,
        'jogos_200': 0,
        'jogos_300': 0,
        'elite': 0,
    }

    for jogador in jogadores:

        participacoes = ParticipanteJogo.objects.filter(
            jogador=jogador,
            jogo__status='CONFIRMADO',
            jogo__tipo_jogo='CHAMPIONSHIP_DUPLAS'
        )

        jogos_sistema = participacoes.count()
        vitorias_sistema = participacoes.filter(vencedor=True).count()
        derrotas_sistema = participacoes.filter(vencedor=False).count()

        total_jogos = jogador.jogos_historicos + jogos_sistema
        total_vitorias = jogador.vitorias_historicas + vitorias_sistema
        total_derrotas = jogador.derrotas_historicas + derrotas_sistema

        aproveitamento = 0

        if total_jogos > 0:
            aproveitamento = round(
                (total_vitorias / total_jogos) * 100,
                1
            )

        selos = []

        if jogador.titulos_cd >= 1:
            selos.append({
                'texto': 'Campeão',
                'imagem': 'img/patches/campeao.png'
            })
            contadores['campeao'] += 1

        if jogador.titulos_cd >= 2:
            selos.append({
                'texto': 'Bicampeão',
                'imagem': 'img/patches/bicampeao.png'
            })
            contadores['bicampeao'] += 1

        if jogador.titulos_cd >= 3:
            selos.append({
                'texto': 'Tricampeão',
                'imagem': 'img/patches/tricampeao.png'
            })
            contadores['tricampeao'] += 1

        if total_vitorias >= 100:
            selos.append({
                'texto': '100+ Vitórias',
                'imagem': 'img/patches/100_vitorias.png'
            })
            contadores['vitorias_100'] += 1

        if total_vitorias >= 200:
            selos.append({
                'texto': '200+ Vitórias',
                'imagem': 'img/patches/200_vitorias.png'
            })
            contadores['vitorias_200'] += 1

        if total_vitorias >= 300:
            selos.append({
                'texto': '300+ Vitórias',
                'imagem': 'img/patches/300_vitorias.png'
            })
            contadores['vitorias_300'] += 1

        if total_jogos >= 100:
            selos.append({
                'texto': '100+ Jogos',
                'imagem': 'img/patches/100_jogos.png'
            })
            contadores['jogos_100'] += 1

        if total_jogos >= 200:
            selos.append({
                'texto': '200+ Jogos',
                'imagem': 'img/patches/200_jogos.png'
            })
            contadores['jogos_200'] += 1

        if total_jogos >= 300:
            selos.append({
                'texto': '300+ Jogos',
                'imagem': 'img/patches/300_jogos.png'
            })
            contadores['jogos_300'] += 1

        if aproveitamento >= 70 and total_jogos >= 100:
            selos.append({
                'texto': 'Elite',
                'imagem': 'img/patches/elite.png'
            })
            contadores['elite'] += 1

        if selos:
            lista_jogadores.append({
                'jogador': jogador,
                'jogos': total_jogos,
                'vitorias': total_vitorias,
                'derrotas': total_derrotas,
                'titulos': jogador.titulos_cd,
                'aproveitamento': aproveitamento,
                'selos': selos,
                'total_selos': len(selos),
            })

    lista_jogadores = sorted(
        lista_jogadores,
        key=lambda item: (
            item['total_selos'],
            item['titulos'],
            item['vitorias'],
            item['jogos']
        ),
        reverse=True
    )

    return render(
        request,
        'championship/selos.html',
        {
            'jogadores': lista_jogadores,
            'contadores': contadores,
        }
    )

@staff_member_required
def painel_sistema(request):

    total_jogadores = Jogador.objects.count()
    total_jogos = Jogo.objects.count()
    total_torneios = Torneio.objects.count()
    total_reservas = ReservaQuadra.objects.count()
    total_notificacoes = Notificacao.objects.count()

    return render(
        request,
        'sistema/painel.html',
        {
            'total_jogadores': total_jogadores,
            'total_jogos': total_jogos,
            'total_torneios': total_torneios,
            'total_reservas': total_reservas,
            'total_notificacoes': total_notificacoes,
        }
    )

@login_required
def notificacoes(request):

    jogador = Jogador.objects.filter(
        usuario=request.user
    ).first()

    if not jogador:
        return redirect('/meu-perfil/')

    lista = Notificacao.objects.filter(
        jogador=jogador,
        lida=False
    ).order_by(
        '-criada_em'
    )

    return render(
        request,
        'notificacoes/index.html',
        {
            'notificacoes': lista
        }
    )


@login_required
def detalhe_notificacao_resultado(request, jogo_id):

    jogador_logado = Jogador.objects.filter(
        usuario=request.user
    ).first()

    if not jogador_logado:
        return redirect('/meu-perfil/')

    jogo = get_object_or_404(
        Jogo.objects.prefetch_related(
            'participantes',
            'participantes__jogador',
            'sets'
        ),
        id=jogo_id
    )

    participacao = ParticipanteJogo.objects.filter(
        jogo=jogo,
        jogador=jogador_logado
    ).first()

    if not participacao:
        messages.error(
            request,
            'Você não participa deste jogo.'
        )
        return redirect('/notificacoes/')

    if jogo.status != 'PENDENTE':
        Notificacao.objects.filter(
            jogador=jogador_logado,
            link=f'/resultado-pendente/{jogo.id}/'
        ).delete()

        if jogo.status == 'CONFIRMADO':
            messages.info(
                request,
                'Este resultado já foi confirmado.'
            )
        else:
            messages.info(
                request,
                'Este resultado já foi contestado.'
            )

        return redirect('/meus-jogos/')

    participantes = ParticipanteJogo.objects.filter(
        jogo=jogo
    ).select_related(
        'jogador'
    ).order_by(
        'lado',
        'id'
    )

    return render(
        request,
        'notificacoes/resultado.html',
        {
            'jogo': jogo,
            'participantes': participantes,
            'participacao': participacao,
        }
    )


@login_required
def abrir_notificacao(request, notificacao_id):

    jogador = Jogador.objects.filter(
        usuario=request.user
    ).first()

    if not jogador:
        return redirect('/meu-perfil/')

    notificacao = get_object_or_404(
        Notificacao,
        id=notificacao_id,
        jogador=jogador
    )

    notificacao.lida = True
    notificacao.save(update_fields=['lida'])

    return redirect('/meus-jogos/')