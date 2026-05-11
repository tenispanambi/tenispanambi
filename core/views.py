from django.shortcuts import (
    render,
    get_object_or_404,
    redirect
)

from django.contrib.auth.models import User
from django.contrib.auth import login

from django.contrib.auth.decorators import login_required

from .services.ranking import recalcular_ranking

from .services.chaveamento import gerar_chaveamento

from .services.avanco import avancar_vencedor

from .models import (
    RankingJogador,
    Jogador,
    ParticipanteJogo,
    Jogo,
    SetJogo,
    Torneio,
    InscricaoTorneio,
    CategoriaTorneio,
)
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    ultimos_jogos = Jogo.objects.all().order_by('-data_jogo')[:5]

    ranking_top = RankingJogador.objects.filter(
        categoria__categoria='A'
    ).order_by('posicao')[:5]

    return render(
        request,
        'core/index.html',
        {
            'ultimos_jogos': ultimos_jogos,
            'ranking': ranking_top,
        }
    )


@login_required
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


@login_required
def headtohead(request):
    jogadores = Jogador.objects.all().order_by('nome')

    jogador1_id = request.GET.get('j1')
    jogador2_id = request.GET.get('j2')

    jogador1 = None
    jogador2 = None

    confrontos = []
    parceiros = []

    vitorias_j1 = 0
    vitorias_j2 = 0

    vitorias_juntos = 0
    derrotas_juntos = 0

    if jogador1_id and jogador2_id:
        jogador1 = get_object_or_404(
            Jogador,
            id=jogador1_id
        )

        jogador2 = get_object_or_404(
            Jogador,
            id=jogador2_id
        )

        jogos = Jogo.objects.all().order_by('-data_jogo')

        for jogo in jogos:
            participantes = jogo.participantes.all()

            p1 = None
            p2 = None

            for p in participantes:
                if p.jogador.id == jogador1.id:
                    p1 = p

                if p.jogador.id == jogador2.id:
                    p2 = p

            if p1 and p2:
                if p1.lado == p2.lado:
                    parceiros.append(jogo)

                    if p1.vencedor:
                        vitorias_juntos += 1
                    else:
                        derrotas_juntos += 1
                else:
                    confrontos.append(jogo)

                    if p1.vencedor:
                        vitorias_j1 += 1
                    else:
                        vitorias_j2 += 1

    return render(
        request,
        'headtohead/index.html',
        {
            'jogadores': jogadores,
            'jogador1': jogador1,
            'jogador2': jogador2,
            'confrontos': confrontos,
            'parceiros': parceiros,
            'vitorias_j1': vitorias_j1,
            'vitorias_j2': vitorias_j2,
            'vitorias_juntos': vitorias_juntos,
            'derrotas_juntos': derrotas_juntos,
        }
    )


@login_required
def meu_painel(request):
    jogador = Jogador.objects.get(
        usuario=request.user
    )

    jogos_query = ParticipanteJogo.objects.filter(
        jogador=jogador
    ).select_related(
        'jogo'
    ).order_by(
        '-jogo__data_jogo'
    )

    ranking = RankingJogador.objects.filter(
        jogador=jogador
    ).first()

    vitorias = jogos_query.filter(
        vencedor=True
    ).count()

    derrotas = jogos_query.filter(
        vencedor=False
    ).count()

    jogos = jogos_query[:10]

    total = vitorias + derrotas

    aproveitamento = 0

    if total > 0:
        aproveitamento = round(
            (vitorias / total) * 100,
            1
        )

    return render(
        request,
        'jogador/painel.html',
        {
            'jogador': jogador,
            'ranking': ranking,
            'jogos': jogos,
            'vitorias': vitorias,
            'derrotas': derrotas,
            'total': total,
            'aproveitamento': aproveitamento,
        }
    )


@login_required
def lancar_resultado(
    request,
    jogo_id
):

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

            adversarios.append(
                p.jogador
            )

    if request.method == 'POST':

        placar_a = int(
            request.POST.get('placar_a')
        )

        placar_b = int(
            request.POST.get('placar_b')
        )

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

        return redirect(
            'meus_jogos'
        )

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

        avancar_vencedor(
            jogo
        )

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
def gerar_torneio(
    request,
    torneio_id,
    categoria_id
):

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

    return redirect(
        'torneios'
    )

@login_required
def chaveamento(
    request,
    torneio_id,
    categoria_id
):

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
def meus_jogos(request):

    jogador = Jogador.objects.get(
        usuario=request.user
    )

    participacoes = ParticipanteJogo.objects.filter(
        jogador=jogador
    ).select_related(
        'jogo',
        'jogo__torneio',
        'jogo__categoria'
    ).order_by(
        '-jogo__data_jogo'
    )

    return render(
        request,
        'jogador/meus_jogos.html',
        {
            'participacoes': participacoes
        }
    )

def cadastro(request):

    if request.method == 'POST':

        nome = request.POST.get('nome')
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        if User.objects.filter(username=username).exists():
            return render(request, 'registration/cadastro.html', {
                'erro': 'Este usuário já existe.'
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=senha
        )

        jogador = Jogador.objects.create(
            usuario=user,
            nome=nome,
            email=email,
            categoria='C',
            ativo=True
        )

        login(request, user)

        return redirect('meu_painel')

    return render(request, 'registration/cadastro.html')