import pandas as pd
import datetime
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, NotFound
from rest_pandas import PandasSimpleView

from uCRM.models import Payment, Expense, BillingPlan, Token


class RevenuesSharedFunctionView(PandasSimpleView):

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

    def get_month_data(self, request, year = datetime.date.today().year, month = datetime.date.today().month):
        current_user = self.check_permissions(request)

        #reservation to be accounted for
        if current_user['type'] == 'staff':
            total_revenues_list = pd.DataFrame(list(Payment.objects.filter(space=current_user['space_id'])
                                                    .filter(start_date__year= year, start_date__month__lte= month, end_date__month__gt= month).values()))
            total_expense_list = pd.DataFrame(list(Expense.objects.filter(space=current_user['space_id']).filter(payment_date__year=year, payment_date__month= month)
                                                   .filter(isapproved=1).values()))
        elif current_user['type'] == 'comp':

            # if len(current_user['space_list']) <= 0:
            #     raise NotFound('Your requested space does not exist.')
            #
            # requested_space = int(request.query_params['space_id'])
            # is_permitted_space = False
            # for space in current_user['space_list']:
            #     if space['id']== requested_space:
            #         is_permitted_space = True
            # if is_permitted_space is False:
            #     raise PermissionDenied()

            total_revenues_list = pd.DataFrame(list(Payment.objects.filter(space=request.query_params['space_id'])
                                                    .filter(start_date__year= year, start_date__month__lte= month, end_date__month__gt= month).values()))
            total_expense_list = pd.DataFrame(list(Expense.objects.filter(space=request.query_params['space_id']).filter(payment_date__year=year, payment_date__month= month)
                                                   .filter(isapproved=1).values()))
        return {'revenues': total_revenues_list, 'expense': total_expense_list}

    def process_balance_data(self, request, data):
        revenues = data['revenues']
        expense = data['expense']
        if len(revenues) > 0:
            bill_mappers = self.get_mapper_billing_plan(request)
            plan_cost_mapper = bill_mappers['cost']
            plan_name_mapper = bill_mappers['name']
            revenues['count'] = 1
            revenues['cost'] = revenues['bill_plan_id'].map(plan_cost_mapper)
            revenues['bill_plan_id'] = revenues['bill_plan_id'].map(plan_name_mapper)
        return {'revenues': revenues, 'expense': expense}

    def get_year_data(self, request, year = datetime.date.today().year):
        monthly_revenues = []
        monthly_expenses = []
        for month in range(1, 13):
            balance = self.get_month_data(request, year, month)
            if len(balance['revenues']) > 0:
                monthly_revenues.append(balance['revenues'])
            if len(balance['expense']) > 0:
                monthly_expenses.append(balance['expense'])
        try:
            total_revenues_list = pd.concat(monthly_revenues)
        except ValueError:
            total_revenues_list = pd.DataFrame()
        try:
            total_expense_list = pd.concat(monthly_expenses)
        except ValueError:
            total_expense_list = pd.DataFrame()
        return {'revenues': total_revenues_list, 'expense': total_expense_list}

    def get_monthly_sum(self, request, year, month):
        month_data = self.get_month_data(request, year, month)
        month_processed = self.process_balance_data(request, month_data)
        try:
            sum_cost = month_processed['revenues']['cost'].sum()
        except:
            sum_cost = 0
        try:
            sum_expense = month_processed['expense']['amount'].sum()
        except:
            sum_expense = 0
        sum_balance = sum_cost - sum_expense

        return {'revenues': sum_cost, 'expense': sum_expense, 'balance': sum_balance}

    def get_flow_monthly_sums(self, request, year):
        sums_flow = pd.DataFrame(columns=list(['revenues', 'expense', 'balance']))
        now = datetime.date.today()
        until = 13
        if year == now.year:
            until = now.month + 1
        for month in range(1, until):
            monthly_sum = self.get_monthly_sum(request, year, month)
            sums_flow.loc[month] = [monthly_sum['revenues'], monthly_sum['expense'], monthly_sum['balance']]
        return sums_flow

    def get_monthly_comparison(self, request, year, month):
        compared_sums = pd.DataFrame(columns=list(['revenues', 'expense', 'balance']))
        last_month_sum = self.get_monthly_sum(request, year, month-1)
        compared_sums.loc['지난달'] = [last_month_sum['revenues'], last_month_sum['expense'], last_month_sum['balance']]
        this_month_sum = self.get_monthly_sum(request, year, month)
        compared_sums.loc['이번달'] = [this_month_sum['revenues'], this_month_sum['expense'], this_month_sum['balance']]

        return compared_sums

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

    def get_mapper_billing_plan(self,request):
        space_bill_plan = self.get_billing_plan(request)
        plan_cost_mapper = {}
        plan_name_mapper = {}
        for plans in space_bill_plan:
            plan_cost_mapper[plans['id']] = plans['cost']
            plan_name_mapper[plans['id']] = plans['name']
        return {'cost': plan_cost_mapper, 'name': plan_name_mapper}


class RevenuesBillingPlanMonthView(RevenuesSharedFunctionView):
    def get(self, request, *args, **kwargs):
        try:
            year = request.query_params['year']
        except:
            year = datetime.date.today().year
        try:
            month = request.query_params['month']
        except:
            month = datetime.date.today().month
        this_month_data = self.get_month_data(request, year, month)
        this_month_balance = self.process_balance_data(request, this_month_data)
        this_month_revenues = this_month_balance['revenues']
        this_month_expense = this_month_balance['expense']
        summary = this_month_revenues.drop(this_month_revenues.columns[[1,2,3,4,5,6,7]], axis=1).groupby('bill_plan_id').sum()
        try:
            try:
                sum_expense = this_month_expense['amount'].sum()
            except:
                sum_expense = 0
            num_members = summary['count'].sum()
            summary['real_cost'] = summary['cost'] - summary['count'] * (sum_expense / num_members)
            summary['cost_per_member'] = summary['real_cost'] / summary['count']
            sum_real_cost = summary['real_cost'].sum()
            summary['real_cost_percentage'] = summary['real_cost'] / sum_real_cost * 100
            #reorders and fills NaNs with 0
            summary.append(summary.sum(numeric_only=True), ignore_index=True)
            # summary = summary.round(0)
            summary.index.names = ['BillingPlan']
            summary = summary[['count', 'cost', 'real_cost', 'real_cost_percentage', 'cost_per_member']]

            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)

class RevenuesBillingPlanYearView(RevenuesSharedFunctionView):
    def get(self, request, *args, **kwargs):
        try:
            year = request.query_params['year']
        except:
            year = datetime.date.today().year

        this_year_data = self.get_year_data(request, year)
        this_year_processed = self.process_balance_data(request, this_year_data)
        this_year_revenues = this_year_processed['revenues']
        this_year_expense = this_year_processed['expense']
        try:
            summary = this_year_revenues.drop(this_year_revenues.columns[[1, 2, 3, 4, 5, 6, 7]], axis=1).groupby(
                'bill_plan_id').sum()
            try:
                sum_expense = this_year_expense['amount'].sum()
            except:
                sum_expense = 0
            num_members = summary['count'].sum()
            summary['real_cost'] = summary['cost'] - summary['count'] * (sum_expense / num_members)
            summary['cost_per_member'] = summary['real_cost'] / summary['count']
            sum_real_cost = summary['real_cost'].sum()
            summary['real_cost_percentage'] = summary['real_cost'] / sum_real_cost * 100
            #reorders and fills NaNs with 0
            summary.append(summary.sum(numeric_only=True), ignore_index=True)
            # summary = summary.round(0)
            summary.index.names = ['BillingPlan']
            summary = summary[['count', 'cost', 'real_cost', 'real_cost_percentage', 'cost_per_member']]

            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)


class RevenuesFlowYearView(RevenuesSharedFunctionView):
    def get(self, request, *args, **kwargs):
        try:
            year = request.query_params['year']
        except:
            year = datetime.date.today().year

        print(year)
        summary = self.get_flow_monthly_sums(request, year)
        try:
            summary.index.names = ['Month']
            summary = summary[['revenues', 'expense', 'balance']]

            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)

class RevenuesFlowMonthView(RevenuesSharedFunctionView):
    def get(self, request, *args, **kwargs):
        try:
            year = request.query_params['year']
        except:
            year = datetime.date.today().year
        try:
            month = request.query_params['month']
        except:
            month = datetime.date.today().month

        summary = self.get_monthly_comparison(request, year, month)
        try:
            summary.index.names = ['Month']
            summary = summary[['revenues', 'expense', 'balance']]

            summary = summary.reset_index()

        except:
            raise NotFound('The requested space has insufficient data to report.')

        return Response(summary)