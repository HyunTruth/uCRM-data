# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from __future__ import unicode_literals

from rest_framework import serializers
import uCRM.models as md
from django_mysql.models import JSONField


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Activity
        fields = ('id', 'space', 'type', 'date', 'user')


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Admin
        fields = ('id', 'company', 'name', 'userid', 'password', 'email', 'mobile')


class BillingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.BillingPlan
        fields = ('id', 'space', 'name', 'cost', 'isdaily', 'duration', 'description')


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Company
        fields = ('id', 'name')


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Expense
        fields = ('id', 'space', 'type', 'details', 'payment_date', 'amount', 'payment_method', 'isapproved')


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Lead
        fields = ('id', 'space', 'date', 'email', 'name', 'mobile', 'note', 'type', 'conversion')


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Member
        fields = ('id', 'space', 'isactive', 'name', 'email', 'mobile', 'joined_date', 'end_date', 'end_reason', 'gender')

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Payment
        fields = ('id', 'space', 'member', 'bill_plan', 'scheduled_date', 'start_date', 'end_date', 'payment_method')

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Reservation
        fields = ('id', 'room', 'start_time', 'end_time', 'duration', 'ispaid')

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Room
        fields = ('id', 'space', 'name', 'cost', 'max_size')

class SalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Salary
        fields = ('space', 'staff', 'scheduled_date', 'payment_date', 'amount')

class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Space
        fields = ('id', 'company', 'name', 'address', 'max_desks')


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Staff
        fields = ('id', 'space', 'name', 'userid', 'password', 'email', 'mobile', 'joined_date', 'end_date', 'is_approved')


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.Token
        fields = ('id', 'token', 'userid', 'expiredat', 'type')
