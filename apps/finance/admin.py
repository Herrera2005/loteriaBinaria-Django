from django.contrib import admin
from .models import Movement, TopUp, VirtualToRealConversion, VirtualTransfer, Wallet, Withdrawal
class FinanceReadOnlyAdminMixin:
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False
    def has_view_permission(self,request,obj=None): return request.user.is_active and request.user.is_staff
@admin.register(Wallet)
class WalletAdmin(FinanceReadOnlyAdminMixin,admin.ModelAdmin): list_display=("user","currency","available_minor","reserved_minor","status","updated_at"); list_filter=("currency","status"); search_fields=("user__username","user__email","user__document")
@admin.register(Movement)
class MovementAdmin(FinanceReadOnlyAdminMixin,admin.ModelAdmin): list_display=("operation_id","wallet","type","direction","amount_minor","balance_after_minor","created_at"); list_filter=("wallet__currency","type","direction")
for model in (TopUp,VirtualToRealConversion,VirtualTransfer,Withdrawal):
    admin.site.register(model,type(f"{model.__name__}Admin",(FinanceReadOnlyAdminMixin,admin.ModelAdmin),{"list_display":("operation_id","user","amount_minor","status","created_at"),"search_fields":("operation_id","user__username","user__email")}))
