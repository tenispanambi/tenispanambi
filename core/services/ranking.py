from django.db.models import Q

from core.models import (
    RankingJogador,
    ParticipanteJogo,
    Jogo,
    InscricaoTorneio,
)


def recalcular_ranking(torneio, categoria):

    if not torneio or not categoria:
        return

    RankingJogador.objects.filter(
        torneio=torneio,
        categoria=categoria
    ).delete()

    jogos = Jogo.objects.filter(
        torneio=torneio,
        categoria=categoria,
        status='CONFIRMADO',
        tipo_jogo='CHAMPIONSHIP_DUPLAS'
    ).filter(
        Q(fase__isnull=True) | Q(fase='')
    ).order_by(
        'rodada',
        'id'
    )

    controle_rodadas = {}
    controle_jogos = set()
    resultados_por_jogador = {}

    for jogo in jogos:

        participantes = ParticipanteJogo.objects.filter(
            jogo=jogo
        )

        for p in participantes:

            jogador = p.jogador

            chave_jogo = f'{jogo.id}_{jogador.id}'

            if chave_jogo in controle_jogos:
                continue

            controle_jogos.add(chave_jogo)

            inscrito = InscricaoTorneio.objects.filter(
                torneio=torneio,
                categoria=categoria,
                jogador=jogador,
                ativo=True
            ).exists()

            if not inscrito:
                continue

            rodada = jogo.rodada or 0
            chave_rodada = f'{jogador.id}_{rodada}'

            if chave_rodada not in controle_rodadas:
                controle_rodadas[chave_rodada] = 0

            if controle_rodadas[chave_rodada] >= categoria.max_jogos_por_rodada:
                continue

            controle_rodadas[chave_rodada] += 1

            if p.lado == 'A':
                games_feitos = jogo.total_games_lado_a()
                games_sofridos = jogo.total_games_lado_b()
            else:
                games_feitos = jogo.total_games_lado_b()
                games_sofridos = jogo.total_games_lado_a()

            if p.vencedor:
                pontos = 20 + games_feitos
                vitoria = 1
                derrota = 0
            else:
                pontos = 5 + games_feitos
                vitoria = 0
                derrota = 1

            if jogador.id not in resultados_por_jogador:
                resultados_por_jogador[jogador.id] = {
                    'jogador': jogador,
                    'resultados': []
                }

            resultados_por_jogador[jogador.id]['resultados'].append({
                'pontos': pontos,
                'vitoria': vitoria,
                'derrota': derrota,
                'games_feitos': games_feitos,
                'games_sofridos': games_sofridos,
            })

    inscricoes = InscricaoTorneio.objects.filter(
        torneio=torneio,
        categoria=categoria,
        ativo=True
    )

    for inscricao in inscricoes:

        jogador = inscricao.jogador

        if jogador.id not in resultados_por_jogador:
            resultados_por_jogador[jogador.id] = {
                'jogador': jogador,
                'resultados': []
            }

    ranking_lista = []

    for dados in resultados_por_jogador.values():

        jogador = dados['jogador']

        melhores = sorted(
            dados['resultados'],
            key=lambda r: r['pontos'],
            reverse=True
        )

        if categoria.melhores_resultados and categoria.melhores_resultados > 0:
            melhores = melhores[:categoria.melhores_resultados]

        pontos = sum(r['pontos'] for r in melhores)
        vitorias = sum(r['vitoria'] for r in melhores)
        derrotas = sum(r['derrota'] for r in melhores)
        games_feitos = sum(r['games_feitos'] for r in melhores)
        games_sofridos = sum(r['games_sofridos'] for r in melhores)

        total_jogos = vitorias + derrotas

        aproveitamento = 0

        if total_jogos > 0:
            aproveitamento = round(
                (vitorias / total_jogos) * 100,
                2
            )

        ranking_lista.append({
            'jogador': jogador,
            'pontos': pontos,
            'vitorias': vitorias,
            'derrotas': derrotas,
            'games_feitos': games_feitos,
            'games_sofridos': games_sofridos,
            'aproveitamento': aproveitamento,
        })

    ranking_lista = sorted(
        ranking_lista,
        key=lambda r: (
            r['pontos'],
            r['vitorias'],
            r['games_feitos'] - r['games_sofridos'],
            r['games_feitos']
        ),
        reverse=True
    )

    total_jogadores = len(ranking_lista)

    for indice, item in enumerate(ranking_lista, start=1):

        status_ranking = ''

        # CLASSIFICADOS / PROMOVIDOS
        if categoria.classificados_finais and indice <= categoria.classificados_finais:

            if categoria.categoria in ['B', 'C']:
                status_ranking = 'PROMOVIDO'
            else:
                status_ranking = 'CLASSIFICADO'

        # REBAIXADOS
        if categoria.rebaixados and indice > total_jogadores - categoria.rebaixados:
            status_ranking = 'REBAIXADO'

        RankingJogador.objects.create(
            torneio=torneio,
            categoria=categoria,
            jogador=item['jogador'],
            pontos=item['pontos'],
            vitorias=item['vitorias'],
            derrotas=item['derrotas'],
            games_feitos=item['games_feitos'],
            games_sofridos=item['games_sofridos'],
            aproveitamento=item['aproveitamento'],
            posicao=indice,
            status_ranking=status_ranking
        )