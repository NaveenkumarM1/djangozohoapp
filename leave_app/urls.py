from django.urls import path
from . import views

urlpatterns = [
    path('', views.love, name='love'),
    path('hello', views.hello, name='hello'),
    # path('index', views.index, name='index'),
    path('content', views.content, name='content'),

    path('holiday', views.holiday, name='holiday'),
    path('form', views.get_all_form, name='get_all_form'),
    path('find', views.find, name='find'),
    path('getRecordDetail', views.get_record, name='get_record'),
    path('getAllAppliedLeaveList', views.applied_leave_list, name='applied_leave_list'),
    path('leaveBalance', views.employee_leave_balance, name='employee_leave_balance'),
    path('cancelLeave', views.cancle_leave, name='cancle_leave'),
    path('callApi', views.call_api, name='call_api'),
    path('apply', views.apply, name='apply'),
    path('next_holiday', views.next_upcoming_holiday, name='next_upcoming_holiday'),
]