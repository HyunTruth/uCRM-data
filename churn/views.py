import pandas as pd
import datetime
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, NotFound
from rest_pandas import PandasSimpleView

from uCRM.models import Member, Token


class ChurnedSharedFunctionView(PandasSimpleView):
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

    def get_all_churned(self, request):
        current_user = self.check_permissions(request)
        print(request.query_params)
        if current_user['type'] == 'staff':
            total_churn_data = pd.DataFrame(list(Member.objects.filter(space=current_user['space_id']).filter(end_date__isnull=False)
                                                 .exclude(end_reason__contains='입력오류').values()))
        elif current_user['type'] == 'comp':

            # if len(current_user['space_list']) <= 0:
            #     raise NotFound('Your requested space does not exist.')

            # requested_space = int(request.query_params['space_id'])
            # is_permitted_space = False
            # for space in current_user['space_list']:
            #     if space['id'] == requested_space:
            #         is_permitted_space = True
            # if is_permitted_space is False:
            #     raise PermissionDenied()

            total_churn_data = pd.DataFrame(list(Member.objects.filter(space=request.query_params['space_id']).filter(end_date__isnull=False)
                                                 .exclude(end_reason__contains='입력오류').values()))
        return total_churn_data

    def get_yearly_churned(self, request):
        current_user = self.check_permissions(request)
        now = datetime.date.today()
        if current_user['type'] == 'staff':
            yearly_churn = pd.DataFrame(list(Member.objects.filter(space=current_user['space_id']).filter(end_date__isnull=False)
                                             .filter(end_date__year=now.year).exclude(end_reason__contains='입력오류').values()))
        elif current_user['type'] == 'comp':

            # if len(current_user['space_list']) <= 0:
            #     raise NotFound('Your requested space does not exist.')
            #
            # requested_space = int(request.query_params['space_id'])
            # is_permitted_space = False
            # for space in current_user['space_list']:
            #     if space['id'] == requested_space:
            #         is_permitted_space = True
            #
            # if is_permitted_space is False:
            #     raise PermissionDenied()

            yearly_churn = pd.DataFrame(list(Member.objects.filter(space=request.query_params['space_id']).filter(end_date__isnull=False)
                                             .filter(end_date__year=now.year).exclude(end_reason__contains='입력오류').values()))
        return yearly_churn


class ChurnedComparisonView(ChurnedSharedFunctionView):
    def get(self, request, *args, **kwargs):
        now = datetime.date.today()
        total_churn_data = self.get_all_churned(request)
        try:
            date_one_month_ago = now - datetime.timedelta(30)
            date_two_months_ago = now - datetime.timedelta(60)

            current_month_condition = (date_one_month_ago < total_churn_data.end_date) & (total_churn_data.end_date < now)
            last_month_condition = (date_two_months_ago < total_churn_data.end_date) & (total_churn_data.end_date < date_one_month_ago)

            current_month = total_churn_data[current_month_condition]
            last_month = total_churn_data[last_month_condition]

            current_month_data = current_month.groupby('end_reason').size().astype(float)
            last_month_data = last_month.groupby('end_reason').size()

            current_month_percentage = current_month_data.apply(lambda x, i = current_month_data.sum(): x / i * 100)
            last_month_percentage = last_month_data.apply(lambda x, i = last_month_data.sum(): x / i * 100)

            summary = pd.concat({'ThisMonth': current_month_data,'ThisPercentage': current_month_percentage, 'LastMonth': last_month_data, 'LastPercentage': last_month_percentage}, axis=1)

            #reorders and fills NaNs with 0
            summary = summary[['ThisMonth', 'ThisPercentage','LastMonth', 'LastPercentage']]
            summary.fillna(0, inplace= True)
            summary = summary.reset_index()
        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)

class ChurnedThisMonthView(ChurnedSharedFunctionView):
    def get(self, request, *args, **kwargs):
        now = datetime.date.today()
        total_churn_data = self.get_all_churned(request)
        try:
            date_one_month_ago = now - datetime.timedelta(30)

            current_month_condition = (date_one_month_ago < total_churn_data.end_date) & (total_churn_data.end_date < now)

            current_month = total_churn_data[current_month_condition]

            current_month_data = current_month.groupby('end_reason').size().astype(float)

            current_month_percentage = current_month_data.apply(lambda x, i = current_month_data.sum(): x / i * 100)

            summary = pd.concat({'ThisMonth': current_month_data,'ThisPercentage': current_month_percentage}, axis=1)

            #reorders and fills NaNs with 0
            summary = summary[['ThisMonth', 'ThisPercentage']]
            summary.fillna(0, inplace= True)
            summary.index.names = ['index']
            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)

class ChurnedLastMonthView(ChurnedSharedFunctionView):
    def get(self, request, *args, **kwargs):
        now = datetime.date.today()
        total_churn_data = self.get_all_churned(request)

        try:
            date_one_month_ago = now - datetime.timedelta(30)

            date_two_months_ago = now - datetime.timedelta(60)

            last_month_condition = (date_two_months_ago < total_churn_data.end_date) & (total_churn_data.end_date < date_one_month_ago)

            last_month = total_churn_data[last_month_condition]

            last_month_data = last_month.groupby('end_reason').size()

            last_month_percentage = last_month_data.apply(lambda x, i = last_month_data.sum(): x / i * 100)

            summary = pd.concat({'LastMonth': last_month_data, 'LastPercentage': last_month_percentage}, axis=1)

            #reorders and fills NaNs with 0
            summary = summary[['LastMonth', 'LastPercentage']]
            summary.fillna(0, inplace= True)
            summary.index.names = ['index']
            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)

class ChurnedFlowView(ChurnedSharedFunctionView):
    def get(self, request, *args, **kwargs):
        now = datetime.date.today()
        yearly_churn = self.get_yearly_churned(request)
        try:
            yearly_churn_data = yearly_churn.groupby(yearly_churn.end_date.dt.month).size().astype(float)

            summary = pd.concat({'Churns': yearly_churn_data}, axis=1)
            #
            #reorders and fills NaNs with 0
            summary.index.names = ['Month']
            summary.fillna(0, inplace= True)
            summary = summary.reset_index()
        except:
            raise NotFound('The requested space has insufficient data to report.')
        return Response(summary)