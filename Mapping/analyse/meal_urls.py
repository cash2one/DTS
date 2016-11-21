from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from analyse.meal import MealList, MealUpFile, DeleteMeal
from analyse.meal import ChangeHead, GetHeads, MealSortView

urlpatterns = patterns('',
    url(r'^meal_list/$', login_required(MealList.as_view())),
    url(r'meal_up/$', login_required(MealUpFile.as_view())),
    url(r'delete_meal/$', login_required(DeleteMeal.as_view())),
    url(r'change_head/$', login_required(ChangeHead.as_view())),
    url(r'get_heads/$', login_required(GetHeads.as_view())),
    url(r'sort/$', login_required(MealSortView.as_view())),
)
