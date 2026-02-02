from decimal import Decimal
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Bill, BillImport, Category, Expense, Transfer


def parse_amount(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


@csrf_exempt
def categories(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            category, _created = Category.objects.get_or_create(name=name)
            return JsonResponse({"id": category.id, "name": category.name})
    data = list(Category.objects.order_by("name").values("id", "name"))
    return JsonResponse({"items": data})


@csrf_exempt
def transfers(request):
    if request.method == "POST":
        month = request.POST.get("month", "")
        amount = parse_amount(request.POST.get("amount"))
        note = request.POST.get("note", "")
        if amount is not None and month:
            transfer = Transfer.objects.create(month=month, amount=amount, note=note)
            return JsonResponse({"id": transfer.id})
    queryset = Transfer.objects.order_by("-created_at")
    month = request.GET.get("month")
    if month:
        queryset = queryset.filter(month=month)
    items = list(
        queryset.values("id", "month", "amount", "note", "created_at")
    )
    return JsonResponse({"items": items})


@csrf_exempt
def expenses(request):
    if request.method == "POST":
        month = request.POST.get("month", "")
        amount = parse_amount(request.POST.get("amount"))
        description = request.POST.get("description", "")
        category_id = request.POST.get("category_id")
        if amount is not None and month and category_id:
            expense = Expense.objects.create(
                month=month,
                amount=amount,
                description=description,
                category_id=category_id,
            )
            return JsonResponse({"id": expense.id})
    queryset = Expense.objects.select_related("category").order_by("-created_at")
    month = request.GET.get("month")
    if month:
        queryset = queryset.filter(month=month)
    items = list(
        queryset.values(
            "id",
            "month",
            "amount",
            "description",
            "created_at",
            "category__name",
        )
    )
    return JsonResponse({"items": items})


@csrf_exempt
def bills(request):
    if request.method == "POST":
        month = request.POST.get("month", "")
        amount = parse_amount(request.POST.get("amount"))
        bill_type = request.POST.get("bill_type", "paper")
        source = request.POST.get("source", "")
        status = request.POST.get("status", "pending")
        if amount is not None and month:
            bill = Bill.objects.create(
                month=month,
                amount=amount,
                bill_type=bill_type,
                source=source,
                status=status,
            )
            return JsonResponse({"id": bill.id})
    queryset = Bill.objects.order_by("-created_at")
    month = request.GET.get("month")
    if month:
        queryset = queryset.filter(month=month)
    items = list(
        queryset.values(
            "id",
            "month",
            "amount",
            "bill_type",
            "source",
            "status",
            "created_at",
        )
    )
    return JsonResponse({"items": items})


@csrf_exempt
def imports(request):
    if request.method == "POST":
        provider = request.POST.get("provider", "").strip()
        account_hint = request.POST.get("account_hint", "").strip()
        if provider:
            bill_import = BillImport.objects.create(
                provider=provider,
                account_hint=account_hint,
                status="not_configured",
            )
            return JsonResponse({"id": bill_import.id})
    items = list(
        BillImport.objects.order_by("id").values(
            "id", "provider", "account_hint", "status", "last_run"
        )
    )
    return JsonResponse({"items": items})


@csrf_exempt
def queue_import(request, import_id):
    if request.method == "POST":
        BillImport.objects.filter(id=import_id).update(
            status="queued", last_run=timezone.now()
        )
    return JsonResponse({"queued": True})


def month_summary(request, month):
    transfers_total = (
        Transfer.objects.filter(month=month).aggregate(total=Sum("amount"))["total"]
        or 0
    )
    expenses_total = (
        Expense.objects.filter(month=month).aggregate(total=Sum("amount"))["total"]
        or 0
    )
    bills_total = (
        Bill.objects.filter(month=month).aggregate(total=Sum("amount"))["total"] or 0
    )
    category_totals = (
        Expense.objects.filter(month=month)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    return JsonResponse(
        {
            "month": month,
            "totals": {
                "transfers": str(transfers_total),
                "expenses": str(expenses_total),
                "bills": str(bills_total),
            },
            "categories": [
                {"name": entry["category__name"], "total": str(entry["total"])}
                for entry in category_totals
            ],
        }
    )
