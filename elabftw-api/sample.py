from bs4 import BeautifulSoup
import elabapy


def get_exp_text(exp_number, current_endpoint, current_token):
    line_no = 1
    clean_lines = []
    # PLEASE CHANGE THE VERIFY FLAG TO TRUE UPON DEPLOYMENT
    manager = elabapy.Manager(endpoint=current_endpoint, token=current_token, verify=False)
    exp = manager.get_experiment(exp_number)
    soup = BeautifulSoup(exp["body"], features="lxml")
    non_break_space = u'\xa0'
    text = soup.get_text().splitlines()
    lines = [x for x in text if x != '\xa0']  # Remove NBSP if it is on a single list element
    # Replace NBSP with space if it is inside the text
    for line in lines:
        line = line.replace(non_break_space, ' ')
        clean_lines.append(line)
        line_no = line_no + 1
    return clean_lines


token = "db45c9c6db52cdf73256913a57fb4c2cffec602006436a5271193c094cbc29721febfccaf556dae3a3c0"
endpoint = "https://localhost/api/v1/"
exp_no = 1
exp_lines = get_exp_text(1, endpoint, token)
print(exp_lines)
