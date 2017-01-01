from django.shortcuts import render, HttpResponse, redirect
from django.http import HttpResponseNotFound
from django.template import loader, RequestContext
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from .forms import CustomerForm
from .models import Customer, BankAccount, Mandate, Payment, Subscription, CustomerDataInput, CustomerOrder

import requests
import locale

import gocardless_pro

# Set locale and GoCardless client connection.
locale.setlocale(locale.LC_ALL, 'en_GB')

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

@csrf_exempt
def hello(request):
	return HttpResponse('pong')