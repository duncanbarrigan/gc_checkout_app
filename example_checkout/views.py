from django.shortcuts import render, HttpResponse, redirect
from django.http import HttpResponseNotFound
from django.template import loader, RequestContext
from django.contrib import messages
from django.views.generic import View

from .forms import CustomerForm
from .models import Customer, BankAccount, Mandate, Payment, Subscription, CustomerDataInput, CustomerOrder

import requests
import locale

import gocardless_pro

# Webhook handling
import json
import hmac
import hashlib
import os

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Set locale and GoCardless client connection.
# locale.setlocale(locale.LC_ALL, 'en_GB.utf8')

client = gocardless_pro.Client(
	access_token='sandbox_IyUsW0Qqwu77LMDNaujtZHEiq4TvvuEslzbk0gWF',
	environment='sandbox'
)

###########################
###### CORE VIEWS #########
###########################

def index(request):
	template = loader.get_template('example_checkout/index.html')
	return HttpResponse(template.render(request))

def checkout_subscription(request):
	order_record = CustomerOrder(
		subscription=True,
		amount="5000",
		)
	order_record.save()
	return redirect('payment_page')

def checkout_one_off(request):
	order_record = CustomerOrder(
		subscription=False,
		amount="50000",
		)
	order_record.save()
	return redirect('payment_page')

def payment_page(request):

	# Input data
	customer_data = {}
	customer_order = CustomerOrder.objects.latest('id')
	amount = customer_order.amount
	recurring = customer_order.subscription

	# Used to determine what is displayed in the template
	showForm = True
	confirmation = False

	form = CustomerForm(request.POST)

	template = loader.get_template('example_checkout/payment_page.html')

	if request.method == 'POST':
		if 'preview' in request.POST:
			if form.is_valid():

				customer_data = CustomerDataInput(
					email=request.POST.get('email'),
					given_name=request.POST.get('given_name'),
					family_name=request.POST.get('family_name'),
					address_line1="27 Acer Road",
					address_line2="Apt 2",
					city="London",
					postal_code=request.POST.get('postal_code'),
					country_code="GB",
					branch_code=request.POST.get('branch_code'),
					account_number=request.POST.get('account_number'),
					)
				customer_data.save()

				# Remove form and display confirmation
				confirmation = True
				showForm = False

		if 'confirm' in request.POST:

			try:
				bank_account_details_check(CustomerDataInput.objects.latest('id'))
				confirmation = False
				complete_checkout(CustomerDataInput.objects.latest('id'), customer_order)
				return redirect('success_page')

			except:
				confirmation = False
				showForm = True
				messages.warning(request, 'A Direct Debit could not be created against that account. Please check your details and try again.')

	else:
		form = CustomerForm()

	context = { 
		'customer_data':customer_data,
		'showForm':showForm, 
		'confirmation':confirmation, 
		'form':form,
		'amount': int(int(amount)/100),
		'recurring':recurring,
		}
	return HttpResponse(template.render(context, request))

def direct_debit_guarantee(request):
	template = loader.get_template('example_checkout/direct_debit_guarantee.html')
	return HttpResponse(template.render(request))	

def success_page(request):
	template = loader.get_template('example_checkout/success.html')
	return HttpResponse(template.render(request))

def payments(request):
	payments = client.payments.list(params={"limit": "50"}).records
	template = loader.get_template('example_checkout/payments.html')
	context = {'payments': payments}
	return HttpResponse(template.render(context, request))

def view_payment_details(request):
	payments = {}
	if request.method == 'POST':
		paymentId = request.POST.get('ID')
		payments = client.payments.get(str(paymentId))
	template = loader.get_template('example_checkout/payment_details.html')
	context = {'payments': payments}
	return HttpResponse(template.render(context, request))


##################################
####### PAYMENT PAGE FORM ########
##################################

def bank_account_details_check(customer_data):
	bank_details_lookup_response = client.bank_details_lookups.create(params={
		"account_number": customer_data.account_number,
		"branch_code": customer_data.branch_code,
		"country_code": customer_data.country_code,
	})
	return bank_details_lookup_response

def complete_checkout(customer_data, customer_order):
	customer = create_customer(customer_data)
	customer_bank_account = create_customer_bank_account(customer, customer_data) 
	mandate = create_mandate(customer_bank_account)
	if customer_order.subscription == True:
		subscription = create_subscription(mandate)
	else:
		payment = create_payment(mandate)
	return customer, customer_bank_account, mandate

def create_payments(mandate, recurring, amount):
	if recurring == True:
		subscription = create_subscription(mandate)
		return subscription
	else:
		payment = create_payment(mandate)
		return payment 

##################################
## GOCARDLESS RESOURCE CREATION ##
##################################

def create_customer(customer_data):
	customer = client.customers.create(params={
		"email": customer_data.email,
		"given_name": customer_data.given_name,
		"family_name": customer_data.family_name,
		"address_line1": "27 Acer Road",
		"address_line2": "Apt 2",
		"city": "London",
		"postal_code": customer_data.postal_code,
		"country_code": "GB",
		}
	)
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
	return customer 

def create_customer_bank_account(customer, customer_data):
	customer_bank_account = client.customer_bank_accounts.create(params={
		"account_number": customer_data.account_number,
		"branch_code": customer_data.branch_code,
		"account_holder_name": str(customer.given_name) + ' ' + str(customer.family_name),
		"country_code": customer.country_code,
		"links": {
			"customer": customer.id
		}
	})
	customer_bank_account_record = BankAccount(
		id=customer_bank_account.id,
		account_number=customer_data.account_number,
		branch_code=customer_data.branch_code,
		account_holder_name=customer_bank_account.account_holder_name,
		country_code=customer.country_code,
		linked_customer=Customer.objects.get(pk=customer.id)
		)
	customer_bank_account_record.save()
	return customer_bank_account

def create_mandate(customer_bank_account):
	mandate = client.mandates.create(params={
		"scheme": "bacs",
		"links": {
			"customer_bank_account": customer_bank_account.id,
		}
	})
	mandate_record = Mandate(
		id=mandate.id,
		scheme=mandate.scheme,
		linked_bank_account=BankAccount.objects.get(pk=customer_bank_account.id),
		)
	mandate_record.save()
	return mandate

def create_payment(mandate):
	payment = client.payments.create(params={
		"amount": "5000",
		"currency": "GBP",
		"links": {
				"mandate": mandate.id,
		}
	})
	payment_record = Payment(
		id=payment.id,
		amount=payment.amount,
		charge_date=payment.charge_date,
		currency=payment.currency,
		reference=payment.reference,
		status=payment.status,
		linked_mandate=Mandate.objects.get(pk=mandate.id),
	)
	payment_record.save()
	return payment

def create_subscription(mandate):
	subscription = client.subscriptions.create(params={
		"name": "Subscription",
		"amount": "5000",
		"currency": "GBP",
		"interval_unit": "monthly",
		"interval": "1",
		"links": {
				"mandate": mandate.id,
		}
	})
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
		linked_mandate=Mandate.objects.get(pk=mandate.id),
	)
	subscription_record.save()
	return subscription

##########################
#### WEBHOOK HANDLING ####
##########################

class Webhook(View):
	@method_decorator(csrf_exempt)
	def dispatch(self, *args, **kwargs):
		return super(Webhook, self).dispatch(*args, **kwargs)

	def is_valid_signature(self, request):
		# Checks secret on webhook matches the one provided by GoCardless.
		secret = bytes('jUBeqqlm_fHoHRZk7ecrgEjsfl5Y5ZOTwUcUAvys', 'utf-8')
		computed_signature = hmac.new(
			secret, request.body, hashlib.sha256).hexdigest()
		provided_signature = request.META["HTTP_WEBHOOK_SIGNATURE"]
		return hmac.compare_digest(provided_signature, computed_signature)

	def post(self, request, *args, **kwargs):
		if self.is_valid_signature(request):
			response = HttpResponse()
			payload = json.loads(request.body.decode('utf-8'))
			# Webhooks can contain multiple events
			for event in payload['events']:
				self.process(event, response)
			return response
		else:
			return HttpResponse(498)

	def process(self, event, response):
		response.write("Processing event {}\n".format(event['id']))
		if event['resource_type'] == 'mandates':
			return self.process_mandates(event, response)
		if event['resource_type'] == 'payments':
			return self.process_payments(event, response)
		else:
			# Not currently handling subscription, payout or refund webhooks.
			response.write("Don't know how to process an event with resource_type {}\n".format(event['resource_type']))
			return response

	def process_mandates(self, event, response):
		if event['action'] == 'created':
			try:
				# When a mandate has been created outside the app. Won't work unless the customer bank account
				# is already present in the database.
				# TODO: handle changes in customer bank accounts (triggers new CBA and mandate)
				mandate = client.mandates.get(str(event['links']['mandate']))
				mandate_record = Mandate(
					id=mandate.id,
					scheme=mandate.scheme,
					status=mandate.status,
					linked_bank_account=BankAccount.objects.get(pk=customer_bank_account.id),
					)
				mandate_record.save()
				response.write("New mandate {} has been created\n".format(event['links']['mandate']))
			except:
				response.write("Failed to create new mandate record for {}\n".format(event['links']['mandate']))
		try:
			mandate_id = str(event['links']['mandate'])
			mandate_record = Mandate.objects.get(pk=mandate_id)
			mandate_record.status = event['action']
			mandate_record.save()

			# Expected mandate path. Additional actions not required.
			if event['action'] == 'submitted':
				response.write("Mandate {} has been submitted\n".format(event['links']['mandate']))
			elif event['action'] == 'active':
				response.write("Mandate {} has been activated\n".format(event['links']['mandate']))
			
			# Mandate events triggered by banks
			elif event['action'] == 'failed':
				# TODO: Trigger an email to support when this happens, or one directly to the customer
				# to tell them that the mandate failed and they should try again.
				# Best to look at ['details']['cause'] and provide the explanation.
				response.write("Mandate {} has failed\n".format(event['links']['mandate']))
			elif event['action'] == 'expired':
				# Mandates expire if they are not used. 
				# TODO: Trigger an email to the customer or support.
				response.write("Mandate {} has expired\n".format(event['links']['mandate']))
			
			# Mandate events triggered by customer actions
			elif event['action'] == 'cancelled':
				# Depending on the ['details']['cause'] this could be due to the customer cancelling the mandate.
				# This is usually intentional customer payment churn.
				# TODO: Trigger marketing email to the customer.
				response.write("Mandate {} has been cancelled\n".format(event['links']['mandate']))
			elif event['action'] == 'transferred': 
				# Customer uses a bank account transfer process to move DDs to a new account.
				# TODO: Update Customer Bank Account when this happens.
				response.write("Mandate {} has been transferred\n".format(event['links']['mandate']))
			elif event['action'] == 'amended':
				# Customer has amended the name of the bank account holder
				# TODO amend account holder name in database.
				response.write("Mandate {} has been amended\n".format(event['links']['mandate']))		
			else:
				response.write("Don't know how to process an event with resource_type {}\n".format(event['resource_type']))
				return response
		except:
			# Ignoring mandate events relating to restricted mandates as these are not used by this app.
			response.write("Failed to find resource for {} in system\n".format(event['id']))
			return response

	def process_payments(self, event, response):
		if event['action'] == 'created':
			try:
				# Payments are created outside the app by subscriptions.
				# To keep payments up-to-day they must be created here.
				payment = client.payments.get(str(event['links']['payment']))
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
				response.write("New payment {} has been created\n.".format(event['links']['payment']))
			except:
				# If a new customer is created outside the app then webhooks for new payments will fail to process.
				response.write("Failed to create new payment record for {}\n".format(event['links']['payment']))
		else:
			try:
				payment_id = str(event['links']['payment'])
				payment_record = Payment.objects.get(pk=payment_id)
				payment_record.status = event['action']
				payment_record.save()

				# Expected payment path
				if event['action'] == 'submitted':
					response.write("Payment {} has been submitted\n".format(event['links']['payment']))
				elif event['action'] == 'confirmed':
					response.write("Payment {} has been activated\n".format(event['links']['payment']))
				elif event['action'] == 'paid_out':
					# TODO: Build balances functionality and trigger it here.
					response.write("Payment {} has been paid out\n".format(event['links']['payment']))

				# Payment failure path
				elif event['action'] == 'cancelled':
					response.write("Payment {} has been cancelled\n".format(event['links']['payment']))				
				elif event['action'] == 'failed':
					# TODO: Trigger payment retry here. Customer is automatically emailed by GoCardless.
					response.write("Payment {} has failed\n".format(event['links']['payment']))
				elif event['action'] == 'late_failure_settled':
					# TODO: Add trigger to balances reconciliation here.
					response.write("Late failure on payment {} has been settled\n".format(event['links']['payment']))

				# Payment chargeback path
				elif event['action'] == 'charged_back':
					# Could insert custom handling of chargebacks here.
					response.write("Payment {} has been charged back\n".format(event['links']['payment']))
				elif event['action'] == 'chargeback_cancelled':
					response.write("Chargeback on payment {} has been cancelled\n".format(event['links']['payment']))
				elif event['action'] == 'chargeback_settled':
					# TODO: Add trigger to balances reconciliation here.
					response.write("Chargeback on payment {} has been settled\n".format(event['links']['payment']))

			except:
				# Ignoring various events about payments requiring approval (shouldn't happen as not used by app)
				response.write("Failed to find resource for {} in system\n".format(event['id']))
				return response
