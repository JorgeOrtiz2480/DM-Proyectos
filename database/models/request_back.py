import requests
import json

# URL for the web service
scoring_uri = 'http://ea996b09-ea78-48ad-ba08-ae99c588e7c4.francecentral.azurecontainer.io/score'
# If the service is authenticated, set the key or token
key = 'q121dbGQGuYHULt7CQMRrqRtkczlHPgW'

set1 = [
                5.583037423226975,
                6.257198517101056,
                2.753778089862417,
                3.907518371115759,
                11.824082863274194,
                0.320738149132483,
                4.656318519378988,
                4.18101518633876]
set2 = [
                5.313270987393447,
                7.541981086635956,
                9.702078178995714,
                4.182776584238159,
                9.354004597971354,
                0.407808473556946,
                5.619456740301016,
                4.934506657692589]

# Two sets of data to score, so we get two results back
data = {"data": [ set1,set2]}

# Convert to JSON string
input_data = json.dumps(data)

# Set the content type
headers = {'Content-Type': 'application/json'}
# If authentication is enabled, set the authorization header
headers['Authorization'] = f'Bearer {key}'

# Make the request and display the response
resp = requests.post(scoring_uri, input_data, headers=headers)
print(resp.text)