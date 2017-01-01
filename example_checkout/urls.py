from django.conf.urls import url

from example_checkout import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^payments/$', views.payments, name='payments'),
    url(r'^payment_details/$', views.view_payment_details, name='payment_details'),
    url(r'^checkout/subscription/$', views.checkout_subscription, name='checkout_subscription'),
    url(r'^checkout/one-off/$', views.checkout_one_off, name='checkout_one_off'),
    url(r'^checkout/payment/$', views.payment_page, name='payment_page'),
    url(r'^checkout/success/$', views.success_page, name='success_page'),
    url(r'^direct-debit-guarantee/$', views.direct_debit_guarantee, name='dd_guarantee'),
]