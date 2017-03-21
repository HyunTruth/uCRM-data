import pandas as pd
import datetime
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, NotFound
from rest_pandas import PandasSimpleView

from uCRM.models import Room, Reservation, Token


class ReservationSharedFunctionView(PandasSimpleView):

    def check_permissions(self, request):
        now = timezone.now()
        try:
            user_token = request.META['HTTP_TOKEN']
            current_user = Token.objects.filter(token = user_token).values()[0]
        except:
            #403
            raise NotAuthenticated()
        if current_user['expiredat'] < now:
            raise NotAuthenticated('Authentication credentials expired.')
        return current_user

    def get_monthly_reservation(self, request):
        current_user = self.check_permissions(request)
        now = datetime.date.today()
        date_one_month_ago = now - datetime.timedelta(30)

        if current_user['type'] == 'staff':
            space_room_list = Room.objects.filter(space=current_user['space_id']).values()
            room_names = {}
            frames = []
            for room in space_room_list:
                frames.append(pd.DataFrame(list(Reservation.objects.filter(room_id=room['id']).filter(start_time__gte= date_one_month_ago).values())))
                room_names[room['id']] = room['name']

            try:
                total_reservation_list = pd.concat(frames)
            except ValueError:
                raise NotFound('The requested space has insufficient data to report.')

        elif current_user['type'] == 'comp':

            if len(current_user['space_list']) <= 0:
                raise NotFound('Your requested space does not exist.')

            is_permitted_space = False
            requested_space = int(request.query_params['space_id'])

            for space in current_user['space_list']:
                if space['id'] == requested_space:
                    is_permitted_space = True
            if is_permitted_space is False:
                raise PermissionDenied()

            space_room_list = Room.objects.filter(space=requested_space).values()
            room_names = {}
            frames = []
            for room in space_room_list:
                frames.append(pd.DataFrame(list(Reservation.objects.filter(room_id=room['id']).filter(start_time__gte=date_one_month_ago).values())))
                room_names[room['id']] = room['name']

            try:
                total_reservation_list = pd.concat(frames)
            except ValueError:
                raise NotFound('The requested space has insufficient data to report.')
        return {'space_room_list': space_room_list, 'room_name_map': room_names, 'reservation_list': total_reservation_list}

    def get_yearly_reservation(self, request):
        current_user = self.check_permissions(request)
        now = datetime.date.today()
        if current_user['type'] == 'staff':
            space_room_list = Room.objects.filter(space=current_user['space_id']).values()
            room_names = {}
            frames = []
            for room in space_room_list:
                frames.append(pd.DataFrame(list(Reservation.objects.filter(room_id=room['id']).filter(
                    start_time__gte=datetime.date(now.year, 1, 1)).values())))
                room_names[room['id']] = room['name']
            yearly_reservation_list = pd.concat(frames)
        elif current_user['type'] == 'comp':

            if len(current_user['space_list']) <= 0:
                raise NotFound('Your requested space does not exist.')

            is_permitted_space = False
            requested_space = int(request.query_params['space_id'])
            for space in current_user['space_list']:
                if space['id'] == requested_space:
                    is_permitted_space = True

            if is_permitted_space is False:
                raise PermissionDenied()
            space_room_list = Room.objects.filter(space=requested_space).values()
            room_names = {}
            frames = []
            for room in space_room_list:
                frames.append(pd.DataFrame(list(Reservation.objects.filter(room_id=room['id']).filter(
                    start_time__gte=datetime.date(now.year, 1, 1)).values())))
                room_names[room['id']] = room['name']
            try:
                yearly_reservation_list = pd.concat(frames)
            except ValueError:
                NotFound('The requested space has insufficient data to report.')
        return {'space_room_list': space_room_list, 'room_name_map': room_names, 'reservation_list': yearly_reservation_list}


class RoomReservationHourlyView(ReservationSharedFunctionView):
    def get(self, request, *args, **kwargs):
        total_reservation_list = self.get_monthly_reservation(request)['reservation_list']
        try:
            total_reservation_list['start_time'] = pd.DatetimeIndex(total_reservation_list['start_time']).hour
            total_reservation_list['end_time'] = pd.DatetimeIndex(total_reservation_list['end_time']).hour
            hourly_counter = pd.Series()
            for i in range(9, 24):
                counting_condition = (total_reservation_list.start_time < i) & (i < total_reservation_list.end_time)
                count = total_reservation_list[counting_condition].count().id
                hourly_counter = hourly_counter.set_value(i, count)

            summary = pd.concat({'Hourly Usage': hourly_counter}, axis=1)
            #reorders and fills NaNs with 0
            summary = summary[['Hourly Usage']]
            summary.index.names = ['Hour of Day']
            summary.fillna(0, inplace= True)
            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)


class ReservationHourlyByRoomView(ReservationSharedFunctionView):
    def get(self, request, *args, **kwargs):
        total_reservation_data = self.get_monthly_reservation(request)
        total_reservation_list = total_reservation_data['reservation_list']
        room_name_map = total_reservation_data['room_name_map']
        space_room_list = total_reservation_data['space_room_list']

        try:
            total_reservation_list['room_id'] = total_reservation_list['room_id'].map(room_name_map)
            total_reservation_list['start_time'] = pd.DatetimeIndex(total_reservation_list['start_time']).hour
            total_reservation_list['end_time'] = pd.DatetimeIndex(total_reservation_list['end_time']).hour

            room_frames = []
            for room in space_room_list:
                hourly_counter = pd.Series()
                for i in range(9, 24):
                    room_specific_list = total_reservation_list[total_reservation_list.room_id == room['name']]
                    counting_condition = (room_specific_list.start_time < i) & (i < room_specific_list.end_time)
                    count = room_specific_list[counting_condition].count().id
                    hourly_counter = hourly_counter.set_value(i, count)
                if hourly_counter.empty is False:
                    room_frames.append(hourly_counter.rename(room['name']))

            print('hihi', room_frames)
            summary = pd.concat(room_frames, axis=1)
            # reorders and fills NaNs with 0
            summary.index.names = ['Hour of Day']
            summary.fillna(0, inplace=True)
            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)


class ReservationWeekdaysByRoomView(ReservationSharedFunctionView):
    def get(self, request, *args, **kwargs):
        total_reservation_data = self.get_monthly_reservation(request)
        total_reservation_list = total_reservation_data['reservation_list']
        room_name_map = total_reservation_data['room_name_map']
        space_room_list = total_reservation_data['space_room_list']

        try:
            total_reservation_list['room_id'] = total_reservation_list['room_id'].map(room_name_map)
            total_reservation_list['start_time'] = pd.DatetimeIndex(total_reservation_list['start_time']).weekday

            room_frames = []
            for room in space_room_list:
                hourly_counter = pd.Series()
                for i in range(0, 7):
                    room_specific_list = total_reservation_list[total_reservation_list.room_id == room['name']]
                    counting_condition = (room_specific_list.start_time == i)
                    count = room_specific_list[counting_condition].count().id
                    hourly_counter = hourly_counter.set_value(i, count)
                room_frames.append(hourly_counter.rename(room['name']))


            summary = pd.concat(room_frames, axis=1)
            # reorders and fills NaNs with 0
            summary.index.names = ['Day of the Week']
            summary.fillna(0, inplace=True)
            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)


class MonthlyReservationUsageRoomView(ReservationSharedFunctionView):
    def get(self, request, *args, **kwargs):
        total_reservation_data = self.get_yearly_reservation(request)
        total_reservation_list = total_reservation_data['reservation_list']
        room_name_map = total_reservation_data['room_name_map']
        space_room_list = total_reservation_data['space_room_list']

        try:
            total_reservation_list['room_id'] = total_reservation_list['room_id'].map(room_name_map)
            total_reservation_list['start_time'] = pd.DatetimeIndex(total_reservation_list['start_time']).weekday

            room_frames = []
            for room in space_room_list:
                hourly_counter = pd.Series()
                for i in range(0, 7):
                    room_specific_list = total_reservation_list[total_reservation_list.room_id == room['name']]
                    counting_condition = (room_specific_list.start_time == i)
                    count = room_specific_list[counting_condition].count().id
                    hourly_counter = hourly_counter.set_value(i, count)
                room_frames.append(hourly_counter.rename(room['name']))

            summary = pd.concat(room_frames, axis=1)
            # reorders and fills NaNs with 0
            summary.index.names = ['Day of the Week']
            summary.fillna(0, inplace=True)
            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)
