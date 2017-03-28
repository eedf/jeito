import httplib2
import googleapiclient.discovery
from django.core.management.base import BaseCommand
from members.models import Structure


class Command(BaseCommand):
    help = 'Sync google calendar'

    def handle(self, *args, **options):
        structure = Structure.objects.get(name='BECOURS')
        bookings = structure.booking_set.filter(state__income__in=(1, 2, 3), begin__isnull=False, end__isnull=False)
        local = {booking.google_id: booking.google_repr for booking in bookings}
        calendarId = 'adn3tuv3dfpd9h0r8g5sfme6i4@group.calendar.google.com'
        http_auth = structure.google.authorize(httplib2.Http())
        service = googleapiclient.discovery.build(serviceName='calendar', version='v3', http=http_auth)
        events = service.events()
        self.stdout.write('Get first page')
        page = events.list(calendarId=calendarId).execute()
        remote = {item['id']: item for item in page['items']}
        while 'nextPageToken' in page:
            self.stdout.write('Get next page')
            page = events.list(calendarId=calendarId, nextPageToken=page['nextPageToken']).execute()
            remote.update({event.id: event for event in page['items']})
        batch = service.new_batch_http_request()
        for id, event in remote.items():
            if id not in local.keys():
                self.stdout.write('Delete {}'.format(id))
                batch.add(events.delete(calendarId=calendarId, eventId=id))
        for id, event in local.items():
            if id not in remote.keys():
                self.stdout.write('Insert {}'.format(id))
                batch.add(events.insert(calendarId=calendarId, body=event))
            else:
                self.stdout.write('Update {}'.format(id))
                batch.add(events.update(calendarId=calendarId, eventId=id, body=event))
        batch.execute()
