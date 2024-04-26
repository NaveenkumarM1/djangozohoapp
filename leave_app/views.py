from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
# from dotenv import load_dotenv

from django.http import JsonResponse

import requests
from requests.auth import HTTPBasicAuth

from datetime import date, timedelta
import os
import json

# Zoho People API configuration
client_id = '1000.1JTXULJH9LEG69VLJXZAOJM6OL2TMI'
client_secret = '2830160eaf184132a01791268b20514744dbc6c4ce'
refresh_token = '1000.c86141643b4cec6e180e8365b8e63e55.22538d21c65c922ce0df404a1adaf86a'  # This should be the refresh token obtained during the initial authorization


def is_date_between(start_date, end_date, target_date):
    print(start_date, end_date, target_date)
    start_date = datetime.strptime(start_date, '%d-%b-%Y')
    end_date = datetime.strptime(end_date, '%d-%b-%Y')
    target_date = datetime.strptime(target_date, '%d-%b-%Y')

    return start_date <= target_date <= end_date


def check_for_applied_leave_between_date(leaves, start_date, end_date):
    hasLeave = False
    msg = "Good to go"
    # print(start_date, end_date)
    for leave in leaves:
        if 'ApprovalStatus' in leave.keys():

            if (leave['ApprovalStatus'] != 'Pending' or leave['ApprovalStatus'] != 'Approved') or 1:
                isFrom = is_date_between(start_date, end_date, leave['From'])
                isTo = is_date_between(start_date, end_date, leave['To'])
                if isFrom or isTo:
                    hasLeave = True
                    msg = f"{leave['Leavetype']} is applied on {leave['From']} - {leave['To']} "
                    break
    return {"hasLeave": hasLeave, 'msg': msg}


def get_key_from_value(my_dict, target_value):
    for key, value in my_dict.items():
        if value == target_value:
            return key
    return None


leave_type_map = {
    "Sick Leave": "60951000000210065",
    "Earned Leave": "60951000000210069",
    "Compensatory Leave": "60951000001267001",
    "Casual Leave": "60951000000210061"
}

employee_id_to_email_map = {
    "deepak@neelitech.com": "60951000000557059",
    "supriya@neelitech.com": "60951000000340037",
    "bharath@neelitech.com": "60951000000557269",
    "lakshmi@neelitech.com": "60951000000211366"
}

# 60951000000340037
# Zoho People OAuth endpoint
token_url = 'https://accounts.zoho.in/oauth/v2/token'


def refresh_access_token(refresh_token):
    token = os.environ.get("AUTH_TOKEN")
    token_expiry = os.environ.get("AUTH_TOKEN_EXPIRY")

    if token and token_expiry:
        expiry_time = datetime.fromisoformat(token_expiry)
        if datetime.now() < expiry_time:
            print("******************* Reused the token **********************")
            return token

    data = {
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token'
    }

    response = requests.post(token_url, data=data,
                             auth=HTTPBasicAuth(client_id, client_secret))

    if response.status_code == 200:
        print("******************* Generated new token **********************")
        token = response.json().get("access_token")
        expiry_time = datetime.now() + timedelta(seconds=3600)
        os.environ["AUTH_TOKEN"] = token
        os.environ["AUTH_TOKEN_EXPIRY"] = expiry_time.isoformat()

        return response.json().get('access_token')

    else:
        print(
            f"Failed to refresh access token. Status code: {response.status_code}, Response: {response.text}")
        return None


def get_organization_info(auth_token):
    base_url = 'https://people.zoho.com/people/api/'
    endpoint = 'organization/'

    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }

    url = f'{base_url}{endpoint}'

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        organization_info = response.json()
        return organization_info
    else:
        print(
            f'Failed to get organization info. Status code: {response.status_code}, Response: {response.text}')
        return None


def generate_holiday_list_image(holiday_list):
    current_directory = os.path.join(os.getcwd(), 'static', 'images')
    print("Current working directory:", holiday_list)
    # Data for the table (public holidays in Singapore for a sample year)

    # Dimensions
    width, height = 500, 350
    cell_height = height // (len(holiday_list) + 1)  # +1 for header
    cell_width = width // 2

    # Create a new white image
    # Create a transparent image
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))

    d = ImageDraw.Draw(img)

    # Load a font
    font = ImageFont.truetype("arial.ttf", 15)

    # Draw the table header
    d.text((10, 10), "Holiday", fill=(0, 0, 0), font=font)
    d.text((cell_width + 10, 10), "Date", fill=(0, 0, 0), font=font)

    # Draw the table data
    count = 1
    for x in holiday_list:
        y_position = count * cell_height
        count = count + 1
        d.text((10, y_position + 10), x['Name'], fill=(0, 0, 0), font=font)
        d.text((cell_width + 10, y_position + 10), x['Date'], fill=(0, 0, 0), font=font)

    im = os.path.join(os.getcwd(), 'static', 'images', 'bengaluru_holidays.png')
    img.save(im)


def generate_leave_image(leave_list):
    # Dimensions
    width = 500
    cell_height = 25  # +1 for header
    height = cell_height * len(leave_list) + cell_height
    print(height)
    cell_width = width // 4

    # Create a new white image
    # Create a transparent image
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))

    d = ImageDraw.Draw(img)

    # Load a font
    font = ImageFont.truetype("arial.ttf", 15)

    # Draw the table header
    d.text((10, 10), "Leave Type", fill=(0, 0, 0), font=font)
    d.text((cell_width + 10, 10), "Date", fill=(0, 0, 0), font=font)
    d.text(((cell_width * 2) + 10, 10), "Status", fill=(0, 0, 0), font=font)
    d.text(((cell_width * 3) + 10, 10), "ID", fill=(0, 0, 0), font=font)

    # Draw the table data
    count = 1
    for x in leave_list:
        y_position = count * cell_height
        count = count + 1
        d.text((10, y_position + 10), x['Leavetype'], fill=(0, 0, 0), font=font)
        d.text((cell_width + 10, y_position + 10), x['From'], fill=(0, 0, 0), font=font)
        d.text(((cell_width * 2), y_position + 10), x['ApprovalStatus'], fill=(0, 0, 0), font=font)
        d.text(((cell_width * 3) + 10, y_position + 10), x['l_number'], fill=(0, 0, 0), font=font)

    im = os.path.join(os.getcwd(), 'static', 'images', 'leave_status_list.png')
    img.save(im)


def leave_balence(auth_token):
    base_url = 'https://people.zoho.in/people/api/'
    endpoint = 'forms/leave/getRecords'
    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }

    # {searchField:'Employee_ID',searchText:'60951000001223001'}
    # json.dump({'searchField' : "Employee_ID", 'searchText' : '60951000001223001'  })
    # params = {  'searchParams' : "{searchField:'Employee_ID',searchText:'Deepak Chandrashekharaiah NTEMP08'}"}
    params = {
        'searchParams': "{searchField:'Employee_ID',searchText:'Supriya Gurusamy NTEMP022'}"}

    url = f'{base_url}{endpoint}'

    # response = requests.get(url, headers=headers, params=params)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        organization_info = response.json()
        return organization_info
    else:
        print(
            f'Failed to get leave balence info. Status code: {response.status_code}, Response: {response.text}')
        return None


def get_all_employees(auth_token):
    base_url = 'https://people.zoho.in/people/api/'
    endpoint = 'forms/employee/getRecords??'

    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }

    params = {
        'searchColumn': 'EMPLOYEEMAILALIAS',
        'searchValue': 'deepak@neelitech.com'

    }

    url = f'{base_url}{endpoint}'

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        employee_list = response.json()
        return employee_list.get('data', [])
    else:
        print(
            f'Failed to get employee list. Status code: {response.status_code}, Response: {response.text}')
        return None


def featch_record(auth_token, form_link, record_id):
    base_url = f"https://people.zoho.in/people/api/forms/{form_link}/getDataByID?recordId={record_id}"

    endpoint = f''
    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }

    url = f'{base_url}{endpoint}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        form_data = response.json()
        return form_data
    else:
        print(
            f'Failed to get leave balance. Status code: {response.status_code}, Response: {response.text}')
        return None


def find_record_by_attribute(auth_token, form_link, key, value):
    base_url = f"https://people.zoho.in/people/api/forms/{form_link}/getRecords?"

    searchParams = {'searchField': key, 'searchText': value, 'searchOperator': 'Is'}

    # {searchField: 'Employeestatus', searchOperator: 'Is', searchText : 'Active'}
    endpoint = f"searchParams={json.dumps(searchParams)}"

    print(endpoint)
    # endpoint = "searchParams={searchField: 'Employeestatus', searchOperator: 'Is', searchText : 'Active'}"

    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }

    url = f'{base_url}{endpoint}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        form_data = response.json()
        return form_data
    else:
        print(
            f'Failed to get leave balance. Status code: {response.status_code}, Response: {response.text}')
        return None


# ?searchParams={searchField: '<fieldLabelName>', searchOperator: '<operator>', searchText : '<textValue>'}

def get_form(auth_token):
    # Deepak Chandrashekharaiah NTEMP08
    base_url = 'https://people.zoho.in/people/api/forms?'

    #  base_url = 'https://people.zoho.in/people/api/forms/leave/getRecords'

    endpoint = f''

    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }

    url = f'{base_url}{endpoint}'

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        form_data = response.json()
        return form_data
    else:
        print(
            f'Failed to get leave balance. Status code: {response.status_code}, Response: {response.text}')
        return None


def get_holiday_list(auth_token):
    # Deepak Chandrashekharaiah NTEMP08
    base_url = 'https://people.zoho.in/people/api/'

    #  base_url = 'https://people.zoho.in/people/api/forms/leave/getRecords'

    endpoint = f'leave/v2/holidays/get'

    # Get today's date
    today = datetime.today()

    # Get the end of the year
    end_of_year = datetime(today.year, 12, 31)

    # Format the date as '31-Dec-2023'
    formatted_date = today.strftime('%d-%b-%Y')
    params = {
        'upcoming': 'true',
        'from': formatted_date,
        'to': end_of_year.strftime('%d-%b-%Y'),  # You can adjust this end date as needed
        'dateFormat': 'dd-MMM-yyyy',
        'location': 'Singapore'
    }

    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }

    url = f'{base_url}{endpoint}'

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        leave_balance_data = response.json()

        p_data = []
        for value in leave_balance_data['data']:
            # value = leave_balance_data['data'][k]
            date_string = value['Date']

            # Convert the date string to a datetime object
            date_object = datetime.strptime(date_string, '%d-%b-%Y')

            # Get the day of the week (Monday is 0 and Sunday is 6)
            day_of_week = date_object.weekday()

            # Get the name of the day
            day_name = date_object.strftime('%A')
            value['day_name'] = day_name
            value['day_of_week'] = day_of_week

            p_data.append(value)

        return p_data
    else:
        print(
            f'Failed to get leave balance. Status code: {response.status_code}, Response: {response.text}')
        return None


def get_applied_leaves(auth_token, employee_id):
    base_url = 'https://people.zoho.in/people/api/'

    endpoint = f'forms/leave/getRecords'

    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }

    params = {'searchColumn': "EMPLOYEEMAILALIAS", "searchValue": employee_id}

    url = f'{base_url}{endpoint}'

    response = requests.get(url, headers=headers, params=params)
    lcount = 0
    if response.status_code == 200:
        leave_list_data = response.json()

        # print("Love")
        # print(leave_list_data)
        # exit()

        data = []
        time = []
        tempDict = {}
        for applied_leave_item in leave_list_data['response']['result']:
            temp_value = applied_leave_item.values()

            for y in temp_value:
                leave_item = (y[0])
                if leave_item['ApprovalStatus'] == 'Pending' or leave_item['ApprovalStatus'] == 'Approved':
                    leave_item['l_number'] = f"L{lcount}"
                    l_type = leave_item['Leavetype']
                    time.append(leave_item['From'])
                    tempDict[leave_item['From']] = l_type
                    data.append(leave_item)
                    lcount = lcount + 1

        try:

            min_date = min(time, key=lambda x: datetime.strptime(x, '%d-%b-%Y'))

            date_obj = datetime.strptime(min_date, "%d-%b-%Y")

            # Format as "dd Month Day" format
            formatted_date = date_obj.strftime("%d %B %A")
            return {'result': data, 'upcoming_leave': f"Your upcoming  {tempDict[min_date]} is on  {formatted_date} "}
        except:
            return {'result': data, 'upcoming_leave': f"You do not currently have any holiday Planned"}

    else:
        print(
            f'Failed to get leave balance. Status code: {response.status_code}, Response: {response.text}')
        return None


def apply_employee_leave(auth_token, input_date):
    #
    base_url = 'https://people.zoho.in/people/api/'

    endpoint = f'forms/json/leave/insertRecord'

    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }

    employee_email = get_key_from_value(employee_id_to_email_map, input_date['Employee_ID'])

    applied_leaves = get_applied_leaves(auth_token, employee_email)

    leave_status = check_for_applied_leave_between_date(applied_leaves['result'], input_date['From'], input_date['To'])
    leave_bal = get_employee_leave_balance(auth_token, employee_email)
    if (leave_status['hasLeave']):
        return {'error': 1, 'message': leave_status['msg'], 'leave_bal': leave_bal}


    compensatory_leave_count = leave_bal('Compensatory Leave')
    combo = 1
    if (compensatory_leave_count > 1 and combo, 1):

        params = {'inputData': json.dumps(input_date)}

        url = f'{base_url}{endpoint}'

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            applid_leave_data = response.json()
            return applid_leave_data
        else:
            print(
                f'Failed to get leave balance. Status code: {response.status_code}, Response: {response.text}')
            return None
    else:

        params = {'inputData': json.dumps(input_date)}

        url = f'{base_url}{endpoint}'

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            applid_leave_data = response.json()
            return applid_leave_data
        else:
            print(
                f'Failed to get leave balance. Status code: {response.status_code}, Response: {response.text}')
            return None


def cancle_employee_leave(auth_token, record_id):
    #
    base_url = 'https://people.zoho.in/api/v2/'

    endpoint = f'leavetracker/leaves/records/cancel/{record_id}'

    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
    }

    url = f'{base_url}{endpoint}'

    response = requests.patch(url, headers=headers)

    if response.status_code == 200:
        leave_balance_data = response.json()
        return leave_balance_data
    else:
        print(
            f'Failed to get leave balance. Status code: {response.status_code}, Response: {response.text}')
        return None


def get_leave_status(auth_token):
    # Deepak Chandrashekharaiah NTEMP08
    base_url = 'https://people.zoho.in/people/api/'

    endpoint = f'forms/leave/getDataByID'

    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }

    params = {
        'recordId': '60951000001223001'
    }
    url = f'{base_url}{endpoint}'

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        leave_balance_data = response.json()
        return leave_balance_data
    else:
        print(
            f'Failed to get leave balance. Status code: {response.status_code}, Response: {response.text}')
        return None


def get_leave_type(auth_token):
    # Deepak Chandrashekharaiah NTEMP08
    base_url = 'https://people.zoho.in/people/api/'

    endpoint = f'leave/getLeaveTypeDetails'

    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }

    params = {
        'userId': 'deepak@neelitech.com'
    }
    url = f'{base_url}{endpoint}'

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        leave_balance_data = response.json()
        return leave_balance_data
    else:
        print(
            f'Failed to get leave balance. Status code: {response.status_code}, Response: {response.text}')
        return None


def index(request):
    auth_token = refresh_access_token(refresh_token)

    leave_balance = get_applied_leaves(auth_token)
    count = 0
    leave_list = []
    if leave_balance:
        print(f"Leave Balance: {leave_balance}")
        for x in leave_balance['response']['result']:
            valueList = list(x.values())
            leave_list.append(valueList[0][0])
            count = count + 1

    else:
        JsonResponse({'error': "Unable to featch the result"})

    return JsonResponse({"result": leave_list, "count": count})


def love(request):
    print('Request for index page received')
    return render(request, 'leave_app/index.html')


# Get holiday list
def holiday(request):
    auth_token = refresh_access_token(refresh_token)

    holidays = get_holiday_list(auth_token)
    if holidays:
        print(f"Leave Balance: {holidays}")


    else:

        JsonResponse({'error': "Unable to featch the result"})

    json_string = json.dumps({"result": holidays})

    # generate_holiday_list_image(holidays)

    params = {
        'data': json_string
    }
    url = f'https://rangacs.pythonanywhere.com/jsonHoliday/'

    response = requests.get(url, params=params)

    print(params)
    # Specify the file names for successful and error responses
    success_file_name = './static/api_response.json'
    error_file_name = './static/api_error_response.json'

    if response.status_code == 200:
        # Save the successful response to the success file
        with open(success_file_name, 'wb') as success_file:
            success_file.write(response.content)
        print(f'Successful response saved to {success_file_name}')
    else:
        # Save the error response to the error file
        with open(error_file_name, 'wb') as error_file:
            error_file.write(response.content)
        print(f'Error response saved to {error_file_name}')

    return JsonResponse({"result": holidays,
                         'image_url': "https://rangacs.pythonanywhere.com/static/images/table/holiday_list.png"})


def get_employee_leave_balance(auth_token, employee_id):
    # Deepak Chandrashekharaiah NTEMP08
    base_url = 'https://people.zoho.in/people/api/'

    endpoint = f'leave/getLeaveTypeDetails'

    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }

    params = {
        'userId': employee_id
    }
    url = f'{base_url}{endpoint}'

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        leave_balance_data = response.json()
        print("-----------------------")
        print(leave_balance_data)
        print("-----------------------")
        # exit()
        final_leave_count = {}
        for leave in leave_balance_data['response']['result']:
            final_leave_count[leave['Name']] = leave['BalanceCount']

        return final_leave_count
    else:
        print(
            f'Failed to get leave balance. Status code: {response.status_code}, Response: {response.text}')
        return None


def call_api(request):
    params = {
        'data': '%7B%22result%22:[%7B%22isRestrictedHoliday%22:false,%22ShiftName%22:%22%22,%22Remarks%22:%22Kannada%20Rajyotsava%5Cn%22,%22LocationId%22:%2260951000000210006,60951000000312021,%22,%22ShiftId%22:%22%22,%22Id%22:%2260951000001017073%22,%22Date%22:%2201-Nov-2023%22,%22isHalfday%22:false,%22Name%22:%22Kannada%20Rajyotsava%22,%22LocationName%22:%22Bengaluru,Bangalore%22,%22Session%22:0,%22day_name%22:%22Wednesday%22,%22day_of_week%22:2%7D,%7B%22isRestrictedHoliday%22:false,%22ShiftName%22:%22%22,%22Remarks%22:%22Deepavali%5Cn%22,%22LocationId%22:%22%22,%22ShiftId%22:%22%22,%22Id%22:%2260951000001017083%22,%22Date%22:%2213-Nov-2023%22,%22isHalfday%22:false,%22Name%22:%22Deepavali%22,%22LocationName%22:%22%22,%22Session%22:0,%22day_name%22:%22Monday%22,%22day_of_week%22:0%7D,%7B%22isRestrictedHoliday%22:false,%22ShiftName%22:%22%22,%22Remarks%22:%22Christmas%5Cn%22,%22LocationId%22:%22%22,%22ShiftId%22:%22%22,%22Id%22:%2260951000001017093%22,%22Date%22:%2225-Dec-2023%22,%22isHalfday%22:false,%22Name%22:%22Christmas%22,%22LocationName%22:%22%22,%22Session%22:0,%22day_name%22:%22Monday%22,%22day_of_week%22:0%7D]%7D'
    }
    url = f'https://rangacs.pythonanywhere.com/jsonHoliday/'

    response = requests.get(url, params=params)
    # Define the file name and content
    file_name = "example.html"
    file_content = str(response.content)

    # Open the file in write mode ('w')
    # If the file doesn't exist, it will be created. If it does exist, its contents will be overwritten.
    with open(file_name, 'w') as file:
        # Write the content to the file
        file.write(file_content)
        return JsonResponse({"response": ''})


@csrf_exempt
def applied_leave_list(request):
    if request.method == 'GET':
        # json_data = json.loads(request.body.decode('utf-8'))
        employee_id = request.GET.get('employee_id')

        if employee_id is None or employee_id == '':
            return JsonResponse({'error': "Please provie required field employee_id"})
        else:
            auth_token = refresh_access_token(refresh_token)
            data = get_applied_leaves(auth_token, employee_id)

            # return JsonResponse({'error': "Please provie required field employee_id"})

            params = {'data': {json.dumps(data)}}
            url = "https://rangacs.pythonanywhere.com/jsonLeave/"
            response = requests.get(url=url, params=params)

            if response.status_code == 200:
                image_info = response.json()
                data['image_info'] = image_info
                data['image_url'] = 'https://rangacs.pythonanywhere.com/static/images/table/leave_list.png'
                file_name = "example.html"
                file_content = str(response.content)

                with open(file_name, 'w') as file:
                    file.write(file_content)


            else:
                file_name = "example.html"
                file_content = str(response.content)
                with open(file_name, 'w') as file:
                    file.write(file_content)

            return JsonResponse(data)
        # /params
    else:
        return JsonResponse({'error': "Requested method not suported"})


@csrf_exempt
def employee_leave_balance(request):
    employee_id = request.GET.get('employee_id')
    print(employee_id)
    if request.method == 'GET':
        employee_id = request.GET.get('employee_id')

        if employee_id is None or employee_id == '':
            return JsonResponse({'error': "Please provie required field employee_id"})
        else:
            auth_token = refresh_access_token(refresh_token)
            data = get_employee_leave_balance(auth_token, employee_id)
            # return JsonResponse({'error': auth_token})
            return JsonResponse(data)

    else:
        return JsonResponse({'error': "Requested method not suported"})


@csrf_exempt
def apply_leave(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        leave_type = request.POST.get('leave_type')
        leave_from = request.POST.get('from')
        leave_to = request.POST.get('to')

        input_data = {'Employee_ID': employee_id_to_email_map.get(employee_id),
                      'Leavetype': leave_type_map.get(leave_type),
                      'From': leave_from,
                      'To': leave_to}

        print(input_data)
        if not employee_id:
            return JsonResponse({'error': "Please provide required field employee_id"})
        else:
            auth_token = refresh_access_token(refresh_token)
            data = apply_employee_leave(auth_token, input_data)
            return JsonResponse(data)
    else:
        return JsonResponse({'error': "Requested method not supported"})


def cancle_leave_logic(leave_data, id):
    for leave in leave_data:
        if leave["l_number"] == id:
            auth_token = refresh_access_token(refresh_token)
            return cancle_employee_leave(auth_token, leave["Zoho_ID"])


def get_all_form(request):
    # get call form zoho
    auth_token = refresh_access_token(refresh_token)
    restult = get_form(auth_token)
    return JsonResponse({"response": restult})


@csrf_exempt
def cancle_leave(request):
    if request.method == 'GET':

        employee_id = request.GET.get('employee_id')
        leave_id = request.GET.get('leave_id')

        if employee_id is None or employee_id == '':
            return JsonResponse({'error': "Please provie required field record_id"})
        else:
            auth_token = refresh_access_token(refresh_token)
            leaves_applied = get_applied_leaves(auth_token, employee_id)
            response = cancle_leave_logic(leaves_applied['result'], leave_id)
            # data = cancle_employee_leave(auth_token,record_id)
            return JsonResponse({"response": response})
    else:
        return JsonResponse({'error': "Requested method not suported"})


def index(request):
    print('Request for index page received')
    return render(request, 'hello_azure/index.html')


@csrf_exempt
def get_record(request):
    if request.method == 'GET':
        record_type = request.GET.get('record_type')
        record_id = request.GET.get('record_id')
        auth_token = refresh_access_token(refresh_token)
        response = featch_record(auth_token, record_type, record_id)
        return JsonResponse({"response": response})
    else:
        return JsonResponse({'error': "Requested method not supported"})


@csrf_exempt
def find(request):
    if request.method == 'GET':
        record_type = request.GET.get('record_type')
        value = request.GET.get('value')
        key = request.GET.get('key')
        auth_token = refresh_access_token(refresh_token)
        response = find_record_by_attribute(auth_token, record_type, key, value)
        return JsonResponse({"response": response})
    else:
        return JsonResponse({'error': "Requested method not supported"})


@csrf_exempt
def hello(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name is None or name == '':
            print("Request for hello page received with no name or blank name -- redirecting")
            return redirect('index')
        else:
            print("Request for hello page received with name=%s" % name)
            context = {'name': name}
            return render(request, 'hello_azure/hello.html', context)
    else:
        return redirect('index')


def content(request):
    print('Request for index page received')
    return render(request, 'hello_azure/content.html')


def next_upcoming_holiday(request):
    auth_token = refresh_access_token(refresh_token)
    holidays = get_holiday_list(auth_token)
    next_holiday = holidays[0]
    # Convert to datetime object
    date_obj = datetime.strptime(next_holiday['Date'], "%d-%b-%Y")

    # Format as "dd Month Day" format
    formatted_date = date_obj.strftime("%d %B %A")
    next_holiday['Date'] = formatted_date
    return JsonResponse({'holiday': holidays[0]})


def apply(request):
    if request.method == 'POST':
        json_data = json.loads(request.body.decode('utf-8'))
        employee_id = json_data['employee_id']
        leave_type = json_data['leave_type']
        leave_from = json_data['from']
        leave_to = json_data['to']
        hasComboOff = json_data['has_combo_off']
        half_day = False
        number_of_days = json_data.get('number_of_days', None)
        if number_of_days:
            split_parts = number_of_days.split(',')
            half_day = True if len(split_parts) > 1 else False

        print("rty", number_of_days, half_day)
        leave_from = datetime.strptime(
            json_data['from'], "%m/%d/%Y").strftime("%d-%b-%Y")
        leave_to = datetime.strptime(
            json_data['to'], "%m/%d/%Y").strftime("%d-%b-%Y")
        date_from = datetime.strptime(leave_from, '%d-%b-%Y')
        date_to = datetime.strptime(leave_to, '%d-%b-%Y')

        if (half_day):
            session = split_parts[1].split(' ')
            input_data = {'Employee_ID': employee_id_to_email_map[employee_id],
                          'Leavetype': leave_type_map[leave_type],
                          'From': leave_from,
                          'To': leave_to,
                          "days": {
                              leave_from: {
                                  "LeaveCount": 0.5,
                                  "Session": session[1]
                              }
                          }
                          }

            print(input_data)
            auth_token = refresh_access_token(refresh_token)
            response = apply_half_day_leave(auth_token, input_data=input_data)
            return JsonResponse(response)

        if date_to < date_from:
            return JsonResponse({'error': "1", 'message': f"Start date {leave_from} grater than End Date{leave_to}"})

        input_data = {'Employee_ID': employee_id_to_email_map[employee_id],
                      'Leavetype': leave_type_map[leave_type],
                      'From': leave_from,
                      'To': leave_to}

        employee_email = employee_id

        auth_token = refresh_access_token(refresh_token)

        if employee_id is None or employee_id == '':
            return JsonResponse({'error': "Please provie required field employee_id"})
        else:
            if hasComboOff == '0':
                response = apply_simple_leave(
                    auth_token, input_data=input_data)
                return JsonResponse(response)
            else:

                applied_leaves = get_applied_leaves(auth_token, employee_email)

                leave_status = check_for_applied_leave_between_date(
                    applied_leaves['result'], input_data['From'], input_data['To'])

                if not (leave_status['hasLeave']):
                    response = apply_leave(auth_token, input_data)
                    return JsonResponse(response)
                return JsonResponse({'error': '1', 'message': leave_status['message']})

    else:
        return JsonResponse({'error': "Requested method not suported"})

def apply_half_day_leave(auth_token, input_data):

    base_url = 'https://people.zoho.in/people/api/'
    endpoint = f'forms/json/leave/insertRecord'
    headers = {
        'Authorization': f'Zoho-oauthtoken {auth_token}',
        'Content-Type': 'application/json'
    }
    params = {'inputData': json.dumps(input_data)}

    url = f'{base_url}{endpoint}'

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        leave_response = response.json()

        if leave_response['response']['status'] == 1:

            return {'error': "1", "message":leave_response['errors']['message']['From']}
        else:
            return {'error': "0", "message": leave_response['response']['result']['message']}
    else:
        print(
            f'Failed to apply leave. Status code: {response.status_code}, Response: {response.text}')
        return {"err": json.loads(response.text)}
