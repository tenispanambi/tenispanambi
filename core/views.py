from django.shortcuts import (
    render,
    get_object_or_404,
    redirect
)

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count

from .services.ranking import recalcular_ranking
from .services.avanco import avancar_vencedor
from .services.chaveamento import gerar_chaveamento
from datetime import date

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
)


def home(request):
    total_jogadores = Jogador.objects.count()

    total_jogos = Jogo.objects.filter(
        status='CONFIRMADO'
    ).count()

    total_torneios = Torneio.objects.count()

    jogos_semana = Jogo.objects.filter(
        status='CONFIRMADO'
    ).count()

    ultimos_jogos = Jogo.objects.filter(
    status='CONFIRMADO'
    ).order_by('-data_jogo','-id')[:10]

    ranking_a = RankingJogador.objects.filter(
        categoria__categoria='A'
    ).order_by('posicao')[:5]

    ranking_b = RankingJogador.objects.filter(
        categoria__categoria='B'
    ).order_by('posicao')[:5]

    ranking_c = RankingJogador.objects.filter(
        categoria__categoria='C'
    ).order_by('posicao')[:5]

    proximos_torneios = Torneio.objects.filter(
        data_inicio__gte=date.today()
    ).order_by('data_inicio')[:3]

    return render(
        request,
        'core/index.html',
        {
            'total_jogadores': total_jogadores,
            'total_jogos': total_jogos,
            'total_torneios': total_torneios,
            'jogos_semana': jogos_semana,
            'ultimos_jogos': ultimos_jogos,
            'ranking_a': ranking_a,
            'ranking_b': ranking_b,
            'ranking_c': ranking_c,
            'proximos_torneios': proximos_torneios,
        }
    )


def cadastro(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        if User.objects.filter(username=username).exists():
            return render(
                request,
                'registration/cadastro.html',
                {
                    'erro': 'Este usuário já existe.'
                }
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=senha
        )

        user.is_active = False
        user.save()

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
    ranking_a = RankingJogador.objects.filter(
        categoria__categoria='A'
    ).order_by('posicao')

    ranking_b = RankingJogador.objects.filter(
        categoria__categoria='B'
    ).order_by('posicao')

    ranking_c = RankingJogador.objects.filter(
        categoria__categoria='C'
    ).order_by('posicao')

    return render(
        request,
        'ranking/lista.html',
        {
            'ranking_a': ranking_a,
            'ranking_b': ranking_b,
            'ranking_c': ranking_c,
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
).order_by(
    'nome'
)

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
        jogador1 = get_object_or_404(Jogador, id=jogador1_id)

        r1 = RankingJogador.objects.filter(
            jogador=jogador1
        ).first()

        if r1:
            ranking1 = f'{r1.posicao}º'

    if jogador2_id:
        jogador2 = get_object_or_404(Jogador, id=jogador2_id)

        r2 = RankingJogador.objects.filter(
            jogador=jogador2
        ).first()

        if r2:
            ranking2 = f'{r2.posicao}º'

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
        ).order_by('-data_jogo')

        if modalidade == 'SIMPLES':
            jogos = jogos.filter(tipo_jogo='SIMPLES')

        elif modalidade == 'DUPLAS':
            jogos = jogos.exclude(tipo_jogo='SIMPLES')

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
            percentual_h2h_1 = round((vitorias1 / total_h2h) * 100, 1)
            percentual_h2h_2 = round((vitorias2 / total_h2h) * 100, 1)

    return render(
        request,
        'headtohead/index.html',
        {
            'jogadores': jogadores,
            'jogador1': jogador1,
            'jogador2': jogador2,
            'modalidade': modalidade,

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

            'stats1': stats1,
            'stats2': stats2,
        }
    )

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
        ).order_by('-data_jogo')

        if modalidade == 'SIMPLES':
            jogos = jogos.filter(tipo_jogo='SIMPLES')

        elif modalidade == 'DUPLAS':
            jogos = jogos.exclude(tipo_jogo='SIMPLES')

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
            percentual_h2h_1 = round((vitorias1 / total_h2h) * 100, 1)
            percentual_h2h_2 = round((vitorias2 / total_h2h) * 100, 1)

    return render(
        request,
        'headtohead/index.html',
        {
            'jogadores': jogadores,
            'jogador1': jogador1,
            'jogador2': jogador2,
            'modalidade': modalidade,

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

    if adversarios:
        nome_fregues, dados_fregues = max(
            adversarios.items(),
            key=lambda x: x[1]['vitorias']
        )

        maior_fregues_detalhe = {
            'nome': nome_fregues,
            'jogos': dados_fregues['jogos'],
            'vitorias': dados_fregues['vitorias'],
            'derrotas': dados_fregues['derrotas'],
        }

        nome_rival, dados_rival = max(
            adversarios.items(),
            key=lambda x: x[1]['derrotas']
        )

        maior_rival_detalhe = {
            'nome': nome_rival,
            'jogos': dados_rival['jogos'],
            'vitorias': dados_rival['vitorias'],
            'derrotas': dados_rival['derrotas'],
        }

    if parceiros:
        nome_melhor, dados_melhor = max(
            parceiros.items(),
            key=lambda x: x[1]['vitorias']
        )

        melhor_parceiro_detalhe = {
            'nome': nome_melhor,
            'jogos': dados_melhor['jogos'],
            'vitorias': dados_melhor['vitorias'],
            'derrotas': dados_melhor['derrotas'],
        }

        nome_pior, dados_pior = max(
            parceiros.items(),
            key=lambda x: x[1]['derrotas']
        )

        pior_parceiro_detalhe = {
            'nome': nome_pior,
            'jogos': dados_pior['jogos'],
            'vitorias': dados_pior['vitorias'],
            'derrotas': dados_pior['derrotas'],
        }

    return render(
        request,
        'jogador/painel.html',
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

            # mantém compatibilidade caso ainda use em algum ponto
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
    jogos_validos = []

    for p in participacoes:
        jogo = p.jogo
        categoria = jogo.categoria
        rodada = jogo.rodada or 0

        p.contabilizado = False
        p.historico_valido = False
        p.motivo_desconsiderado = ''
        p.pontos_calculados = 0

        # Amistoso ou simples não entra no ranking, mas vale para histórico
        if jogo.tipo_jogo != 'CHAMPIONSHIP_DUPLAS':
            p.historico_valido = True
            p.motivo_desconsiderado = 'Jogo amistoso/simples: vale para histórico, mas não soma ranking.'
            continue

        if jogo.status != 'CONFIRMADO':
            p.motivo_desconsiderado = 'Jogo ainda não confirmado.'

        elif categoria and rodada > categoria.rodadas_contabilizadas:
            p.motivo_desconsiderado = 'Rodada fora do limite contabilizado.'

        else:
            categoria_id = categoria.id if categoria else 0
            chave = f'{jogador.id}_{categoria_id}_{rodada}'

            if chave not in controle_rodadas:
                controle_rodadas[chave] = 0

            if categoria and controle_rodadas[chave] >= categoria.max_jogos_por_rodada:
                p.motivo_desconsiderado = 'Excedeu o limite de jogos contabilizados nesta rodada.'
            else:
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

                jogos_validos.append(p)

    jogos_validos_ordenados = sorted(
        jogos_validos,
        key=lambda p: p.pontos_calculados,
        reverse=True
    )

    categorias_processadas = {}

    for p in jogos_validos_ordenados:
        categoria = p.jogo.categoria

        if not categoria:
            continue

        chave_categoria = categoria.id

        if chave_categoria not in categorias_processadas:
            categorias_processadas[chave_categoria] = 0

        if categorias_processadas[chave_categoria] < categoria.melhores_resultados:
            p.contabilizado = True
            categorias_processadas[chave_categoria] += 1
        else:
            p.contabilizado = False
            p.motivo_desconsiderado = 'Fora dos melhores resultados.'

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
        placar_a = int(request.POST.get('placar_a'))
        placar_b = int(request.POST.get('placar_b'))

        jogo.sets.all().delete()

        SetJogo.objects.create(
            jogo=jogo,
            numero_set=1,
            games_lado_a=placar_a,
            games_lado_b=placar_b
        )

        vencedor_lado = 'A'

        if placar_b > placar_a:
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
    jogo = get_object_or_404(
        Jogo,
        id=jogo_id
    )

    jogo.status = 'CONTESTADO'
    jogo.save()

    return redirect('resultados_pendentes')


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
        jogador.email = request.POST.get('email')
        jogador.telefone = request.POST.get('telefone')
        jogador.cidade = request.POST.get('cidade')
        jogador.categoria = request.POST.get('categoria')
        jogador.nivel = request.POST.get('nivel')
        jogador.mao_dominante = request.POST.get('mao_dominante')
        jogador.raquete = request.POST.get('raquete')
        jogador.instagram = request.POST.get('instagram')

        if request.FILES.get('foto'):
            jogador.foto = request.FILES.get('foto')

        jogador.save()

        return redirect('meu_perfil')

    return render(
        request,
        'jogador/meu_perfil.html',
        {
            'jogador': jogador
        }
    )
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect


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


def logout_view(request):

    logout(request)

    return redirect('/')


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
        ativo=True
    ).exclude(
        id=jogador_logado.id
    ).order_by('nome')

    jogadores_categoria = Jogador.objects.filter(
        ativo=True,
        categoria=jogador_logado.categoria
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

        games_a = int(request.POST.get('games_a'))
        games_b = int(request.POST.get('games_b'))

        data_jogo = date.fromisoformat(data_jogo_str)

        torneio = None
        categoria = None
        tipo_jogo_salvar = 'SIMPLES'

        if tipo_jogo_form == 'DUPLAS':

            if not torneio_duplas_categoria:
                messages.error(
                    request,
                    'Não existe torneio de ranking em duplas aberto ou em fase finais para sua categoria.'
                )
                return redirect('/lancar-jogo/')

            categoria = torneio_duplas_categoria
            torneio = categoria.torneio

            if torneio.status == 'ENCERRADO':
                messages.error(
                    request,
                    'Este torneio está encerrado definitivamente.'
                )
                return redirect('/lancar-jogo/')

            if torneio.status in ['ABERTO', 'EM_ANDAMENTO']:

                if fase:
                    messages.error(
                        request,
                        'As finais ainda não foram liberadas para este torneio.'
                    )
                    return redirect('/lancar-jogo/')

                if not rodada:
                    messages.error(
                        request,
                        'Informe a rodada do jogo classificatório.'
                    )
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

            if not parceiro_a_id or not adversario_2_id:
                messages.error(
                    request,
                    'Para jogo de duplas, informe parceiro e adversário 2.'
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
                        'Em jogos de duplas, todos os jogadores precisam ser da mesma categoria.'
                    )
                    return redirect('/lancar-jogo/')

            tipo_jogo_salvar = 'CHAMPIONSHIP_DUPLAS'

        else:

            rodada = None
            fase = None
            torneio = None
            categoria = None
            tipo_jogo_salvar = 'SIMPLES'

            adversario_1 = Jogador.objects.get(
                id=adversario_1_id
            )

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

        if tipo_jogo_form == 'DUPLAS':

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

        if tipo_jogo_form == 'DUPLAS':

            ParticipanteJogo.objects.create(
                jogo=jogo,
                jogador=adversario_2,
                lado='B'
            )

        SetJogo.objects.create(
            jogo=jogo,
            numero_set=1,
            games_lado_a=games_a,
            games_lado_b=games_b
        )

        lado_vencedor = 'A'

        if games_b > games_a:
            lado_vencedor = 'B'

        participantes = ParticipanteJogo.objects.filter(
            jogo=jogo
        )

        for p in participantes:
            p.vencedor = p.lado == lado_vencedor
            p.save()

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
        return redirect('/meu-perfil/')

    jogo = get_object_or_404(
        Jogo,
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

    if jogo.status != 'PENDENTE':
        messages.error(
            request,
            'Este jogo já foi confirmado ou contestado.'
        )
        return redirect('/meus-jogos/')

    if participacao.lado != 'B':
        messages.error(
            request,
            'A confirmação deve ser feita pelo adversário.'
        )
        return redirect('/meus-jogos/')

    jogo.status = 'CONFIRMADO'
    jogo.save()

    if jogo.tipo_jogo == 'CHAMPIONSHIP_DUPLAS':
        recalcular_ranking(
            jogo.torneio,
            jogo.categoria
        )

    messages.success(
        request,
        'Resultado confirmado com sucesso.'
    )

    return redirect('/meus-jogos/')