from django.core.management.base import BaseCommand
from example_checkout.models import Customer, BankAccount, Mandate, Payment, Subscription

import gocardless_pro

# Set locale and GoCardless client connection.

client = gocardless_pro.Client(
	access_token='sandbox_IyUsW0Qqwu77LMDNaujtZHEiq4TvvuEslzbk0gWF',
	environment='sandbox'
)

class Command(BaseCommand):
	args = ''

	def get_customers(self):
		customers = client.customers.list(params={"limit": "500"}).records
		for customer in customers:
			customer_record = Customer(
				id=customer.id,
				given_name=customer.given_name,
				family_name=customer.family_name,
				address_line1=customer.address_line1,
				address_line2=customer.address_line2,
				city=customer.city,
				postal_code=customer.postal_code,
				country_code=customer.country_code
			)
			customer_record.save()

	def get_customer_bank_accounts(self):
		customer_bank_accounts = client.customer_bank_accounts.list(params={"limit": "500"}).records
		for customer_bank_account in customer_bank_accounts:
			customer_bank_account_record = BankAccount(
				id=customer_bank_account.id,
				account_number_ending=customer_bank_account.account_number_ending,
				bank_name=customer_bank_account.bank_name,
				account_holder_name=customer_bank_account.account_holder_name,
				country_code=customer_bank_account.country_code,
				linked_customer=Customer.objects.get(pk=customer_bank_account.links.customer)
				)	
			customer_bank_account_record.save()

	def get_mandates(self):
		mandates = client.mandates.list(params={"limit": "500"}).records
		for mandate in mandates:
			mandate_record = Mandate(
				id=mandate.id,
				scheme=mandate.scheme,
				status=mandate.status,
				linked_bank_account=BankAccount.objects.get(pk=mandate.links.customer_bank_account),
				)	
			mandate_record.save()

	def get_payments(self):
		payments = client.payments.list(params={"limit": "500"}).records
		for payment in payments:
			payment_record = Payment(
				id=payment.id,
				amount=payment.amount,
				charge_date=payment.charge_date,
				currency=payment.currency,
				reference=payment.reference,
				status=payment.status,
				linked_mandate=Mandate.objects.get(pk=payment.links.mandate),
			)
			payment_record.save()

	def get_subscriptions(self):
		subscriptions = client.subscriptions.list(params={"limit": "500"}).records
		for subscription in subscriptions:
			subscription_record = Subscription(
				id=subscription.id,
				name=subscription.name,
				amount=subscription.amount,
				currency=subscription.currency,
				day_of_month=subscription.day_of_month,
				end_date=subscription.end_date,
				interval_unit=subscription.interval_unit,
				interval=subscription.interval,
				start_date=subscription.start_date,
				status=subscription.status,
				linked_mandate=Mandate.objects.get(pk=subscription.links.mandate),
			)
			subscription_record.save()

	def handle(self, *args, **options):
		self.get_customers()
		self.get_customer_bank_accounts()
		self.get_mandates()
		self.get_payments()
		self.get_subscriptions()