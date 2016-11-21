from django.contrib import admin
from analyse.models import SourceFile, MappingedFile, ReportFile
from analyse.models import ThirdMappedFile, Meal, MealHead
from analyse.models import MealSort, Interface
from analyse.models import Coder


class SourceFileAdmin(admin.ModelAdmin):
    pass


class MappingedFileAdmin(admin.ModelAdmin):
    pass


class ReportFileAdmin(admin.ModelAdmin):
    pass


class ThirdMappedFileAdmin(admin.ModelAdmin):
    pass


class MealAdmin(admin.ModelAdmin):
    list_display = ('name', 'chinese_name', 'max_map')
    list_display_link = ('chinese_name',)


class MealHeadAdmin(admin.ModelAdmin):
    pass


class MealSortAdmin(admin.ModelAdmin):
    pass


class CoderAdmin(admin.ModelAdmin):
    list_display = ('code','is_outdate','to_user','permission')
    list_display_link = ('code',)


class InterfaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'chinese_name', 'thread_num', 'max_map')
    list_display_link = ('name',)


admin.site.register(Interface, InterfaceAdmin)
admin.site.register(SourceFile, SourceFileAdmin)
admin.site.register(MappingedFile, MappingedFileAdmin)
admin.site.register(ReportFile, ReportFileAdmin)
admin.site.register(ThirdMappedFile, ThirdMappedFileAdmin)
admin.site.register(Meal, MealAdmin)
admin.site.register(MealHead, MealHeadAdmin)
admin.site.register(MealSort, MealSortAdmin)
admin.site.register(Coder, CoderAdmin)
