import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voicepilot.settings.development')

app = Celery('voicepilot')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'process-missed-calls-every-15-min': {
        'task': 'tasks.callback_tasks.process_missed_calls_queue',
        'schedule': 900.0,
    },
    'sync-unsynced-calls-hourly': {
        'task': 'tasks.crm_tasks.sync_unsynced_calls',
        'schedule': 3600.0,
    },
    'cleanup-old-recordings-daily': {
        'task': 'tasks.recording_tasks.cleanup_old_recordings',
        'schedule': 86400.0,  # once a day
    },
}
