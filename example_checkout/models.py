from django.db import models
from datetime import date

class CustomerDataInput(models.Model):
	id = models.AutoField(primary_key=True)
	email = models.CharField(max_length=100)
	given_name = models.CharField(max_length=40)
	given_name = models.CharField(max_length=40)
	family_name = models.CharField(max_length=40)
	address_line1 = models.CharField(max_length=100)
	address_line2 = models.CharField(max_length=100)
	city = models.CharField(max_length=40)
	postal_code = models.CharField(max_length=10)
	country_code = models.CharField(max_length=2)
	branch_code = models.CharField(max_length=8)
	account_number = models.CharField(max_length=12)

	def __str__(self):
		return str(self.id)

class CustomerOrder(models.Model):
	id = models.AutoField(primary_key=True)
	subscription = models.BooleanField()
	amount = models.CharField(max_length=10)

	def __str__(self):
		return str(self.id)

class Customer(models.Model):
	id = models.CharField(max_length=40, primary_key=True)
	email = models.CharField(max_length=100)
	given_name = models.CharField(max_length=40)
	family_name = models.CharField(max_length=40)
	address_line1 = models.CharField(max_length=100, blank=True, null=True)
	address_line2 = models.CharField(max_length=100, blank=True, null=True)
	city = models.CharField(max_length=40, blank=True, null=True)
	postal_code = models.CharField(max_length=10, blank=True, null=True)
	country_code = models.CharField(max_length=2, blank=True, null=True)

	def __str__(self):
		return self.id

class BankAccount(models.Model):
	linked_customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
	id = models.CharField(max_length=40, primary_key=True)
	branch_code = models.CharField(max_length=12, blank=True, null=True)
	account_number = models.CharField(max_length=8, blank=True, null=True)
	account_number_ending = models.CharField(max_length=5, blank=True, null=True)
	bank_name = models.CharField(max_length=50, blank=True, null=True)
	account_holder_name = models.CharField(max_length=100)
	country_code = models.CharField(max_length=2)

	def __str__(self):
		return self.id

class Mandate(models.Model):
	linked_bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
	id = models.CharField(max_length=40, primary_key=True)
	scheme = models.CharField(max_length=10)
	status = models.CharField(max_length=50, blank=True, null=True)

	def __str__(self):
		return self.id

class Payment(models.Model):
	linked_mandate = models.ForeignKey(Mandate, on_delete=models.CASCADE)
	id = models.CharField(max_length=40, primary_key=True)
	amount = models.IntegerField(default=0)
	charge_date = models.DateField(auto_now=False)
	currency = models.CharField(max_length=3)
	reference = models.CharField(max_length=140, blank=True, null=True)
	status = models.CharField(max_length=50)

	def __str__(self):
		return self.id

class Subscription(models.Model):
	linked_mandate = models.ForeignKey(Mandate, on_delete=models.CASCADE)	
	id = models.CharField(max_length=40, primary_key=True)
	name = models.CharField(max_length=40, blank=True, null=True)
	amount = models.IntegerField(default=0)
	currency = models.CharField(max_length=3)
	day_of_month = models.CharField(max_length=12, blank=True, null=True)
	end_date = models.DateField(blank=True, null=True)
	interval_unit = models.CharField(max_length=40)
	interval = models.IntegerField(default=0)
	start_date = models.CharField(max_length=12)
	status = models.CharField(max_length=40)

	def __str__(self):
		return self.id