from core.models import RankingJogador, ParticipanteJogo


def pontos_championship(vencedor, games_feitos):
    if vencedor:
        return 20 + games_feitos

    return 5 + games_feitos


def recalcular_ranking(torneio, categoria):
    RankingJogador.objects.filter(
        torneio=torneio,
        categoria=categoria
    ).delete()

    participantes = ParticipanteJogo.objects.filter(
        jogo__torneio=torneio,
        jogo__categoria=categoria,
        jogo__tipo_jogo='CHAMPIONSHIP_DUPLAS'
    ).order_by('jogo__rodada', 'jogo__id')

    dados = {}
    controle_rodadas = {}

    for p in participantes:
        jogador = p.jogador
        jogo = p.jogo
        rodada = jogo.rodada

        if jogador.id not in dados:
            dados[jogador.id] = {
                'jogador': jogador,
                'resultados': [],
                'vitorias': 0,
                'derrotas': 0,
                'games_feitos': 0,
                'games_sofridos': 0,
            }

        chave = f'{jogador.id}_{rodada}'

        if chave not in controle_rodadas:
            controle_rodadas[chave] = 0

        if controle_rodadas[chave] >= categoria.max_jogos_por_rodada:
            continue

        controle_rodadas[chave] += 1

        if p.lado == 'A':
            games_feitos = jogo.total_games_lado_a()
            games_sofridos = jogo.total_games_lado_b()
        else:
            games_feitos = jogo.total_games_lado_b()
            games_sofridos = jogo.total_games_lado_a()

        pontos = pontos_championship(
            p.vencedor,
            games_feitos
        )

        dados[jogador.id]['resultados'].append(pontos)
        dados[jogador.id]['games_feitos'] += games_feitos
        dados[jogador.id]['games_sofridos'] += games_sofridos

        if p.vencedor:
            dados[jogador.id]['vitorias'] += 1
        else:
            dados[jogador.id]['derrotas'] += 1

    ranking_final = []

    for item in dados.values():
        resultados = sorted(
            item['resultados'],
            reverse=True
        )

        melhores = resultados[:categoria.melhores_resultados]
        pontos = sum(melhores)

        jogos = item['vitorias'] + item['derrotas']

        aproveitamento = 0

        if jogos > 0:
            aproveitamento = round(
                (item['vitorias'] / jogos) * 100,
                2
            )

        ranking = RankingJogador.objects.create(
            torneio=torneio,
            categoria=categoria,
            jogador=item['jogador'],
            pontos=pontos,
            vitorias=item['vitorias'],
            derrotas=item['derrotas'],
            games_feitos=item['games_feitos'],
            games_sofridos=item['games_sofridos'],
            aproveitamento=aproveitamento
        )

        ranking_final.append(ranking)

    ranking_final.sort(
        key=lambda x: (
            -x.pontos,
            -x.vitorias,
            -x.games_feitos,
            -x.aproveitamento
        )
    )

    posicao = 1

    for r in ranking_final:
        status = 'NORMAL'

        if categoria.categoria == 'A':
            if posicao <= categoria.classificados_finais:
                status = 'CLASSIFICADO'
            elif posicao > (
                categoria.quantidade_jogadores -
                categoria.rebaixados
            ):
                status = 'REBAIXADO'

        elif categoria.categoria == 'B':
            if posicao <= categoria.promovidos:
                status = 'ACESSO'
            elif posicao <= categoria.classificados_finais:
                status = 'CLASSIFICADO'
            elif posicao > (
                categoria.quantidade_jogadores -
                categoria.rebaixados
            ):
                status = 'REBAIXADO'

        elif categoria.categoria == 'C':
            if posicao <= categoria.classificados_finais:
                status = 'CLASSIFICADO'

        r.posicao = posicao
        r.status_ranking = status
        r.save()

        posicao += 1