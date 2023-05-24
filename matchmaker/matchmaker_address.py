import json
import requests



print('[START] scan')

r = requests.get('https://ifconfig.me')
print('New address: {:s}'.format(r.text))
f = open('matchmaker_address.json', 'w')
f.write(json.dumps({
  'matchmakerAddress': r.text
}, indent = 2))
f.close()
r.close()

print('[END] scan')
