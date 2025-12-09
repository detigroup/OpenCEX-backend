import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exchange.settings')
import django
django.setup()

from bots.models import BotConfig

print("=== BOT STATUS ===")
bots = BotConfig.objects.all()
for b in bots:
    print(f'{b.name}: enabled={b.enabled}, stopped={b.stopped}, next_launch={b.next_launch}')
    
print(f"\nTotal bots: {bots.count()}")
print(f"Enabled bots: {BotConfig.objects.filter(enabled=True).count()}")
print(f"Disabled bots: {BotConfig.objects.filter(enabled=False).count()}")
