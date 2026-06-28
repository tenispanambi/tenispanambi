from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.utils import timezone
from io import StringIO


@staff_member_required
def baixar_backup(request):
    buffer = StringIO()

    call_command(
        'dumpdata',
        '--natural-foreign',
        '--natural-primary',
        '--indent',
        '2',
        stdout=buffer
    )

    agora = timezone.localtime().strftime('%Y-%m-%d_%H-%M')
    nome_arquivo = f'backup_tenispanambi_{agora}.json'

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/json'
    )

    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'

    return response