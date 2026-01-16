from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User

from core.currency import Currency
from core.balance_manager import BalanceManager


class TransferByEmailAPITest(APITestCase):

    def setUp(self):
        self.sender = User.objects.create_user(username='alice', email='alice@example.com', password='pass')
        self.recipient = User.objects.create_user(username='bob', email='bob@example.com', password='pass')
        self.client = APIClient()
        self.url = '/api/v1/inouts/internal/transfer/'

    def test_transfer_success(self):
        # give sender some BNB balance
        bnb = Currency.get('BNB')
        BalanceManager.increase_amount(self.sender.id, bnb, 10)

        self.client.login(username='alice', password='pass')
        resp = self.client.post(self.url, data={
            'to_email': 'bob@example.com',
            'currency': 'BNB',
            'amount': '1.5'
        }, format='json')

        self.assertEqual(resp.status_code, 200)
        self.assertIn('withdraw_tx', resp.data)
        self.assertIn('topup_tx', resp.data)

    def test_transfer_insufficient_funds(self):
        bnb = Currency.get('BNB')
        # no balance
        self.client.login(username='alice', password='pass')
        resp = self.client.post(self.url, data={
            'to_email': 'bob@example.com',
            'currency': 'BNB',
            'amount': '1000'
        }, format='json')

        # should return 400 with transfer_failed validation
        self.assertEqual(resp.status_code, 400)
