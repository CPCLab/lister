import json
from bs4 import BeautifulSoup

import elabapy
manager = elabapy.Manager(endpoint="https://localhost/api/v1/",
                          token="db45c9c6db52cdf73256913a57fb4c2cffec602006436a5271193c094cbc29721febfccaf556dae3a3c0",
                          verify=False)
# get all experiments
all_exp = manager.get_all_experiments()
# get experiment with id 42
exp = manager.get_experiment(1)
#print(exp["body"])
soup = BeautifulSoup(exp["body"], features="lxml")
nonBreakSpace = u'\xa0'
# soup = soup.replace(nonBreakSpace, ' ')
text = soup.get_text().splitlines()
#text = list(filter('\xa0', text))
stext = [x for x in text if x != '\xa0']
line_no = 1
pline = []
for line in stext:
    line = line.replace(nonBreakSpace, ' ')
    pline.append(line)
    line_no = line_no + 1
print(pline)
#print(soup.get_text())
#print(json.dumps(exp, indent=4, sort_keys=True))

