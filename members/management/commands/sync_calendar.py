from datetime import timedelta
import httplib2
import googleapiclient.discovery
from googleapiclient.http import HttpError
from django.core.management.base import BaseCommand
from members.models import Structure
from booking.models import Booking


class Command(BaseCommand):
    help = 'Import members'
    tree = None

    def sync_calendar(self):
        id = 'jeito{}'.format(self.id)
        event = {
            'id': id,
            'summary': self.title,
            'start': {
                'date': self.begin.isoformat(),
            },
            'end': {
                'date': (self.end + timedelta(days=1)).isoformat(),
            },
        }
        try:
            service.events().update(calendarId=calendarId, eventId=id, body=event).execute()
        except HttpError as exception:
            if exception.resp.status == 404:
                service.events().insert(calendarId=calendarId, body=event).execute()
            else:
                raise

    def handle(self, *args, **options):
        http_auth = self.structure.google.authorize(httplib2.Http())
        service = googleapiclient.discovery.build(serviceName='calendar', version='v3', http=http_auth)
        calendarId = 'adn3tuv3dfpd9h0r8g5sfme6i4@group.calendar.google.com'
        for structure in Structure.objects.filter(google__isnull=False):
            remote = service.events().list(calendarId=calendarId)
            remote_ids = set([item.id for item in remote['items']])
            bookings = Booking.objects.filter(structure=structure)
            booking_ids = set(['jeito{}'.format(booking.id) for booking in bookings])
            to_add = booking_ids - remote_ids
            to_remove = remote_ids - booking_ids
            to_update = booking_ids & remote_ids
            print(to_add)
            print(to_remove)
            print(to_update)
