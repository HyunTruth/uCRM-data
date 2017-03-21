# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from __future__ import unicode_literals

from django.db import models

from django_mysql.models import JSONField


class Activity(models.Model):
    space = models.ForeignKey('Space', on_delete=models.CASCADE)
    type = models.CharField(max_length=20)
    date = models.DateTimeField()
    user = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'activity'


class Admin(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=45)
    userid = models.CharField(max_length=45)
    password = models.CharField(max_length=64)
    email = models.CharField(max_length=254)
    mobile = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'admin'
        unique_together = (('name', 'userid', 'email', 'mobile'),)


class BillingPlan(models.Model):
    space = models.ForeignKey('Space', on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    cost = models.IntegerField()
    isdaily = models.IntegerField()
    duration = models.IntegerField()
    description = models.CharField(max_length=254, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'billingplan'


class Company(models.Model):
    name = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'company'
        unique_together = (('id', 'name'),)


class Expense(models.Model):
    space = models.ForeignKey('Space', on_delete=models.CASCADE)
    type = models.CharField(max_length=13)
    details = models.CharField(max_length= 64, blank=True, null=True)
    payment_date = models.DateTimeField()
    amount = models.IntegerField()
    payment_method = models.CharField(max_length=7)
    isapproved= models.IntegerField()

    class Meta:
        managed = False
        db_table = 'expense'


class Lead(models.Model):
    space = models.ForeignKey('Space', on_delete=models.CASCADE)
    date = models.DateTimeField()
    email = models.CharField(max_length=254)
    name = models.CharField(max_length=45, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    note = models.CharField(max_length=45, blank=True, null=True)
    type = models.CharField(max_length=5)
    conversion = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'lead'


class Member(models.Model):
    space = models.ForeignKey('Space', on_delete=models.CASCADE)
    isactive = models.IntegerField()
    name = models.CharField(max_length=45)
    email = models.CharField(max_length=254)
    mobile = models.CharField(max_length=20)
    joined_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    end_reason = models.CharField(max_length=40, blank=True, null=True)
    gender = models.CharField(max_length=1)

    class Meta:
        managed = False
        db_table = 'member'
        unique_together = (('id', 'email', 'mobile'),)


class Payment(models.Model):
    space = models.ForeignKey('Space', on_delete=models.CASCADE)
    member = models.ForeignKey('Member', on_delete=models.CASCADE)
    bill_plan = models.ForeignKey('Billingplan', on_delete=models.CASCADE)
    scheduled_date = models.IntegerField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    payment_method = models.CharField(max_length=7)

    class Meta:
        managed = False
        db_table = 'payment'


class Reservation(models.Model):
    room = models.ForeignKey('Room', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.IntegerField()
    ispaid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'reservation'


class Room(models.Model):
    space = models.ForeignKey('Space', on_delete=models.CASCADE)
    max_size = models.IntegerField()
    cost = models.IntegerField()
    name = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'room'


class Salary(models.Model):
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE)
    space = models.ForeignKey('Space', on_delete=models.CASCADE)
    scheduled_date = models.IntegerField()
    payment_date = models.DateTimeField()
    amount = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'salary'


class Space(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=45)
    address = models.CharField(max_length=254)
    max_desks = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'space'
        unique_together = (('name'),)


class Staff(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    name = models.CharField(max_length=45)
    userid = models.CharField(max_length=45)
    password = models.CharField(max_length=64)
    email = models.CharField(max_length=254)
    mobile = models.CharField(max_length=20)
    joined_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    is_approved = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'staff'
        unique_together = (('id', 'name', 'userid', 'email', 'mobile'),)


class Token(models.Model):
    token = models.CharField(max_length=254)
    userid = models.CharField(max_length=45)
    expiredat = models.DateTimeField()
    type = models.CharField(max_length=5)

    class Meta:
        managed = False
        db_table = 'token'
        unique_together = (('token'),)
