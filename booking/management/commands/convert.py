from django.core.management.base import BaseCommand
from becours.models import Group, Headcount
from booking.models import Booking, BookingItem, BookingState, Payment


def join(a, b):
    return a + (" " if a and b else "") + b


class Command(BaseCommand):
    def handle(self, *args, **options):
        for group in Group.objects.all():
            paye = BookingState.objects.get(title="Payé")
            booking = Booking.objects.create(
                title=group.name,
                contact=join(group.firstname, group.lastname),
                email=group.email,
                tel=group.tel,
                org_type=group.type if group.type < 3 else 5,
                state=paye,
                description=group.comments,
                invoice=group.invoice,
                invoice_number=group.invoice_number,
            )
            for headcount in group.headcounts.all():
                BookingItem.objects.create(
                    booking=booking,
                    headcount=headcount.number,
                    begin=headcount.begin,
                    end=headcount.end,
                    product=headcount.comfort,
                    price_pppn=headcount.cost,
                    cotisation=bool(group.coop_cost),
                )
            if group.additional_cost:
                BookingItem.objects.create(
                    booking=booking,
                    product=3,
                    price=group.additional_cost,
                    cotisation=bool(group.coop_cost),
                )
            Payment.objects.create(
                booking=booking,
                amount=group.cost,
                mean=1,
                date=group.end or '2016-12-31',
            )
