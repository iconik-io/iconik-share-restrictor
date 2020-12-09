import requests
import json
import os
from string import Template

app_id = os.environ.get('app_id')
token = os.environ.get('token')
view_id = os.environ.get('view_id')
slack_webhook = os.environ.get('slack_webhook')

headers = {'App-ID':app_id,'Auth-Token':token}

iconik_url = 'https://app.iconik.io/API/'

slack_template = """{
    "attachments": [
        {
            "fallback": "Warning! Restricted asset illegally shared: $item_id",
            "title": "Warning! Restricted asset illegally shared: $item_id",
            "title_link": "$item_url",
            "fields": [
                {
                    "title": "Name",
                    "value": "$fname $lname",
                    "short": false
                },
				{	
					"title": "email",
					"value": "$email",
					"short": false
				}
            ]
        }
    ]
}"""


def run_audit(request):
    input_data = request.get_json()
    if check_validity(input_data):
        if check_metadata(input_data):
            print('Attempting to post to slack')
            user_info = get_user_info(input_data)
            message = Template(slack_template)
            formatted_message = message.safe_substitute(fname=user_info['first_name'],item_url='https://app.iconik.io/asset/' + input_data['data']['object_id'],lname=user_info['last_name'],email=user_info['email'],item_id=input_data['data']['object_id'])
            post_to_slack(formatted_message)		
            if delete_share(input_data):
                print ("all good, deleted share id " + input_data['object_id'] + ' for item ' + input_data['data']['object_id'])
            else:
                print("Problem deleting")
        else:
            print("Metadata didn't have flag, we don't care, exiting")
def check_validity(webhook):
	try:
		if webhook['system_domain_id'] != "73775d86-f6d8-11e7-8ff5-0a580a300418":
			return False
	except:
		return False 
	return True

def check_metadata(webhook):
	r = requests.get(iconik_url + 'metadata/v1/assets/' + webhook['data']['object_id'] + '/views/' + view_id,headers=headers)
	if r.status_code == 200:
		if 'metadata_values' in r.json():
			if 'ShareNo' in r.json()['metadata_values']:
				for value in r.json()['metadata_values']['ShareNo']['field_values']:
					if value['value'] == 'true':
						return True
					else:
						return False
			else:
				print("No metadata field found that we care about, exiting")
				return False
		else:
			print("No values found at all in successful response, exiting")
			return False

def delete_share(webhook):
	print("trying this: " + iconik_url + 'assets/v1/assets/' + webhook['data']['object_id'] + '/shares/' + webhook['object_id'] + '/')
	r = requests.delete(iconik_url + 'assets/v1/assets/' + webhook['data']['object_id'] + '/shares/' + webhook['object_id'] + '/',headers=headers)
	print(webhook['data']['object_id'])
	print(webhook['object_id'])
	if r.status_code == 204:
		print(r.status_code)
		return True
	else:
		print(r.status_code)		
		return False

def get_user_info(webhook):
	r = requests.get(iconik_url + 'users/v1/users/' + webhook['data']['owner_id'] + '/',headers=headers)
	if r.status_code == 200:
		return r.json()

def post_to_slack(message):
	r = requests.post(slack_webhook,headers={'content-type':'application/json'},data=message)
	if r.status_code != 200:
		print("Something went wrong with slack")
