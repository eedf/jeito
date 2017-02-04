from django.contrib import admin
from .models import BookingState, Booking, BookingItem, TrackingEvent, TrackingValue, Agreement, Payment


@admin.register(BookingState)
class BookingStateAdmin(admin.ModelAdmin):
    list_display = ('title', 'color', 'income')


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'booking')


class BookingItemInline(admin.TabularInline):
    model = BookingItem
    fields = ('product', 'title', 'headcount', 'begin', 'end', 'price_pppn', 'price_pn', 'price_pp', 'price',
              'cotisation')


class PaymentInline(admin.TabularInline):
    model = Payment
    fields = ('mean', 'date', 'amount', 'scan')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    inlines = (BookingItemInline, PaymentInline)
    list_display = ('title', 'state', 'contact', 'email', 'tel', 'agreement')
    list_filter = ('state', )


class TrackingValueInline(admin.TabularInline):
    model = TrackingValue
    fields = ('field', 'value')


@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'obj')
    inlines = (TrackingValueInline, )
