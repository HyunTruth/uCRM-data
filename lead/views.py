import pandas as pd
import datetime
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, NotFound
from rest_pandas import PandasSimpleView

from uCRM.models import Lead, Token


class LeadSharedFunctionView(PandasSimpleView):
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

    def get_yearly_leads(self, request, year):
        now = datetime.date.today()
        current_user = self.check_permissions(request)
        if current_user['type'] == 'staff':
            if year == now.year:
                total_lead_data = pd.DataFrame(list(Lead.objects.filter(space=current_user['space_id']).filter(date__year= now.year, date__month__lte = now.month).values()))
            else:
                total_lead_data = pd.DataFrame(list(Lead.objects.filter(space=current_user['space_id']).filter(date__year= year).values()))
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
            if year == now.year:
                total_lead_data = pd.DataFrame(list(Lead.objects.filter(space=requested_space).filter(date__year= now.year, date__month__lte= now.month).values()))
            else:
                total_lead_data = pd.DataFrame(list(Lead.objects.filter(space=requested_space).filter(date__year= year).values()))
        return total_lead_data

class LeadDetailView(LeadSharedFunctionView):
    def get(self, request, *args, **kwargs):
        now = datetime.date.today()
        total_lead_data = self.get_yearly_leads(request, now.year)
        try:
            date_30_days_ago = now - datetime.timedelta(30)
            date_60_days_ago = now - datetime.timedelta(60)

            current_month_condition = (date_30_days_ago < total_lead_data.date) & (total_lead_data.date < now)
            last_month_condition = (date_60_days_ago < total_lead_data.date) & (total_lead_data.date < date_30_days_ago)

            current_month = total_lead_data[current_month_condition]
            current_month_conversion = current_month[current_month.conversion == 1]
            last_month = total_lead_data[last_month_condition]
            last_month_conversion = last_month[last_month.conversion == 1]


            current_month_data = current_month.groupby('type').size().astype(float)
            current_month_conversion_data = current_month_conversion.groupby('type').size()
            last_month_data = last_month.groupby('type').size().astype(float)
            last_month_conversion_data = last_month_conversion.groupby('type').size()

            summary = pd.concat({'ThisMonth': current_month_data, 'ThisConversion': current_month_conversion_data, 'LastMonth': last_month_data, 'LastConversion': last_month_conversion_data}, axis=1)
            summary['ThisConversionPercentage'] = summary.apply(lambda row : (row['ThisConversion'] / row['ThisMonth'] * 100), axis = 1)
            summary['LastConversionPercentage'] = summary.apply(lambda row : (row['LastConversion'] / row['LastMonth'] * 100), axis = 1)

            #reorders and fills NaNs with 0
            summary = summary[['ThisMonth', 'ThisConversion', 'ThisConversionPercentage', 'LastMonth', 'LastConversion', 'LastConversionPercentage']]
            summary.index.names = ['Channels']
            summary.fillna(0, inplace= True)
            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)

class LeadYearlyView(LeadSharedFunctionView):
    def get(self, request, *args, **kwargs):
        try:
            year = request.query_params['year']
        except:
            year = datetime.date.today().year

        total_lead_data = self.get_yearly_leads(request, year)
        try:
            conversion = total_lead_data[total_lead_data.conversion == 1]
            lead_data = total_lead_data.groupby(total_lead_data.date.dt.month).size().astype(float)
            conversion_data = conversion.groupby(conversion.date.dt.month).size().astype(float)

            summary = pd.concat({'Leads': lead_data, 'ActualConversion': conversion_data}, axis = 1)
            summary['ConversionPercentage'] = summary.apply(lambda row : (row['ActualConversion'] / row['Leads'] * 100), axis = 1)
            summary.fillna(0, inplace= True)
            summary.index.names = ['Month']
            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)