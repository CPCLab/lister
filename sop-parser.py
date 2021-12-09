import json
import re
from enum import Enum
import xlsxwriter
from docx import Document




# -------------------------------- CLASSES TO HANDLE ENUMERATED CONCEPTS --------------------------------
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

class Bracket_pair_error(Enum):
    IMPROPER_COMMENT_BRACKET = "ERROR: Mismatch between '(' and ')'. Check line "
    IMPROPER_RANGE_BRACKET = "ERROR: Mismatch between '[' and ']'.  Check line "
    IMPROPER_KV_BRACKET = "ERROR: Mismatch between '{' and '}'.  Check line "
    IMPROPER_FLOW_BRACKET = "ERROR: Mismatch between '<' and '>'.  Check line "

class Misc_error_msg(Enum):
    ARGUMENT_MISMATCH = "ERROR: Argument type mismatch: numerical value is found while string was expected. " \
                        "Check the value '%s' in the following set of values: %s."
    UNRECOGNIZED_OPERATOR = "ERROR: The logical operator is not recognized. " \
                            "Please check the operator '%s' in the following set of values: %s. " \
                            "Only 'e', 'ne', 'lt', 'lte', 'gt', 'gte' and 'between' are supported."
    UNRECOGNIZED_FLOW_TYPE = "ERROR: The flow type is not recognized. " \
                            "Please check the flow type '%s' in the following set of values: %s."
    RANGE_NOT_TWO_ARGS = "ERROR: There should only be two numerical arguments on a range separated by a dash (-). " \
                         "Please check the following set of values: %s."
    RANGE_NOT_NUMBERS = "ERROR: The range values should only contain numbers." \
                        "Check the following part: %s."
    INVALID_ITERATION_OPERATOR = "ERROR: %s is not a valid iteration operators. Only +, -, *, / and %% are supported." \
                                 "Check the following part: %s."
    IMPROPER_ARGNO = "ERROR: Expected number of arguments in the %s statement is %s, but %s was found." \
                     "Check the following part: %s"

class Arg_num(Enum):
    ARG_NUM_FOREACH = 2
    ARG_NUM_IF = 4
    ARG_NUM_ELSEIF = 4
    ARG_NUM_ELSE = 1
    ARG_NUM_WHILE = 4
    ARG_NUM_ITERATE = 3
    ARG_NUM_FOR = 5
    ARG_NUM_KV = 2
    ARG_NUM_COMMENT = 1
    ARG_NUM_SECTION = 2


# -------------------------------- SPLIT TEXT INTO SENTENCES --------------------------------
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

# -------------------------------- TYPE-VALIDATOR HELPER FUNCTIONS --------------------------------
def is_valid_comparative_operator(operator):
    operators_list = ["e", "ne", "lt", "lte", "gt", "gte", "between"]
    if operator.lower() in operators_list:
        return True
    else:
        return False

def is_valid_iteration_operator(operator):
    operators_list = ["+", "-", "*", "/", "%"]
    if operator.lower() in operators_list:
        return True
    else:
        return False

def is_num(s):
    s = s.replace('.', '', 1)
    s = s.replace(',', '', 1)
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()

# -------------------------------- CONTROL-FLOW VALIDATOR FUNCTIONS --------------------------------
def check_bracket_num(par_no, text):
    log = ""
    base_error_warning = "BRACKET ERROR: %s %s: %s"
    is_error = False
    if text.count("{") != text.count("}"):
        is_error = True
        log = base_error_warning % (Bracket_pair_error.IMPROPER_KV_BRACKET.value, str(par_no), text)
    if text.count("<") != text.count(">"):
        is_error = True
        log = base_error_warning % (Bracket_pair_error.IMPROPER_FLOW_BRACKET.value, str(par_no), text)
    if text.count("[") != text.count("]"):
        is_error = True
        log = base_error_warning % (Bracket_pair_error.IMPROPER_RANGE_BRACKET.value, str(par_no), text)
    if text.count("(") != text.count(")"):
        is_error = True
        log = base_error_warning % (Bracket_pair_error.IMPROPER_COMMENT_BRACKET.value, str(par_no), text)
    # print(log)
    return log, is_error

def validate_foreach(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements == Arg_num.ARG_NUM_FOREACH.value:
        if is_num(cf_split[1]): #or
            # https://stackoverflow.com/questions/36330860/pythonically-check-if-a-variable-name-is-valid
            is_error = True
            log = log + Misc_error_msg.ARGUMENT_MISMATCH.value % (cf_split[1], cf_split) + "\n"
    else:
        log = log + Misc_error_msg.IMPROPER_ARGNO.value % (cf_split[0].upper(), Arg_num.ARG_NUM_FOREACH.value, elements,
                                                           cf_split) + "\n"
        is_error = True
    return log, is_error

def validate_while(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements == Arg_num.ARG_NUM_WHILE.value:
        if is_num(cf_split[1]):
            is_error = True
            log = log + Misc_error_msg.ARGUMENT_MISMATCH.value % (cf_split[1], cf_split) + "\n"
        if not is_valid_comparative_operator(cf_split[2]):
            is_error = True
            log = log + Misc_error_msg.UNRECOGNIZED_OPERATOR.value % (cf_split[2], cf_split) + "\n"
    else:
        log = log + Misc_error_msg.IMPROPER_ARGNO.value % (cf_split[0].upper(), Arg_num.ARG_NUM_WHILE.value, elements,
                                                           cf_split) + "\n"
        is_error = True
    # note that the last value (comparison point is not yet checked as it can be digit, binary or possibly other things)
    return log, is_error

def validate_if(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements == Arg_num.ARG_NUM_IF.value:
        if is_num(cf_split[1]):
            is_error = True
            log = log + Misc_error_msg.ARGUMENT_MISMATCH.value % (cf_split[1], cf_split) + "\n"
        if not is_valid_comparative_operator(cf_split[2]):
            is_error = True
            log = log + Misc_error_msg.UNRECOGNIZED_OPERATOR.value % (cf_split[2], cf_split) + "\n"
    else:
        log = log + Misc_error_msg.IMPROPER_ARGNO.value % (cf_split[0].upper(), Arg_num.ARG_NUM_IF.value, elements,
                                                           cf_split) + "\n"
        is_error = True
    # note that the last value (comparison point) is not yet checked as it can be digit, binary or possibly other things
    return log, is_error

# Validation functions for else if, while and if have similar properties. Hence, these functions can be integrated, but
# if there are changes for each of those, it may be difficult to refactor. For now these validation functions are
# provided individually.
def validate_elseif(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements == Arg_num.ARG_NUM_ELSEIF.value:
        if is_num(cf_split[1]):
            is_error = True
            log = log + Misc_error_msg.ARGUMENT_MISMATCH.value % (cf_split[1], cf_split) + "\n"
        if not is_valid_comparative_operator(cf_split[2]):
            is_error = True
            log = log + Misc_error_msg.UNRECOGNIZED_OPERATOR.value % (cf_split[2], cf_split) + "\n"
    else:
        log = log + Misc_error_msg.IMPROPER_ARGNO.value % (cf_split[0].upper(), Arg_num.ARG_NUM_ELSEIF.value, elements,
                                                           cf_split) + "\n"
        is_error = True
    # note that the last value (comparison point is not yet checked as it can be digit, binary or possibly other things)
    return log, is_error

def validate_else(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements != Arg_num.ARG_NUM_ELSE.value:
        log = log + Misc_error_msg.IMPROPER_ARGNO.value % (cf_split[0].upper(), Arg_num.ARG_NUM_ELSE.value, elements,
                                                           cf_split) + "\n"
        is_error = True
    return log, is_error

def validate_range(flow_range):
    is_error = False
    log = ""
    range_values = re.split("-", flow_range[1:-1])
    if len(range_values) == 2:
        if not (is_num(range_values[0]) and is_num(range_values[0])):
            is_error = True
            log = log + Misc_error_msg.RANGE_NOT_NUMBERS.value % (flow_range)+ "\n"
    else:
        is_error = True
        log = log + Misc_error_msg.RANGE_NOT_TWO_ARGS.value % (flow_range) + "\n"
    return log, is_error

def validate_for(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements == Arg_num.ARG_NUM_FOR.value:                       # validating number of arguments in FOR
        if is_num(cf_split[1]):                                     # in case 2nd argument is number, throw an error
            is_error = True
            log = log + Misc_error_msg.ARGUMENT_MISMATCH.value % (cf_split[1], cf_split) + "\n"
        range_error_log, is_range_error = validate_range(cf_split[2])
        if is_range_error == True:                                  # check whether it is a valid range
            is_error = True
            log = log + range_error_log + "\n"
        if not is_valid_iteration_operator(cf_split[3]):            # check whether it is a valid operator
            is_error = True
            log = log + Misc_error_msg.INVALID_ITERATION_OPERATOR.value % (cf_split[3], cf_split) + "\n"
    else: # if number of argument is invalid
        log = log + Misc_error_msg.IMPROPER_ARGNO.value % (cf_split[0].upper(), Arg_num.ARG_NUM_FOR.value, elements,
                                                           cf_split) + "\n"
        is_error = True
    return log, is_error

def validate_iterate(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements == Arg_num.ARG_NUM_ITERATE.value:
        if not is_valid_iteration_operator(cf_split[1]):
            is_error = True
            log = log + Misc_error_msg.INVALID_ITERATION_OPERATOR.value % (cf_split[1], cf_split) + "\n"
    else:  # if number of argument is invalid
        log = log + Misc_error_msg.IMPROPER_ARGNO.value % (cf_split[0].upper(), Arg_num.ARG_NUM_ITERATE.value, elements,
                                                           cf_split) + "\n"
        is_error = True
    return log, is_error

def validate_section(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements != Arg_num.ARG_NUM_SECTION.value:
        log = log + Misc_error_msg.IMPROPER_ARGNO.value % (cf_split[0].upper(), Arg_num.ARG_NUM_SECTION.value,
                                                           elements, cf_split) + "\n"
        is_error = True
    return log, is_error

# -------------------------------- CONTROL-FLOW PROCESSING FUNCTIONS --------------------------------
def process_foreach(par_no, cf_split):
    key_val = []
    log, is_error = validate_foreach(cf_split)
    if is_error:
        write_log(log)
        print(log)
        exit()
    step_type = "iteration"
    key_val.append([par_no, Ctrl_metadata.STEP_TYPE.value, step_type])
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type])
    flow_param = cf_split[1]
    key_val.append([par_no, Ctrl_metadata.FLOW_PARAM.value, flow_param])
    return key_val, log, is_error

def process_while(par_no, cf_split):
    key_val = []
    log, is_error = validate_while(cf_split)
    if is_error:
        write_log(log)
        print(log)
        exit()
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
    return key_val, log, is_error

def process_if(par_no, cf_split):
    key_val = []
    log, is_error = validate_if(cf_split)
    if is_error:
        write_log(log)
        print(log)
        exit()
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
    return key_val, log, is_error

def process_elseif(par_no, cf_split):
    key_val = []
    log, is_error = validate_elseif(cf_split)
    if is_error:
        write_log(log)
        print(log)
        exit()
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
        start, end, range_log, range_is_error = process_range(flow_compared_value)
        key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_STRT.value, start])
        key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_END.value, end])
    else:
        key_val.append([par_no, Ctrl_metadata.FLOW_CMPRD_VAL.value, flow_compared_value])
    return key_val, log, is_error

# no arguments is passed so no validation is needed.
def process_else(par_no, cf_split):
    key_val = []
    log = ""
    is_error = False
    log, is_error = validate_else(cf_split)
    if is_error:
        write_log(log)
        print(log)
        exit()
    step_type = "conditional"
    key_val.append([par_no, Ctrl_metadata.STEP_TYPE.value, step_type])
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type])
    return key_val, log, is_error

def process_range(flow_range):
    log, is_error = "", False
    log, is_error = validate_range(flow_range)
    if is_error:
        write_log(log)
        print(log)
        exit()
    else:
        range_values = re.split("-", flow_range[1:-1])
    return float(range_values[0]), float(range_values[1]), log, is_error

def process_for(par_no, cf_split):
    key_val = []
    log, is_error = validate_for(cf_split)
    if is_error:
        write_log(log)
        print(log)
        exit()
    step_type = "iteration"
    key_val.append([par_no, Ctrl_metadata.STEP_TYPE.value, step_type])
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type])
    flow_param = cf_split[1]
    key_val.append([par_no, Ctrl_metadata.FLOW_PARAM.value, flow_param])
    flow_range = cf_split[2]
    key_val.append([par_no, Ctrl_metadata.FLOW_RANGE.value, flow_range])
    start, end, log, is_error = process_range(flow_range)
    key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_STRT.value, start])
    key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_END.value, end])
    flow_operation = cf_split[3]
    key_val.append([par_no, Ctrl_metadata.FLOW_OPRTN.value, flow_operation])
    flow_magnitude = cf_split[4]
    key_val.append([par_no, Ctrl_metadata.FLOW_MGNTD.value, flow_magnitude])
    return key_val, log, is_error

# should happen only after having 'while' iterations to provide additional steps on the iterator
def process_iterate(par_no, cf_split):
    key_val = []
    log = ""
    is_error = False
    pw_log, pw_is_error = validate_iterate(cf_split)
    if pw_is_error:
        log = log + pw_log + "\n"
        print(log)
        write_log(log)
        exit()
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type + "  (after while)"])
    flow_operation = cf_split[1]
    key_val.append([par_no, Ctrl_metadata.FLOW_OPRTN.value, flow_operation])
    flow_magnitude = cf_split[2]
    key_val.append([par_no, Ctrl_metadata.FLOW_MGNTD.value, flow_magnitude])
    return key_val, log, is_error

def process_comment(str_with_brackets):
    comment_regex = "\(.+?\)"
    comment = re.search(comment_regex, str_with_brackets)
    comment = comment.group(0)
    remains = str_with_brackets.replace(comment,'')
    comment = comment[1:-1]
    return remains.strip(), comment.strip()

def process_section(cf_split):
    key_val = []
    log = ""
    is_error = False
    sect_log, sect_is_error = validate_section(cf_split)
    if sect_is_error:
        is_error = True
        log = log + sect_log + "\n"
    else:
        key_val.append(["-",Ctrl_metadata.FLOW_SECTION.value, cf_split[1]])
    return key_val, log, is_error

# -------------------------------- METADATA EXTRACTION FUNCTIONS --------------------------------
# parse opened document, first draft of sop
def extract_kv(kv):
    kv = kv[1:-1]
    kv_split = re.split("\|", kv)
    key = kv_split[1]
    key = key.strip()
    val = kv_split[0]
    val = val.strip()
    return key, val

def extract_flow_type(par_no, flow_control_pair):
    flow_log = ""
    is_error = False
    key_val = []
    cf = flow_control_pair[1:-1]
    cf_split = re.split("\|", cf)
    flow_type = cf_split[0]
    flow_type = flow_type.strip()
    flow_type = flow_type.lower()
    if flow_type == "for each":
        key_val, flow_log, is_error = process_foreach(par_no, cf_split)
    elif flow_type == "while":
        key_val, flow_log, is_error = process_while(par_no, cf_split)
    elif flow_type == "if":
        key_val, flow_log, is_error = process_if(par_no, cf_split)
    elif flow_type == "else if" or flow_type == "elif":
        key_val, flow_log, is_error = process_elseif(par_no, cf_split)
    elif flow_type == "else":
        key_val, flow_log, is_error = process_else(par_no, cf_split)
    elif flow_type == "for":
        key_val, flow_log, is_error = process_for(par_no, cf_split)
    elif flow_type.casefold() == "section".casefold():
        key_val, flow_log, is_error = process_section(cf_split)
    elif flow_type == "iterate":
        key_val, flow_log, is_error = process_iterate(par_no, cf_split)
    else:
        # key_val, flow_log, is_error = process_post_while(par_no, cf_split)
        is_error = True
        flow_log = Misc_error_msg.UNRECOGNIZED_FLOW_TYPE.value % (cf_split[0].upper(), cf_split)  + "\n"
    return key_val, flow_log, is_error

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

# parse opened document, second draft of sop
def parse_docx2_content(doc_content):
    par_no = 0
    key_val = []
    comment_regex = "\(.+?\)"                                      # define regex for parsing comment
    log = ""
    for para in doc_content.paragraphs:
        # Check bracketing validity
        bracketnum_log, is_bracket_error = check_bracket_num(par_no, para.text)
        log = log + bracketnum_log + "\n"
        if is_bracket_error:
            write_log(log)
            print(log)
            break
        # Extract KV and flow metadata
        kv_and_flow_pattern = r'\{.+?\}|<.+?>'
        kv_pattern = r'\{.+?\}'
        flow_pattern = r'<.+?>'
        section_pattern = r'\<section|.>'
        kv_and_flow_pairs = re.findall(kv_and_flow_pattern, para.text)
        if len(kv_and_flow_pairs) > 0 and bool(re.match(section_pattern, kv_and_flow_pairs[0], re.IGNORECASE)) is False:
            # THhe definition of paragraph here is therefore anything non section that has at least 1 KV/Control Flow
            par_no = par_no + 1  # count paragraph index, starting from 1 and iterate
        for kv_and_flow_pair in kv_and_flow_pairs:
            if re.match(kv_pattern, kv_and_flow_pair):
                key, val = extract_kv(kv_and_flow_pair)
                if key != "" and val != "":
                    if re.search(comment_regex, key):
                        key, comment = process_comment(key)
                    if re.search(comment_regex, val):
                        val, comment = process_comment(val)
                    #NOTE: comment from key or value is available but not yet serialized into files. TBD.
                    one_key_val = [par_no, key, val]
                    key_val.append(one_key_val)
                    print([par_no, key, val])
            if re.match(flow_pattern, kv_and_flow_pair):
                flow_metadata, flow_log, is_flow_error = extract_flow_type(par_no, kv_and_flow_pair)
                log = log + flow_log + "\n"
                if is_flow_error:
                    write_log(log)
                    print(log)
                    break
                key_val.extend(flow_metadata)
    return key_val, log

# -------------------------------- SERIALIZING TO FILES --------------------------------
def write_to_json(list, log, filename):
    json.dump(list, open(filename + "json", 'w', encoding="utf-8"), ensure_ascii=False)
    write_log(log)

def write_log(log):
    with open(output_file_prefix + "log", 'w', encoding="utf-8") as f:
        f.write(log)

def write_to_xlsx(key_val, log, output_file):
    header = ["LINE NUMBER","KEY","VALUE"]
    with xlsxwriter.Workbook(output_file + "xlsx") as workbook:
        worksheet = workbook.add_worksheet()
        worksheet.write_row(0, 0, header)
        for row_no, data in enumerate(key_val):
            worksheet.write_row(row_no+1, 0, data)
    write_log(log)

# open docx document
def get_docx_content(filename):
    f = open(filename, 'rb')
    content = Document(f)
    f.close()
    return content

# ADJUST INPUT/OUTPUT FILE HERE
output_file_prefix = "output/cpc-material-method."
input_file = 'input/cpc-material-method.docx'
# output_file_prefix = "output/cpc-rewritten."
# input_file = 'input/cpc-rewritten.docx'


document = get_docx_content(input_file)
print('No. of lines: ' + str(len(document.paragraphs)))
kv, log = parse_docx2_content(document)
write_to_json(kv, log, output_file_prefix)
write_to_xlsx(kv, log, output_file_prefix)