from django.contrib import admin
from account.models import Member, Queryer, Filter

class QueryerAdmin(admin.ModelAdmin):
    list_display = ('name', 'apicode', 'is_busy', 'do_on_file', 'start_match', 'end_match')
    list_display_link = ('name',)


class MemberAdmin(admin.ModelAdmin):
    def username(self, instance):
        return str(instance.user.username)
    list_display = ('username', 'name', 'mem_type', 'allow_ips')
    list_display_link = ('username',)
    search_fields=['user__username']

class FilterAdmin(admin.ModelAdmin):
	list_display = ('ip_list',)
		

admin.site.register(Member, MemberAdmin)
admin.site.register(Queryer, QueryerAdmin)
admin.site.register(Filter, FilterAdmin)
