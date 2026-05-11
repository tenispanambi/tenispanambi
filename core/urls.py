from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('ranking/', views.ranking, name='ranking'),
    path('jogador/<int:jogador_id>/', views.jogador, name='jogador'),
    path('headtohead/', views.headtohead, name='headtohead'),
path(
    'meu-painel/',
    views.meu_painel,
    name='meu_painel'
),
path(
    'lancar-resultado/<int:jogo_id>/',
    views.lancar_resultado,
    name='lancar_resultado'
),
path(
    'resultados-pendentes/',
    views.resultados_pendentes,
    name='resultados_pendentes'
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
    'torneios/',
    views.torneios,
    name='torneios'
),

path(
    'inscrever/<int:torneio_id>/<int:categoria_id>/',
    views.inscrever_torneio,
    name='inscrever_torneio'
),
path(
    'gerar-torneio/<int:torneio_id>/<int:categoria_id>/',
    views.gerar_torneio,
    name='gerar_torneio'
),
path(
    'chaveamento/<int:torneio_id>/<int:categoria_id>/',
    views.chaveamento,
    name='chaveamento'
),
path(
    'meus-jogos/',
    views.meus_jogos,
    name='meus_jogos'
),
]