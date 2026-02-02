from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Transfer(models.Model):
    month = models.CharField(max_length=7)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Expense(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    month = models.CharField(max_length=7)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Bill(models.Model):
    BILL_TYPES = [("paper", "Paper"), ("app", "App")]
    STATUSES = [("pending", "Pending"), ("paid", "Paid"), ("reimbursed", "Reimbursed")]

    month = models.CharField(max_length=7)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bill_type = models.CharField(max_length=20, choices=BILL_TYPES, default="paper")
    source = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)


class BillImport(models.Model):
    provider = models.CharField(max_length=120)
    account_hint = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=40, default="not_configured")
    last_run = models.DateTimeField(null=True, blank=True)
