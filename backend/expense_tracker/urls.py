from django.urls import path

from api import views

urlpatterns = [
    path("api/summary/<str:month>/", views.month_summary, name="month-summary"),
    path("api/categories/", views.categories, name="categories"),
    path("api/transfers/", views.transfers, name="transfers"),
    path("api/expenses/", views.expenses, name="expenses"),
    path("api/bills/", views.bills, name="bills"),
    path("api/imports/", views.imports, name="imports"),
    path("api/imports/<int:import_id>/queue/", views.queue_import, name="queue-import"),
]
