import os
import random
import time
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exchange.settings')
import django

django.setup()

from django.db.transaction import atomic
from django.utils import timezone
from bots.models import BotConfig
from bots.bot import Bot
from cryptocoins.models import AccumulationTransaction

from core.models import Balance, UserWallet, UserFee, UserExchangeFee
from django.contrib.auth import get_user_model
from django.db.models import Q


# todo needs to repair
def main():
    with atomic():
        users = get_user_model().objects.filter(~Q(is_staff=True) & ~Q(username__iregex="^bot[0-9]+@bot.com$")).all()

        wallets = UserWallet.objects.filter(user__in=users)
        AccumulationTransaction.objects.filter(wallet_transaction__wallet__in=wallets.all()).delete()

        BotConfig.objects.filter(user__in=users).delete()
        # MarketTradeRequest.objects.filter(user__in=users).delete()
        UserFee.objects.filter(user__in=users).delete()
        UserExchangeFee.objects.filter(user__in=users).delete()

        for user in users:
            user.delete()

        Balance.objects.update(amount=0, amount_in_orders=0)
        wallets2 = UserWallet.objects.filter(~Q(user__isnull=True) & ~Q(user__username__iregex="^bot[0-9]+@bot.com$"))
        AccumulationTransaction.objects.filter(wallet_transaction__wallet__in=wallets2.all()).delete()
        wallets2.delete()

        # Disable all bot configurations with timestamp
        disable_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        all_bots = BotConfig.objects.filter(enabled=True)
        bot_count = all_bots.count()
        
        print(f'Disabling {bot_count} bot(s) at {disable_timestamp}')
        
        for bot_config in all_bots:
            bot_config.enabled = False
            bot_config.stopped = False  # Keep as False so check_bots task will cancel orders
            bot_config.next_launch = timezone.now()  # Schedule to run immediately
            bot_config.save()
        
        # Cancel all pending orders for disabled bots
        disabled_bots = BotConfig.objects.filter(
            enabled=False,
            stopped=False
        )
        
        for bot_config in disabled_bots:
            try:
                bot = Bot(bot_config=bot_config)
                bot.cancel_all_orders()
                bot_config.stopped = True
                bot_config.save()
                print(f'Cancelled orders for bot: {bot_config.name}')
            except Exception as e:
                print(f'Error cancelling orders for {bot_config.name}: {e}')
        
        print(f'Disabled {bot_count} bot(s) at {disable_timestamp}')


if __name__ == '__main__':
    print('Start')
    main()
    print('Stop')

