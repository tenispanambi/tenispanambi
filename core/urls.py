from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


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
]