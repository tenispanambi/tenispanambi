from django.db import models
from django.contrib.auth.models import User


class Jogador(models.Model):

    CATEGORIAS = [
        ('A', 'Categoria A'),
        ('B', 'Categoria B'),
        ('C', 'Categoria C'),
    ]

    NIVEIS = [
        ('INICIANTE', 'Iniciante'),
        ('INTERMEDIARIO', 'Intermediário'),
        ('AVANCADO', 'Avançado'),
    ]

    MAOS = [
        ('DIREITA', 'Direita'),
        ('ESQUERDA', 'Esquerda'),
    ]

    BACKHANDS = [
        ('UMA_MAO', '1 mão'),
        ('DUAS_MAOS', '2 mãos'),
    ]

    ESTILOS_JOGO = [
        ('OFENSIVO', 'Ofensivo'),
        ('DEFENSIVO', 'Defensivo'),
        ('ALL_COURT', 'All Court'),
        ('SAQUE_VOLEIO', 'Saque e Voleio'),
    ]

    CLUBES = [
        ('TENIS_PANAMBI', 'Tênis Panambi'),
        ('AABB', 'AABB'),
        ('AFUBRA', 'Afubra'),
        ('OUTRO', 'Outro'),
    ]

    usuario = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    nome = models.CharField(max_length=150)

    email = models.EmailField(
        blank=True,
        null=True
    )

    telefone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    cidade = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    categoria = models.CharField(
        max_length=1,
        choices=CATEGORIAS,
        blank=True,
        null=True
    )

    nivel = models.CharField(
        max_length=20,
        choices=NIVEIS,
        default='INICIANTE'
    )

    mao_dominante = models.CharField(
        max_length=20,
        choices=MAOS,
        default='DIREITA'
    )

    raquete = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    instagram = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    foto = models.ImageField(
        upload_to='jogadores/',
        blank=True,
        null=True
    )

    ano_inicio = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Ano que começou a jogar'
    )

    clube = models.CharField(
        max_length=30,
        choices=CLUBES,
        blank=True,
        null=True
    )

    backhand = models.CharField(
        max_length=20,
        choices=BACKHANDS,
        blank=True,
        null=True
    )

    estilo_jogo = models.CharField(
        max_length=30,
        choices=ESTILOS_JOGO,
        blank=True,
        null=True
    )

    jogador_favorito = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    frase_pessoal = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    jogos_historicos = models.IntegerField(default=0)
    vitorias_historicas = models.IntegerField(default=0)
    derrotas_historicas = models.IntegerField(default=0)
    titulos_cd = models.IntegerField(default=0)
    vice_cd = models.IntegerField(default=0)
    semifinal_cd = models.IntegerField(default=0)

    ativo = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nome} - Categoria {self.categoria}'

    class Meta:
        ordering = ['categoria', 'nome']


class Torneio(models.Model):

    TIPOS = [
        ('RANKING', 'Ranking'),
        ('MATA_MATA', 'Mata-mata'),
        ('GRUPOS', 'Grupos'),
        ('AMISTOSO', 'Amistoso'),
        ('TREINO', 'Treino'),
    ]

    DISPUTAS = [
        ('SIMPLES', 'Simples'),
        ('DUPLAS', 'Duplas'),
    ]

    STATUS = [
    ('ABERTO', 'Aberto'),
    ('EM_ANDAMENTO', 'Em andamento'),
    ('FASE_FINAIS', 'Fase finais'),
    ('ENCERRADO', 'Encerrado definitivamente'),
]

    nome = models.CharField(max_length=100)
    edicao = models.IntegerField(default=1)
    ano = models.IntegerField(default=2026)

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
        default='RANKING'
    )

    disputa = models.CharField(
        max_length=20,
        choices=DISPUTAS,
        default='DUPLAS'
    )

    data_inicio = models.DateField(
        blank=True,
        null=True
    )

    data_fim = models.DateField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='ABERTO'
    )

    CONTROLE_LANCAMENTO = [
    ('LIVRE', 'Livre'),
    ('SABADO', 'Somente aos sábados'),
    ('MANUAL', 'Bloqueado manualmente'),
    ]

    controle_lancamento = models.CharField(
        max_length=20,
        choices=CONTROLE_LANCAMENTO,
        default='LIVRE'
    )

    ativo = models.BooleanField(
    default=False
)

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nome} - {self.edicao}ª edição'


class CategoriaTorneio(models.Model):

    CATEGORIAS = [
        ('A', 'Categoria A'),
        ('B', 'Categoria B'),
        ('C', 'Categoria C'),
    ]

    torneio = models.ForeignKey(
        Torneio,
        on_delete=models.CASCADE,
        related_name='categorias'
    )

    categoria = models.CharField(
        max_length=1,
        choices=CATEGORIAS
    )

    quantidade_jogadores = models.IntegerField(default=20)
    classificados_finais = models.IntegerField(default=8)
    promovidos = models.IntegerField(default=0)
    rebaixados = models.IntegerField(default=0)
    melhores_resultados = models.IntegerField(default=10)
    max_jogos_por_rodada = models.IntegerField(default=2)
    rodadas_contabilizadas = models.IntegerField(
    default=10
)

    def __str__(self):
        return f'{self.torneio} - Categoria {self.categoria}'


class InscricaoTorneio(models.Model):

    jogador = models.ForeignKey(
        Jogador,
        on_delete=models.CASCADE
    )

    torneio = models.ForeignKey(
        Torneio,
        on_delete=models.CASCADE
    )

    categoria = models.ForeignKey(
        CategoriaTorneio,
        on_delete=models.CASCADE
    )

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.jogador} - {self.torneio}'


class Jogo(models.Model):

    TIPOS = [
    ('SIMPLES', 'Simples Amistoso'),
    ('AMISTOSO_DUPLAS', 'Duplas Amistoso'),
    ('CHAMPIONSHIP_SIMPLES', 'Championship Simples'),
    ('CHAMPIONSHIP_DUPLAS', 'Championship Duplas'),
]

    STATUS_JOGO = [
        ('PENDENTE', 'Pendente'),
        ('CONFIRMADO', 'Confirmado'),
        ('CONTESTADO', 'Contestado'),
    ]

    FASES = [
        ('OITAVAS', 'Oitavas'),
        ('QUARTAS', 'Quartas'),
        ('SEMI', 'Semi Final'),
        ('FINAL', 'Final'),
    ]

    torneio = models.ForeignKey(
        Torneio,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    categoria = models.ForeignKey(
        CategoriaTorneio,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    tipo_jogo = models.CharField(
        max_length=30,
        choices=TIPOS
    )

    rodada = models.IntegerField(
        blank=True,
        null=True
    )

    fase = models.CharField(
        max_length=20,
        choices=FASES,
        blank=True,
        null=True
    )

    data_jogo = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_JOGO,
        default='PENDENTE'
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    observacoes = models.TextField(
        blank=True,
        null=True
    )

    def total_sets_lado_a(self):
        total = 0

        for s in self.sets.all():
            if s.games_lado_a > s.games_lado_b:
                total += 1

        return total

    def total_sets_lado_b(self):
        total = 0

        for s in self.sets.all():
            if s.games_lado_b > s.games_lado_a:
                total += 1

        return total

    def vencedor_lado(self):
        sets_a = self.total_sets_lado_a()
        sets_b = self.total_sets_lado_b()

        if sets_a > sets_b:
            return 'A'

        if sets_b > sets_a:
            return 'B'

        return None

    def total_games_lado_a(self):
        total = 0

        for s in self.sets.all():
            total += s.games_lado_a

        return total

    def total_games_lado_b(self):
        total = 0

        for s in self.sets.all():
            total += s.games_lado_b

        return total

    def atualizar_participantes(self):
        vencedor = self.vencedor_lado()

        for p in self.participantes.all():

            p.vencedor = p.lado == vencedor

            if p.lado == 'A':
                games_feitos = self.total_games_lado_a()
            else:
                games_feitos = self.total_games_lado_b()

            if p.vencedor:
                p.pontos_ranking = 20 + games_feitos
            else:
                p.pontos_ranking = 5 + games_feitos

            p.save()

    def descricao_confronto(self):
        lado_a = []
        lado_b = []

        for p in self.participantes.all():

            if p.lado == 'A':
                lado_a.append(p.jogador.nome)

            if p.lado == 'B':
                lado_b.append(p.jogador.nome)

        nome_a = ' / '.join(lado_a)
        nome_b = ' / '.join(lado_b)

        return f'{nome_a} x {nome_b}'

    def placar_resumido(self):
        placares = []

        for s in self.sets.all().order_by('numero_set'):

            placar = f'{s.games_lado_a}x{s.games_lado_b}'

            if s.teve_tiebreak:
                placar += f' ({s.tiebreak_lado_a}x{s.tiebreak_lado_b})'

            placares.append(placar)

        return ' / '.join(placares)

    def __str__(self):
        confronto = self.descricao_confronto()

        if confronto.strip() == 'x':
            confronto = 'Sem participantes'

        if self.fase:
            return f'{confronto} - {self.get_fase_display()}'

        if self.rodada:
            return f'{confronto} - Rodada {self.rodada}'

        return confronto


class ParticipanteJogo(models.Model):

    LADOS = [
        ('A', 'Lado A'),
        ('B', 'Lado B'),
    ]

    jogo = models.ForeignKey(
        Jogo,
        on_delete=models.CASCADE,
        related_name='participantes'
    )

    jogador = models.ForeignKey(
        Jogador,
        on_delete=models.CASCADE
    )

    lado = models.CharField(
        max_length=1,
        choices=LADOS
    )

    vencedor = models.BooleanField(default=False)

    pontos_ranking = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.jogador} - {self.jogo}'


class SetJogo(models.Model):

    jogo = models.ForeignKey(
        Jogo,
        on_delete=models.CASCADE,
        related_name='sets'
    )

    numero_set = models.IntegerField()

    games_lado_a = models.IntegerField()
    games_lado_b = models.IntegerField()

    teve_tiebreak = models.BooleanField(default=False)

    tiebreak_lado_a = models.IntegerField(
        blank=True,
        null=True
    )

    tiebreak_lado_b = models.IntegerField(
        blank=True,
        null=True
    )

    def __str__(self):
        placar = f'{self.games_lado_a}x{self.games_lado_b}'

        if self.teve_tiebreak:
            placar += f' ({self.tiebreak_lado_a}x{self.tiebreak_lado_b})'

        return f'Set {self.numero_set} - {placar}'


class RankingJogador(models.Model):

    torneio = models.ForeignKey(
        Torneio,
        on_delete=models.CASCADE
    )

    categoria = models.ForeignKey(
        CategoriaTorneio,
        on_delete=models.CASCADE
    )

    jogador = models.ForeignKey(
        Jogador,
        on_delete=models.CASCADE
    )

    posicao = models.IntegerField(default=0)

    posicao_anterior = models.IntegerField(default=0)

    pontos = models.IntegerField(default=0)

    pontos = models.IntegerField(default=0)
    vitorias = models.IntegerField(default=0)
    derrotas = models.IntegerField(default=0)
    games_feitos = models.IntegerField(default=0)
    games_sofridos = models.IntegerField(default=0)

    aproveitamento = models.FloatField(default=0)

    posicao = models.IntegerField(default=0)

    status_ranking = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

class Meta:
    unique_together = (
            'torneio',
            'categoria',
            'jogador'
        )

    def __str__(self):
        return f'{self.jogador} - {self.pontos} pts'


class CampeaoTorneio(models.Model):

    CATEGORIAS = [
        ('A', 'Categoria A'),
        ('B', 'Categoria B'),
        ('C', 'Categoria C'),
    ]

    categoria = models.CharField(
        max_length=1,
        choices=CATEGORIAS
    )

    edicao = models.IntegerField()

    data_final = models.DateField()

    campeao_1 = models.CharField(
        max_length=100
    )

    campeao_2 = models.CharField(
        max_length=100
    )

    finalista_1 = models.CharField(
        max_length=100
    )

    finalista_2 = models.CharField(
        max_length=100
    )

    placar = models.CharField(
        max_length=50
    )

    observacoes = models.TextField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            'categoria',
            '-edicao'
        ]

    def __str__(self):
        return f'{self.get_categoria_display()} - {self.edicao}ª edição'
    
class Quadra(models.Model):

    nome = models.CharField(max_length=100)

    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome    
    
class ConfiguracaoHorarioQuadra(models.Model):

    DIAS_SEMANA = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    quadra = models.ForeignKey(
    Quadra,
    on_delete=models.CASCADE,
    related_name='horarios',
    null=True,
    blank=True
    )

    dia_semana = models.IntegerField(
        choices=DIAS_SEMANA
    )

    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['quadra', 'dia_semana', 'hora_inicio']
        unique_together = [
            'quadra',
            'dia_semana',
            'hora_inicio',
            'hora_fim'
        ]

    def __str__(self):

        nome_quadra = 'Sem quadra'

        if self.quadra:
            nome_quadra = self.quadra.nome

        return (
            f'{nome_quadra} - '
            f'{self.get_dia_semana_display()} - '
            f'{self.hora_inicio} às {self.hora_fim}'
        )


class ReservaQuadra(models.Model):

    STATUS = [
        ('AGENDADA', 'Agendada'),
        ('CANCELADA', 'Cancelada'),
        ('CHECKIN', 'Check-in realizado'),
        ('NO_SHOW', 'Não compareceu'),
    ]

    data = models.DateField()

    horario = models.ForeignKey(
        ConfiguracaoHorarioQuadra,
        on_delete=models.CASCADE,
        related_name='reservas'
    )

    reservado_por = models.ForeignKey(
        Jogador,
        on_delete=models.CASCADE,
        related_name='reservas_quadra'
    )

    jogadores = models.TextField(
        help_text='Informe quem vai jogar neste horário.'
    )

    observacao = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='AGENDADA'
    )

    checkin_realizado = models.BooleanField(default=False)
    checkin_data_hora = models.DateTimeField(blank=True, null=True)
    checkin_latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    checkin_longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    checkin_distancia_metros = models.FloatField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data', 'horario__hora_inicio']
        unique_together = ['data', 'horario']

    def __str__(self):
        return f'{self.data} - {self.horario} - {self.reservado_por.nome}' 
    
class RegistroTorneio(models.Model):

    TIPO_CHOICES = (
        ('SIMPLES', 'Simples'),
        ('DUPLAS', 'Duplas'),
        ('SIMPLES_DUPLAS', 'Simples e Duplas'),
        ('GERAL', 'Geral'),
    )

    nome = models.CharField(max_length=150)
    edicao = models.CharField(max_length=50, blank=True, null=True)

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='GERAL'
    )

    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)

    local = models.CharField(max_length=150, blank=True, null=True)

    logo = models.ImageField(
        upload_to='historico_torneios/logos/',
        blank=True,
        null=True
    )

    total_inscritos = models.IntegerField(default=0)
    total_jogos = models.IntegerField(default=0)
    total_categorias = models.IntegerField(default=0)

    observacoes = models.TextField(blank=True, null=True)

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Histórico de Torneio'
        verbose_name_plural = 'Histórico de Torneios'
        ordering = ['-data_inicio', '-id']

    def __str__(self):
        return self.nome


class ResultadoTorneio(models.Model):

    torneio = models.ForeignKey(
        RegistroTorneio,
        on_delete=models.CASCADE,
        related_name='resultados'
    )

    categoria = models.CharField(max_length=100)

    campeao = models.CharField(
        max_length=200,
        help_text='Para duplas, informe: Jogador 1 / Jogador 2'
    )

    vice = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Para duplas, informe: Jogador 1 / Jogador 2'
    )

    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Resultado do Torneio'
        verbose_name_plural = 'Resultados dos Torneios'
        ordering = ['ordem', 'categoria']

    def __str__(self):
        return f'{self.torneio.nome} - {self.categoria}'
    
class BannerSite(models.Model):

    PAGINAS = [
        ('HOME', 'Home'),
        ('RANKING', 'Ranking'),
        ('TORNEIOS', 'Torneios'),
        ('QUADRAS', 'Quadras'),
        ('HEADTOHEAD', 'Head to Head'),
    ]

    titulo = models.CharField(max_length=150)

    pagina = models.CharField(
        max_length=30,
        choices=PAGINAS,
        default='HOME'
    )

    imagem_desktop = models.ImageField(
        upload_to='banners/desktop/',
        blank=True,
        null=True
    )

    imagem_mobile = models.ImageField(
        upload_to='banners/mobile/',
        blank=True,
        null=True
    )

    video = models.FileField(
        upload_to='banners/videos/',
        blank=True,
        null=True
    )

    link = models.URLField(
        blank=True,
        null=True
    )

    ativo = models.BooleanField(default=True)

    ordem = models.IntegerField(default=0)

    visualizacoes = models.PositiveIntegerField(default=0)
    cliques = models.PositiveIntegerField(default=0)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['pagina', 'ordem', '-criado_em']
        verbose_name = 'Banner do Site'
        verbose_name_plural = 'Banners do Site'

    def __str__(self):
        return f'{self.titulo} - {self.get_pagina_display()}'
    
class EventoCalendario(models.Model):

    STATUS = [
        ('EM_BREVE', 'Em breve'),
        ('INSCRICOES_ABERTAS', 'Inscrições abertas'),
        ('INSCRICOES_ENCERRADAS', 'Inscrições encerradas'),
        ('EM_ANDAMENTO', 'Em andamento'),
        ('FINALIZADO', 'Finalizado'),
    ]

    TIPOS_EVENTO = [
        ('TORNEIO', 'Torneio'),
        ('CLINICA', 'Clínica'),
        ('CURSO', 'Curso'),
        ('SOCIAL', 'Evento Social'),
        ('FESTIVAL', 'Festival'),
        ('OUTRO', 'Outro'),
    ]

    nome = models.CharField(max_length=150)

    subtitulo = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    mensagem_inscricao = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        default='Fique ligado, as inscrições abrirão em breve.',
        help_text='Mensagem exibida no card de inscrições.'
    )

    tipo_evento = models.CharField(
        max_length=30,
        choices=TIPOS_EVENTO,
        default='TORNEIO'
    )

    descricao = models.TextField(
        blank=True,
        null=True
    )

    categorias = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Ex: Categoria A, Categoria B, Infantil, Feminino'
    )

    local = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    endereco = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    data_inicio = models.DateField()

    data_fim = models.DateField(
        blank=True,
        null=True
    )

    data_abertura_inscricoes = models.DateField(
        blank=True,
        null=True
    )

    data_fechamento_inscricoes = models.DateField(
        blank=True,
        null=True
    )

    plataforma_inscricao = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default='LetzPlay',
        help_text='Ex: LetzPlay'
    )

    logo_plataforma_inscricao = models.ImageField(
        upload_to='eventos_calendario/plataformas/',
        blank=True,
        null=True
    )

    link_inscricao = models.URLField(
        blank=True,
        null=True,
        help_text='Cole aqui o link da inscrição no LetzPlay'
    )

    valor_inscricao = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Ex: R$ 50,00 ou Gratuito'
    )

    limite_vagas = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    banner = models.ImageField(
        upload_to='eventos_calendario/',
        blank=True,
        null=True
    )

    logo = models.ImageField(
        upload_to='eventos_calendario/logos/',
        blank=True,
        null=True
    )

    regulamento = models.FileField(
        upload_to='eventos_calendario/regulamentos/',
        blank=True,
        null=True
    )

    cor_evento = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Ex: azul, verde, laranja'
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS,
        default='EM_BREVE'
    )

    destaque = models.BooleanField(default=False)

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_inicio', 'nome']
        verbose_name = 'Evento do Calendário'
        verbose_name_plural = 'Eventos do Calendário'

    def __str__(self):
        return self.nome