from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

from core.views_backup import baixar_backup


urlpatterns = [

    path(
        '',
        views.home,
        name='home'
    ),

    path(
         'lancar-jogo/',
         views.lancar_jogo,
        name='lancar_jogo'
    ),

    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),

    path(
        'password_change/',
        auth_views.PasswordChangeView.as_view(
            template_name='registration/password_change.html',
            success_url='/meu-painel/'
        ),
        name='password_change'
    ),

    path(
        'cadastro/',
        views.cadastro,
        name='cadastro'
    ),

    path(
        'ranking/',
        views.ranking,
        name='ranking'
    ),

    path(
        'head-to-head/',
        views.headtohead,
        name='headtohead'
    ),

    path(
        'meu-painel/',
        views.meu_painel,
        name='meu_painel'
    ),

    path(
        'meus-jogos/',
        views.meus_jogos,
        name='meus_jogos'
    ),

    path(
        'meu-perfil/',
        views.meu_perfil,
        name='meu_perfil'
    ),

    path(
        'resultados-pendentes/',
        views.resultados_pendentes,
        name='resultados_pendentes'
    ),

    path(
        'torneios/',
        views.torneios,
        name='torneios'
    ),

    path(
        'jogador/<int:jogador_id>/',
        views.jogador,
        name='jogador'
    ),

    path(
        'lancar-resultado/<int:jogo_id>/',
        views.lancar_resultado,
        name='lancar_resultado'
    ),

    path(
        'confirmar-resultado/<int:jogo_id>/',
        views.confirmar_resultado,
        name='confirmar_resultado'
    ),

    path(
        'contestar-resultado/<int:jogo_id>/',
        views.contestar_resultado,
        name='contestar_resultado'
    ),

    path(
        'inscrever/<int:torneio_id>/<int:categoria_id>/',
        views.inscrever_torneio,
        name='inscrever_torneio'
    ),

    path(
        'gerar-chaveamento/<int:torneio_id>/<int:categoria_id>/',
        views.gerar_torneio,
        name='gerar_torneio'
    ),

    path(
        'chaveamento/<int:torneio_id>/<int:categoria_id>/',
        views.chaveamento,
        name='chaveamento'
    ),

    path(
         'mural-campeoes/',
         views.mural_campeoes,
         name='mural_campeoes'
    ),

    path(
    'confirmar-resultado-usuario/<int:jogo_id>/',
    views.confirmar_resultado_usuario,
    name='confirmar_resultado_usuario'
),

    path('quadras/', views.quadras, name='quadras'),
    path('quadras/reservar/<int:horario_id>/', views.reservar_quadra, name='reservar_quadra'),
    path('quadras/cancelar/<int:reserva_id>/', views.cancelar_reserva_quadra, name='cancelar_reserva_quadra'),

    path(
    'gerar-horarios-quadra/',
    views.gerar_horarios_quadra,
    name='gerar_horarios_quadra'
),

path(
    'quadras/checkin/<int:reserva_id>/',
    views.checkin_quadra,
    name='checkin_quadra'
),

path(
    'quadras/relatorio/',
    views.relatorio_quadras,
    name='relatorio_quadras'
),

path(
    'torneios/<int:torneio_id>/',
    views.detalhe_torneio,
    name='detalhe_torneio'
),

path(
    'torneios-historico/',
    views.torneios_historico,
    name='torneios_historico'
),

path(
    'torneios-historico/<int:torneio_id>/',
    views.detalhe_torneio_historico,
    name='detalhe_torneio_historico'
),

path(
    'calendario/',
    views.calendario,
    name='calendario'
),

path(
    'estatisticas-championship/',
    views.estatisticas_championship,
    name='estatisticas_championship'
),

path(
    'champ-duplas/selos/',
    views.selos_championship,
    name='selos_championship'
),

path('backup/download/', baixar_backup, name='baixar_backup'),

path('sistema/', views.painel_sistema, name='painel_sistema'),

]