from django.contrib import admin
from .models import ScrapeRequest

# Register your models here.


class ScrapeRequestAdmin(admin.ModelAdmin):
    fields = ('email', 'subject', 'csv_path', 'result_csv_path', 'status', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'status', 'updated_at')
    list_display = ('email', 'subject', 'csv_path', 'current_status', 'created_at', 'updated_at')


    def current_status(self, obj):
        return obj.status == 0 and 'Pending' or 'Delivered'


admin.site.site_header = 'Administration'
admin.site.register(ScrapeRequest, ScrapeRequestAdmin)
