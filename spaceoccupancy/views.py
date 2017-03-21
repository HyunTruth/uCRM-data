import pandas as pd
import datetime
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, NotFound
from rest_pandas import PandasSimpleView

from uCRM.models import BillingPlan, Payment, Space, Token, Admin, Company


class OccupancySharedFunctionView(PandasSimpleView):

    def check_permissions(self, request):
        now = timezone.now()
        try:
            user_token = request.META['HTTP_TOKEN']
            current_user_token = Token.objects.filter(token = user_token).values()[0]
        except:
            #403
            raise NotAuthenticated()
        if current_user_token['expiredat'] < now:
            raise NotAuthenticated('Authentication credentials expired.')
        # current_user = Admin.objects.filter(userid= current_user_token['userid']).values()[0]
        return current_user_token


    def get_total_payment_list(self, request):
        current_user = self.check_permissions(request)
        now = datetime.date.today()

        if current_user['type'] == 'staff':
            current_space_size = Space.objects.filter(id=current_user['space_id']).values()[0]['max_desks']
            total_payment_list = pd.DataFrame(list(Payment.objects.filter(space=current_user['space_id']).filter(start_date__lte= now).values()))

        elif current_user['type'] == 'comp':

            # if len(current_user['space_list']) <= 0:
            #     raise NotFound('Your requested space does not exist.')
            #
            requested_space = int(request.query_params['space_id'])
            # is_permitted_space = False
            # for space in current_user['space_list']:
            #     if space['id']== requested_space:
            #         is_permitted_space = True
            # if is_permitted_space is False:
            #     raise PermissionDenied()

            current_space_size = Space.objects.filter(id=requested_space).values()[0]['max_desks']
            total_payment_list = pd.DataFrame(list(Payment.objects.filter(space=request.query_params['space_id']).filter(start_date__lte= now).values()))
        return {'size': current_space_size, 'payment_list': total_payment_list}

    def get_current_active_list(self, request):
        current_user = self.check_permissions(request)
        now = datetime.date.today()

        if current_user['type'] == 'staff':
            current_space_size = Space.objects.filter(id=current_user['space_id']).values()[0]['max_desks']
            total_payment_list = pd.DataFrame(list(Payment.objects.filter(space=current_user['space_id']).filter(start_date__lte= now, end_date__gte=now).values()))
        elif current_user['type'] == 'comp':

            # if len(current_user['space_list']) <= 0:
            #     raise NotFound('Your requested space does not exist.')
            #
            requested_space = int(request.query_params['space_id'])
            # is_permitted_space = False
            # for space in current_user['space_list']:
            #     if space['id']== requested_space:
            #         is_permitted_space = True
            # if is_permitted_space is False:
            #     raise PermissionDenied()

            current_space_size = Space.objects.filter(id=requested_space).values()[0]['max_desks']
            total_payment_list = pd.DataFrame(list(Payment.objects.filter(space=request.query_params['space_id']).filter(start_date__lte= now, end_date__gte=now).values()))
        return {'size': current_space_size, 'payment_list': total_payment_list}

    def get_billing_plan(self,request):
        current_user = self.check_permissions(request)
        now = datetime.date.today()

        if current_user['type'] == 'staff':
            billing_plan = BillingPlan.objects.filter(space_id=current_user['space_id']).values()
        elif current_user['type'] == 'comp':

            # if len(current_user['space_list']) <= 0:
            #     raise NotFound('Your requested space does not exist.')
            #
            requested_space = int(request.query_params['space_id'])
            # is_permitted_space = False
            # for space in current_user['space_list']:
            #     if space['id'] == requested_space:
            #         is_permitted_space = True
            # if is_permitted_space is False:
            #     raise PermissionDenied()

            billing_plan = BillingPlan.objects.filter(space_id=requested_space).values()
        return billing_plan


class BillingPlanOccupancyView(OccupancySharedFunctionView):

    def get(self, request, *args, **kwargs):
        current_occupancy_data = self.get_current_active_list(request)
        total_payment_list = current_occupancy_data['payment_list']
        current_space_size = current_occupancy_data['size']
        now = datetime.date.today()

        # Billing plan id name으로 map해줄 것
        billing_plan = self.get_billing_plan(request)
        billing_plan_mapper = {}

        for plans in billing_plan:
            billing_plan_mapper[plans['id']] = plans['name']
        total_payment_list['bill_plan_id'] = total_payment_list['bill_plan_id'].map(billing_plan_mapper)

        if total_payment_list['bill_plan_id'].isnull().values.sum() > 0:
            raise NotFound('There is some error in space-billing plan association')

        try:
            total_payment_data = total_payment_list.groupby('bill_plan_id').size().astype(float)

            billing_plan_percentage = total_payment_data.apply(lambda x, i = total_payment_data.sum(): x / i * 100)

            total_payment_percentage = total_payment_data.apply(lambda x, i = current_space_size: x / i * 100)

            summary = pd.concat({'OccupyingNumber': total_payment_data, 'BillingPlanOccupancyRate': billing_plan_percentage, 'TotalOccupancyRate': total_payment_percentage}, axis=1)

            #reorders and fills NaNs with 0
            summary = summary[['OccupyingNumber', 'BillingPlanOccupancyRate', 'TotalOccupancyRate']]
            summary.index.names = ['BillingPlan']
            summary.fillna(0, inplace= True)
            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)


class SpaceOccupancyFlowView(OccupancySharedFunctionView):

    def get(self, request, *args, **kwargs):
        now = datetime.date.today()
        try:
            year = request.query_params['year']
        except:
            year = now.year
        occupancy_data = self.get_total_payment_list(request)
        total_payment_list = occupancy_data['payment_list']
        current_space_size = occupancy_data['size']

        try:
            yearly_flow = pd.Series()
            until = 13
            if year == now.year:
                until = now.month + 1
            for i in range(1, until):
                next_month = datetime.date(year, i, 25).replace(day=28) + datetime.timedelta(4)
                target_month = next_month - datetime.timedelta(days=next_month.day)
                counting_condition = (total_payment_list.start_date < target_month) & (target_month < total_payment_list.end_date)
                count = total_payment_list[counting_condition].count().id
                yearly_flow = yearly_flow.set_value(i, count)

            yearlyOccupancyFlow = yearly_flow.apply(lambda x, i = current_space_size: x / i * 100)

            summary = pd.concat({'OccupyingNumber': yearly_flow, 'OccupancyRate': yearlyOccupancyFlow}, axis=1)

            #reorders and fills NaNs with 0
            summary = summary[['OccupyingNumber', 'OccupancyRate']]
            summary.index.names = ['Month']
            summary.fillna(0, inplace= True)
            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)

class WeeklySpaceOccupancyView(OccupancySharedFunctionView):
    def get(self, request, *args, **kwargs):
        occupancy_data = self.get_total_payment_list(request)
        total_payment_list = occupancy_data['payment_list']
        current_space_size = occupancy_data['size']
        now = datetime.date.today()
        try:
            weekly_number_flow = pd.Series()
            for i in range(1, 6):
                targetWeek = now - datetime.timedelta(weeks=5-i)
                counting_condition = (total_payment_list.start_date < targetWeek) & (targetWeek < total_payment_list.end_date)
                count = total_payment_list[counting_condition].count().id
                weekly_number_flow = weekly_number_flow.set_value(i, count)

            weekly_occupancy_flow = weekly_number_flow.apply(lambda x, i = current_space_size: x / i * 100)

            summary = pd.concat({'OccupyingNumber': weekly_number_flow, 'OccupancyRate': weekly_occupancy_flow}, axis=1)

            #reorders and fills NaNs with 0
            summary = summary[['OccupyingNumber', 'OccupancyRate']]
            summary.index.names = ['Weeks']
            summary.fillna(0, inplace= True)
            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)
