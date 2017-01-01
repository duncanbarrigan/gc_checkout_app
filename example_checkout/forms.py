from django import forms

class CustomerForm(forms.Form):
	given_name = forms.CharField(label='Given name', initial='D', widget=forms.TextInput)
	family_name = forms.CharField(label='Family name', initial='Test', widget=forms.TextInput)
	email = forms.EmailField(label='Email', initial='test@test.com', widget=forms.TextInput)
	postal_code = forms.CharField(label='Postal code', initial='EC1V 7LQ', widget=forms.TextInput)
	branch_code = forms.FloatField(label='Sort code', initial='200000', widget=forms.NumberInput)
	account_number = forms.FloatField(label='Account number', initial='55779911', widget=forms.NumberInput)
	# only_authorisation_required = forms.BooleanField(label='More than one person is required to set up a Direct Debit', initial=True, widget=forms.CheckboxInput)