import json
import re
from enum import Enum
import xlsxwriter
from docx import Document

latin_alphabets= "([A-Za-z])"
openers = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
abbr = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
pref = "(Mr|St|Mrs|Ms|Dr)[.]"
sites = "[.](com|net|org|io|gov|de|eu)"
suff = "(Inc|Ltd|Jr|Sr|Co)"
def split_into_sentences(content):
    content = " " + content + "  "
    content = content.replace("\n", " ")
    content = re.sub(pref, "\\1<prd>", content)
    content = re.sub(sites, "<prd>\\1", content)
    content = re.sub("\s" + latin_alphabets + "[.] ", " \\1<prd> ", content)
    content = re.sub(abbr + " " + openers, "\\1<stop> \\2", content)
    content = re.sub(latin_alphabets + "[.]" + latin_alphabets + "[.]" + latin_alphabets
                     + "[.]", "\\1<prd>\\2<prd>\\3<prd>", content)
    content = re.sub(latin_alphabets + "[.]" + latin_alphabets + "[.]", "\\1<prd>\\2<prd>", content)
    content = re.sub(" " + suff + "[.] " + openers, " \\1<stop> \\2", content)
    content = re.sub(" " + suff + "[.]", " \\1<prd>", content)
    content = re.sub(" " + latin_alphabets + "[.]", " \\1<prd>", content)
    if "”" in content: content = content.replace(".”", "”.")
    if "\"" in content: content = content.replace(".\"", "\".")
    if "!" in content: content = content.replace("!\"", "\"!")
    if "?" in content: content = content.replace("?\"", "\"?")
    content = content.replace(".", ".<stop>")
    content = content.replace("?", "?<stop>")
    content = content.replace("!", "!<stop>")
    content = content.replace("<prd>", ".")
    sentences = content.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

def write_to_json(list, log, filename):
    log_filename = filename[:-5] + ".log"
    json.dump(list, open(filename, 'w', encoding="utf-8"), ensure_ascii=False)
    write_log(log, log_filename)

def write_log(log, filename):
    with open(filename, 'w', encoding="utf-8") as f:
        f.write(log)

def get_docx_content(filename):
    f = open(filename, 'rb')
    content = Document(f)
    f.close()
    return content

# parse opened document, first draft of sop
def parse_docx1_content(doc_content):
    par_no = 0
    key_val = []
    for para in doc_content.paragraphs:
        sentences = split_into_sentences(para.text)
        for sentence in sentences:
            key = ""
            key = str(re.findall('\[.*?\]', sentence))              # get keys
            key = ''.join(key[3:-3])                                # remove unnecessary brackets/hyphens
            lst_values = re.findall('\{.*?\}', sentence)            # get lst_values
            lst_values = [value[1:-1] for value in lst_values]      # remove the curly brackets
            str_values = str(lst_values)                            # convert list to string
            str_values = re.sub(r'[\'][\"]*', '', str_values)       # remove superfluous apostrophe and quotation marks
            str_values = str_values[1:-1]
            if key != "" and str_values != "" :                     # only add when none of the key or value is empty
                one_key_val = [par_no, key, str_values]
                key_val.append(one_key_val)
        par_no = par_no + 1                                         # count paragraph index, starting from 1 and iterate
    return key_val

def extract_kv(kv):
    kv = kv[1:-1]
    kv_split = re.split("\|", kv)
    key = kv_split[1]
    key = key.strip()
    val = kv_split[0]
    val = val.strip()
    return key, val

class Ctrl_metadata(Enum):
    STEP_TYPE = "step type"
    FLOW_TYPE = "flow type"
    FLOW_PARAM = "flow parameter"
    FLOW_LGCL_OPRTR = "flow logical parameter"
    FLOW_CMPRD_VAL = "flow compared value"
    FLOW_RANGE = "flow range"
    FLOW_OPRTN = "flow operation"
    FLOW_MGNTD = "flow magnitude"
    FLOW_SECTION = "section"
    FLOW_ITRTN_STRT = "start iteration value"
    FLOW_ITRTN_END = "end iteration value"


# class Regex_validation(Enum):
# #     UNCLOSED_RANGE =
# #     UNOPENED_RANGE =
# #     UNCLOSED_COMMENT =
# #     UNOPENED_COMMENT =
# #     UNCLOSED_FLOW =
# #     UNOPENED_FLOW =
# #     UNCLOSED_KVPAIR =
# #     UNOPENED_KVPAIR =

class Bracket_pair_validation(Enum):
    IMPROPER_COMMENT_BRACKET = "Mismatch between '(' and ')'. Check line "
    IMPROPER_RANGE_BRACKET = "Mismatch between '[' and ']'.  Check line "
    IMPROPER_KV_BRACKET = "Mismatch between '{' and '}'.  Check line "
    IMPROPER_FLOW_BRACKET = "Mismatch between '<' and '>'.  Check line "

class Argno_validation(Enum):
    IMPROPER_ARGNO_IF = "Number of arguments in the IF statement is wrong."
    IMPROPER_ARGNO_ELSEIF  = "Number of arguments in the ELSE IF statement is wrong."
    IMPROPER_ARGNO_ELSE = "Number of arguments in the ELSE statement is wrong."
    IMPROPER_ARGNO_WHILE = "Number of arguments in the WHILE statement is wrong."
    IMPROPER_ARGNO_FOR = "Number of arguments in the FOR statement is wrong."
    IMPROPER_ARGNO_FOREACH = "Number of arguments in the FOREACH statement is wrong."

def process_foreach(par_no, cf_split):
    key_val = []
    step_type = "iteration"
    key_val.append([par_no, Ctrl_metadata.STEP_TYPE.value, step_type])
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type])
    flow_param = cf_split[1]
    key_val.append([par_no, Ctrl_metadata.FLOW_PARAM.value, flow_param])
    return key_val

def process_while(par_no, cf_split):
    key_val = []
    step_type = "iteration"
    key_val.append([par_no, Ctrl_metadata.STEP_TYPE.value, step_type])
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type])
    flow_param = cf_split[1]
    key_val.append([par_no, Ctrl_metadata.FLOW_PARAM.value, flow_param])
    flow_logical_operator = cf_split[2]
    key_val.append([par_no, Ctrl_metadata.FLOW_LGCL_OPRTR.value, flow_logical_operator])
    flow_compared_value = cf_split[3]
    key_val.append([par_no, Ctrl_metadata.FLOW_CMPRD_VAL.value, flow_compared_value])
    return key_val

def process_if(par_no, cf_split):
    key_val = []
    step_type = "conditional"
    key_val.append([par_no, Ctrl_metadata.STEP_TYPE.value, step_type])
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type])
    flow_param = cf_split[1]
    key_val.append([par_no, Ctrl_metadata.FLOW_PARAM.value, flow_param])
    flow_logical_operator = cf_split[2]
    key_val.append([par_no, Ctrl_metadata.FLOW_LGCL_OPRTR.value, flow_logical_operator])
    flow_compared_value = cf_split[3]
    key_val.append([par_no, Ctrl_metadata.FLOW_CMPRD_VAL.value, flow_compared_value])
    return key_val

def process_elseif(par_no, cf_split):
    key_val = []
    step_type = "conditional"
    key_val.append([par_no, Ctrl_metadata.STEP_TYPE.value, step_type])
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type])
    flow_param = cf_split[1]
    key_val.append([par_no, Ctrl_metadata.FLOW_PARAM.value, flow_param])
    flow_logical_operator = cf_split[2]
    key_val.append([par_no, Ctrl_metadata.FLOW_LGCL_OPRTR.value, flow_logical_operator])
    flow_compared_value = cf_split[3]
    if re.search("\[.*?\]",flow_compared_value):
        key_val.append([par_no, Ctrl_metadata.FLOW_RANGE.value, flow_compared_value])
        start, end = process_range(flow_compared_value)
        key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_STRT.value, start])
        key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_END.value, end])
    else:
        key_val.append([par_no, Ctrl_metadata.FLOW_CMPRD_VAL.value, flow_compared_value])
    return key_val

def process_else(par_no, cf_split):
    key_val = []
    step_type = "conditional"
    key_val.append([par_no, Ctrl_metadata.STEP_TYPE.value, step_type])
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type])
    return key_val

def process_for(par_no, cf_split):
    key_val = []
    step_type = "iteration"
    key_val.append([par_no, Ctrl_metadata.STEP_TYPE.value, step_type])
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type])
    flow_param = cf_split[1]
    key_val.append([par_no, Ctrl_metadata.FLOW_PARAM.value, flow_param])
    flow_range = cf_split[2]
    key_val.append([par_no, Ctrl_metadata.FLOW_RANGE.value, flow_range])
    start, end = process_range(flow_range)
    key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_STRT.value, start])
    key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_END.value, end])
    flow_operation = cf_split[3]
    key_val.append([par_no, Ctrl_metadata.FLOW_OPRTN.value, flow_operation])
    flow_magnitude = cf_split[4]
    key_val.append([par_no, Ctrl_metadata.FLOW_MGNTD.value, flow_magnitude])
    return key_val

# should happen only after having 'while' iterations to provide additional steps on the iterator
def process_others(par_no, cf_split):
    key_val = []
    flow_operation = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_OPRTN.value, flow_operation])
    flow_magnitude = cf_split[1]
    key_val.append([par_no, Ctrl_metadata.FLOW_MGNTD.value, flow_magnitude])
    return key_val

def process_comment(str_with_brackets):
    comment_regex = "\(.+?\)"
    comment = re.search(comment_regex, str_with_brackets)
    comment = comment.group(0)
    remains = str_with_brackets.replace(comment,'')
    comment = comment[1:-1]
    return remains.strip(), comment.strip()

def process_range(flow_range):
    range_values = re.split("-", flow_range[1:-1])
    return float(range_values[0]), float(range_values[1])

def process_section(cf_split):
    key_val = []
    key_val.append(["-",Ctrl_metadata.FLOW_SECTION.value, cf_split[1]])
    return key_val

def check_bracket_num(par_no, text):
    log = "No bracketing error was found on par no %s." % (par_no)
    base_error_warning = "BRACKETING ERROR: %s %s: %s"
    is_error = False
    if text.count("{") != text.count("}"):
        is_error = True
        log = base_error_warning % (Bracket_pair_validation.IMPROPER_KV_BRACKET.value, str(par_no), text)
    if text.count("<") != text.count(">"):
        is_error = True
        log = base_error_warning % (Bracket_pair_validation.IMPROPER_FLOW_BRACKET.value, str(par_no), text)
    if text.count("[") != text.count("]"):
        is_error = True
        log = base_error_warning % (Bracket_pair_validation.IMPROPER_RANGE_BRACKET.value, str(par_no), text)
    if text.count("(") != text.count(")"):
        is_error = True
        log = base_error_warning % (Bracket_pair_validation.IMPROPER_COMMENT_BRACKET.value, str(par_no), text)
    # print(log)
    return log, is_error


def extract_flow_type(par_no, flow_control_pair):
    key_val = []
    cf = flow_control_pair[1:-1]
    cf_split = re.split("\|", cf)
    flow_type = cf_split[0]
    flow_type = flow_type.strip()
    if flow_type == "for each":
        key_val = process_foreach(par_no, cf_split)
    elif flow_type == "while":
        key_val = process_while(par_no, cf_split)
    elif flow_type == "if":
        key_val = process_if(par_no, cf_split)
    elif flow_type == "else if":
        key_val = process_elseif(par_no, cf_split)
    elif flow_type == "else":
        key_val = process_else(par_no, cf_split)
    elif flow_type == "for":
        key_val = process_for(par_no, cf_split)
    # elif flow_type == "+":
    elif flow_type.casefold() == "section".casefold():
        key_val = process_section(cf_split)
    else:
       key_val = process_others(par_no, cf_split)
    return key_val


# parse opened document, second draft of sop
def parse_docx2_content(doc_content):
    par_no = 0
    key_val = []
    comment_regex = "\(.+?\)"                                      # define regex for parsing comment
    log = ""
    for para in doc_content.paragraphs:
        flow_control_pairs = re.findall("<.+?>", para.text)
        # check para.text bracket balance
        bracketnum_log, is_bracket_error = check_bracket_num(par_no, para.text)
        log = log + bracketnum_log + "\n"
        if is_bracket_error:
            break
        if len(flow_control_pairs)>0:
            for flow_control_pair in flow_control_pairs:
                flow_metadata = extract_flow_type(par_no, flow_control_pair)
                key_val.extend(flow_metadata)
        kvs = re.findall(r'\{.+?\}', para.text)                     # get values and keys
        if len(kvs)>0:
            for kv in kvs:
                key, val = extract_kv(kv)
                if key != "" and val != "":
                    if re.search(comment_regex, key):
                        key, comment = process_comment(key)
                    if re.search(comment_regex, val):
                        val, comment = process_comment(val)
                    #NOTE: comment from key or value is available but not yet serialized into files. TBD.
                    one_key_val = [par_no, key, val]
                    key_val.append(one_key_val)
        par_no = par_no + 1                                         # count paragraph index, starting from 1 and iterate
    print(log)
    return key_val, log

def write_to_xlsx(key_val, log, xlsx_filename):
    header = ["STEP NUMBER","KEY","VALUE"]
    log_filename = xlsx_filename[:-5] + ".log"
    with xlsxwriter.Workbook(xlsx_filename) as workbook:
        worksheet = workbook.add_worksheet()
        worksheet.write_row(0, 0, header)
        for row_no, data in enumerate(key_val):
            worksheet.write_row(row_no+1, 0, data)
    write_log(log, log_filename)


# open docx document
document = get_docx_content('input/cai-immunofluorescence-rewritten.docx')
print('amount of paragraphs: ' + str(len(document.paragraphs)))
kv, log = parse_docx2_content(document)
write_to_json(kv, log, "output/cai-immunofluorescence-rewritten.json")
write_to_xlsx(kv, log, "output/cai-immunofluorescence-rewritten.xlsx")