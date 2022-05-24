import json
import re
from enum import Enum
import xlsxwriter
from docx import Document
from bs4 import BeautifulSoup
import elabapy
import markdown
import pypandoc
from markdown import Markdown
from io import StringIO
import os
from PIL import Image
from urllib.parse import urlparse
from urllib.request import urlopen
from io import BytesIO
import zipfile
import argparse
from gooey import Gooey, GooeyParser
import sys
from message import display_message


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


class Misc_error_and_warning_msg(Enum):
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
    SIMILAR_PAR_KEY_FOUND = "WARNING: A combination of similar paragraph number and key has been found, %s. Please " \
                            "make sure that this is intended."
    INVALID_KV_SET_ELEMENT_NO = "ERROR: The number of key value element set must be either two (key-value) or four " \
                                "(key-value-measure-unit). There are %s element(s) found in this key-value set: %s."


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


def split_into_sentences(content):
    # The code in this function is adapted from user:5133085's answer in SO: https://stackoverflow.com/a/31505798/548451
    # (CC-BY-SA), see https://stackoverflow.com/help/licensing.
    latin_alphabets = "([A-Za-z])"
    openers = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    abbr = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    pref = "(Mr|St|Mrs|Ms|Dr)[.]"
    sites = "[.](com|net|org|io|gov|de|eu)"
    suff = "(Inc|Ltd|Jr|Sr|Co)"
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
    if isinstance(s, int) or isinstance(s, float):
        return True
    else:
        s = s.replace(',', '', 1)
        if s[0] in ('-', '+'):
            return s[1:].isdigit()
        else:
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
        if is_num(cf_split[1]):  # or
            # https://stackoverflow.com/questions/36330860/pythonically-check-if-a-variable-name-is-valid
            is_error = True
            log = log + Misc_error_and_warning_msg.ARGUMENT_MISMATCH.value % (cf_split[1], cf_split) + "\n"
    else:
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value % (
        cf_split[0].upper(), Arg_num.ARG_NUM_FOREACH.value, elements,
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
            log = log + Misc_error_and_warning_msg.ARGUMENT_MISMATCH.value % (cf_split[1], cf_split) + "\n"
        if not is_valid_comparative_operator(cf_split[2]):
            is_error = True
            log = log + Misc_error_and_warning_msg.UNRECOGNIZED_OPERATOR.value % (cf_split[2], cf_split) + "\n"
    else:
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value % (
        cf_split[0].upper(), Arg_num.ARG_NUM_WHILE.value, elements,
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
            log = log + Misc_error_and_warning_msg.ARGUMENT_MISMATCH.value % (cf_split[1], cf_split) + "\n"
        if not is_valid_comparative_operator(cf_split[2]):
            is_error = True
            log = log + Misc_error_and_warning_msg.UNRECOGNIZED_OPERATOR.value % (cf_split[2], cf_split) + "\n"
    else:
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value % (
        cf_split[0].upper(), Arg_num.ARG_NUM_IF.value, elements,
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
            log = log + Misc_error_and_warning_msg.ARGUMENT_MISMATCH.value % (cf_split[1], cf_split) + "\n"
        if not is_valid_comparative_operator(cf_split[2]):
            is_error = True
            log = log + Misc_error_and_warning_msg.UNRECOGNIZED_OPERATOR.value % (cf_split[2], cf_split) + "\n"
    else:
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value % (
        cf_split[0].upper(), Arg_num.ARG_NUM_ELSEIF.value, elements,
        cf_split) + "\n"
        is_error = True
    # note that the last value (comparison point is not yet checked as it can be digit, binary or possibly other things)
    return log, is_error


def validate_else(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements != Arg_num.ARG_NUM_ELSE.value:
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value % (
        cf_split[0].upper(), Arg_num.ARG_NUM_ELSE.value, elements,
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
            log = log + Misc_error_and_warning_msg.RANGE_NOT_NUMBERS.value % (flow_range) + "\n"
    else:
        is_error = True
        log = log + Misc_error_and_warning_msg.RANGE_NOT_TWO_ARGS.value % (flow_range) + "\n"
    return log, is_error


def validate_for(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements == Arg_num.ARG_NUM_FOR.value:  # validating number of arguments in FOR
        if is_num(cf_split[1]):  # in case 2nd argument is number, throw an error
            is_error = True
            log = log + Misc_error_and_warning_msg.ARGUMENT_MISMATCH.value % (cf_split[1], cf_split) + "\n"
        range_error_log, is_range_error = validate_range(cf_split[2])
        if is_range_error == True:  # check whether it is a valid range
            is_error = True
            log = log + range_error_log + "\n"
        if not is_valid_iteration_operator(cf_split[3]):  # check whether it is a valid operator
            is_error = True
            log = log + Misc_error_and_warning_msg.INVALID_ITERATION_OPERATOR.value % (cf_split[3], cf_split) + "\n"
    else:  # if number of argument is invalid
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value % (
        cf_split[0].upper(), Arg_num.ARG_NUM_FOR.value, elements,
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
            log = log + Misc_error_and_warning_msg.INVALID_ITERATION_OPERATOR.value % (cf_split[1], cf_split) + "\n"
    else:  # if number of argument is invalid
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value % (
        cf_split[0].upper(), Arg_num.ARG_NUM_ITERATE.value, elements,
        cf_split) + "\n"
        is_error = True
    return log, is_error


def validate_section(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements != Arg_num.ARG_NUM_SECTION.value:
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value % (
        cf_split[0].upper(), Arg_num.ARG_NUM_SECTION.value,
        elements, cf_split) + "\n"
        is_error = True
    return log, is_error


# --------------------------------------- CONTROL-FLOW PROCESSING FUNCTIONS -------------------------------------------
def process_foreach(par_no, cf_split):
    key_val = []
    log, is_error = validate_foreach(cf_split)
    if is_error:
        write_log(log)
        # print(log)
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
        # print(log)
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
        # print(log)
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
        # print(log)
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
    if re.search("\[.*?\]", flow_compared_value):
        key_val.append([par_no, Ctrl_metadata.FLOW_RANGE.value, flow_compared_value])
        start, end, range_log, range_is_error = process_range(flow_compared_value)
        key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_STRT.value, start])
        key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_END.value, end])
    else:
        key_val.append([par_no, Ctrl_metadata.FLOW_CMPRD_VAL.value, flow_compared_value])
    return key_val, log, is_error


# no arguments is passed so no validation is needed.
def process_else(par_no, cf_split):
    print(cf_split)
    key_val = []
    log = ""
    is_error = False
    log, is_error = validate_else(cf_split)
    if is_error:
        write_log(log)
        # print(log)
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
        # print(log)
        exit()
    else:
        range_values = re.split("-", flow_range[1:-1])
    return float(range_values[0]), float(range_values[1]), log, is_error


def process_for(par_no, cf_split):
    key_val = []
    log, is_error = validate_for(cf_split)
    if is_error:
        write_log(log)
        # print(log)
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
        # print(log)
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
    remains = str_with_brackets.replace(comment, '')
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
        key_val.append(["-", Ctrl_metadata.FLOW_SECTION.value, cf_split[1]])
    return key_val, log, is_error


# ---------------------------------------- METADATA EXTRACTION FUNCTIONS ----------------------------------------------
# parse opened document, first draft of sop
def extract_kvmu(kvmu):
    log = ""
    source_kvmu = kvmu
    kvmu = kvmu[1:-1]
    kv_split = re.split("\|", kvmu)
    if len(kv_split) == 2:
        key = kv_split[1]
        val = kv_split[0]
        measure = ""
        unit = ""
    elif len(kv_split) == 4:
        measure = kv_split[0]
        unit = kv_split[1]
        key = kv_split[3]
        val = kv_split[2]
    else:
        log = Misc_error_and_warning_msg.INVALID_KV_SET_ELEMENT_NO.value % (len(kv_split), str(source_kvmu))
        raise SystemExit(log)
    key = key.strip()
    val = val.strip()
    measure = measure.strip()
    unit = unit.strip()
    return key, val, measure, unit, log


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
        flow_log = Misc_error_and_warning_msg.UNRECOGNIZED_FLOW_TYPE.value % (cf_split[0].upper(), cf_split) + "\n"
    return key_val, flow_log, is_error


def strip_colon(key):
    stripped_key = re.sub('\:', '', key)
    return stripped_key


def is_explicit_key(key):
    explicit_key_pattern = r':.+?:'
    if re.match(explicit_key_pattern, key):
       return True
    else:
        return False

def strip_markup_and_explicit_keys(line):
    stripped_from_explicit_keys = re.sub(r"\|(\w\s*\.*)+\}", '', line)
    stripped_from_markup = re.sub(r"([{}()<>:])", '', stripped_from_explicit_keys)
    stripped_from_markup = re.sub(r"([|])", ' ', stripped_from_markup)
    # print(stripped_from_markup)
    return stripped_from_markup


def serialize_to_docx(narrative_lines):
    document = Document()
    for line in narrative_lines:
        if re.match(r'Goal:*|Procedure:*|Result:*|Reference:*', line, re.IGNORECASE):
            document.add_heading(line, level=1)
        elif re.match(r'Section.+', line, re.IGNORECASE):
            line = re.sub(r'Section', '', line)
            document.add_heading(line.strip(), level=3)
        else:
            line = re.sub('\s{2,}', ' ', line)
            line = re.sub(r'\s([?.!"](?:\s|$))', r'\1', line)
            document.add_paragraph(line)
    document.save(output_file_prefix + '.docx')


def parse_list(lines):
    par_no = 0
    multi_nkvmu_pair = []
    multi_nk_pair = []
    narrative_lines = []
    comment_regex = "\(.+?\)"  # define regex for parsing comment
    log = ""
    for line in lines:
        # get overall narrative lines for a clean docx document - completely separated from line parsing
        narrative_line = strip_markup_and_explicit_keys(line)
        narrative_lines.append(narrative_line.strip())
        # Check bracketing validity
        bracketing_log, is_bracket_error = check_bracket_num(par_no, line)
        log = log + bracketing_log # + "\n"
        if is_bracket_error:
            write_log(log)
            break
        # Extract KV and flow metadata
        kv_and_flow_pattern = r'\{.+?\}|<.+?>'  # Find any occurrences of either KV or control flow
        kv_pattern = r'\{.+?\}'  # Find any occurrences of KV
        flow_pattern = r'<.+?>'  # Find any occurrences of control flows
        kv_and_flow_pairs = re.findall(kv_and_flow_pattern, line)
        para_len = len(split_into_sentences(line))
        if para_len > 0:
            par_no = par_no + 1  # count paragraph index, starting from 1
            # only if it consists at least a sentence
        for kv_and_flow_pair in kv_and_flow_pairs:
            if re.match(kv_pattern, kv_and_flow_pair):
                kvmu_set = extract_kvmu(kv_and_flow_pair) #returns tuple with key, value, measure, unit, log
                # measure, unit, log could be empty
                if kvmu_set[0] != "" and kvmu_set[1] != "":
                    if re.search(comment_regex, kvmu_set[0]):
                        key, comment = process_comment(kvmu_set[0])
                    else:
                        key = kvmu_set[0]
                    if re.search(comment_regex, kvmu_set[1]):
                        val, comment = process_comment(kvmu_set[1])
                    else:
                        val = kvmu_set[1]
                    if re.search(comment_regex, kvmu_set[2]):
                        measure, comment = process_comment(kvmu_set[2])
                    else:
                        measure = kvmu_set[2]
                    if re.search(comment_regex, kvmu_set[3]):
                        unit, comment = process_comment(kvmu_set[3])
                    else:
                        unit = kvmu_set[3]
                    single_nk_pair = [par_no, key]
                    if (single_nk_pair in multi_nk_pair):
                        log = log + Misc_error_and_warning_msg.SIMILAR_PAR_KEY_FOUND.value % (single_nk_pair) + "\n"
                        # print(log)
                    if is_explicit_key(key):
                        key = strip_colon(key)
                    single_nkvmu_pair = [par_no, key, val, measure, unit]
                    multi_nk_pair.append(single_nk_pair)
                    multi_nkvmu_pair.append(single_nkvmu_pair)
            if re.match(flow_pattern, kv_and_flow_pair):
                flow_metadata, flow_log, is_flow_error = extract_flow_type(par_no, kv_and_flow_pair)
                log = log + flow_log # + "\n"
                if is_flow_error:
                    write_log(log)
                    # print(log)
                    break
                multi_nkvmu_pair.extend(flow_metadata)
    serialize_to_docx(narrative_lines)
    return multi_nkvmu_pair, log


def extract_docx_content(doc_content):
    par_no = 0
    par_lines = []
    for para in doc_content.paragraphs:
        par_lines.append(para.text)
        par_no = par_no + 1
    par_lines = list(line for line in par_lines if line)
    multi_nkvmu_pair, log = parse_list(par_lines)
    return multi_nkvmu_pair, log


# ----------------------------------------- SERIALIZING TO FILES ------------------------------------------------------
def write_to_json(list, log):
    if not os.path.isdir(output_path_prefix):
        os.mkdir(output_path_prefix)
    json.dump(list, open(output_file_prefix + ".json", 'w', encoding="utf-8"), ensure_ascii=False)
    # write_log(log)


def write_log(log):
    log = log.strip()
    print("WRITING LOGS...")
    print(log)
    with open(output_file_prefix + ".log", 'w', encoding="utf-8") as f:
        f.write(log)


def write_to_xlsx(nkvmu, log):
    header = ["PARAGRAPH NUMBER", "KEY", "VALUE", "MEASURE", "UNIT"]
    with xlsxwriter.Workbook(output_file_prefix + ".xlsx") as workbook:
        worksheet = workbook.add_worksheet()
        worksheet.write_row(0, 0, header)
        for row_no, data in enumerate(nkvmu):
            # print(data)
            worksheet.write_row(row_no + 1, 0, data)
    write_log(log)


# ------------------------------------- GETTING CONTENT FROM DOCX/ELABFTW API/MARKDOWN ------------------------------------------
# open docx document
def get_docx_content(filename):
    f = open(filename, 'rb')
    content = Document(f)
    extract_docx_media(filename)
    f.close()
    return content


def extract_docx_media(filename):
    archive = zipfile.ZipFile(filename)
    for file in archive.filelist:
        if file.filename.startswith('word/media/') and file.file_size > 10000:
            archive.extract(file, output_path_prefix)


def get_kv_log_from_html(html_content):
    soup = BeautifulSoup(html_content, "html5lib")
    non_break_space = u'\xa0'
    textmd = soup.text
    text = soup.get_text().splitlines()
    lines = [x for x in text if x != '\xa0']  # Remove NBSP if it is on a single list element
    # Replace NBSP with space if it is inside the text
    line_no = 1
    clean_lines = []
    for line in lines:
        line = line.replace(non_break_space, ' ')
        clean_lines.append(line)
        line_no = line_no + 1
    multi_nkvmu_pair, log = parse_list(clean_lines)
    return multi_nkvmu_pair, log


# extracting md via docx conversion using pandoc in case it is needed in the future
def extract_md_exp_content_via_pandoc(filename):
    output = pypandoc.convert_file(filename, 'docx', outputfile=filename+".docx")
    document = get_docx_content(filename+".docx")
    os.remove(filename+".docx")
    kv, log = extract_docx_content(document)
    log = log + output
    return kv, log

# note: eLabFTW v 3.6.x has bugs for providing html with proper image links if the image is provided per copy-paste
# directly to the text file without providing file names. for the parser to work properly, users have to ensure that
# copy-pasted image has a proper name by the end of the URL. It can be set by checking the properties of the image
# on eLabFTW and set the name of the image file there.
def extract_imgs_from_md(filename):
    f = open(filename, 'r', encoding='utf-8')
    md_text = f.read()
    html_doc = markdown.markdown(md_text)
    soup = BeautifulSoup(html_doc, 'html.parser')
    imgs = soup.findAll("img")
    if not os.path.isdir(output_path_prefix):
        os.mkdir(output_path_prefix)
    for img in imgs:
        file_path = img.get('src')
        loaded_img = Image.open(file_path)
        path_tail = os.path.split(file_path)
        loaded_img.save(output_path_prefix + path_tail[1])


def extract_imgs_from_html(current_endpoint, html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')
    imgs = soup.findAll("img")
    parsed_uri = urlparse(current_endpoint)
    base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    if not os.path.isdir(output_path_prefix):
        os.mkdir(output_path_prefix)
    for img in imgs:
        src = img.get('src')
        file_path = base_url + src
        fd = urlopen(file_path)
        read_img = BytesIO(fd.read())
        loaded_img = Image.open(read_img)
        path_tail = os.path.split(file_path)
        loaded_img.save(output_path_prefix + path_tail[1])


def unmark_element(element, stream=None):
    if stream is None:
        stream = StringIO()
    if element.text:
        stream.write(element.text)
    for sub in element:
        unmark_element(sub, stream)
    if element.tail:
        stream.write(element.tail)
    return stream.getvalue()


# patching Markdown
Markdown.output_formats["plain"] = unmark_element
__md = Markdown(output_format="plain")
__md.stripTopLevelTags = False
def unmark(text):
    return __md.convert(text)


def extract_md_via_text(filename):
    extract_imgs_from_md(filename)
    f = open(filename, 'r', encoding='utf-8')
    marked_txt = f.read()
    unmarked_txt = unmark(marked_txt).replace("\\","")
    lines = unmarked_txt.splitlines()
    multi_nkvmu_pair, log = parse_list(lines)
    return multi_nkvmu_pair, log


def extract_elab_exp_content(exp_number, current_endpoint, current_token):
    # PLEASE CHANGE THE 'VERIFY' FLAG TO TRUE UPON DEPLOYMENT
    manager = elabapy.Manager(endpoint=current_endpoint, token=current_token, verify=False)
    exp = manager.get_experiment(exp_number)
    extract_imgs_from_html(current_endpoint, exp["body"])
    kv, log = get_kv_log_from_html(exp["body"])
    # print(kv) #debug
    return kv, log

def upload_to_elab_exp(exp_number, current_endpoint, current_token, file_with_path):
    manager = elabapy.Manager(endpoint=current_endpoint, token=current_token, verify=False)
    with open(file_with_path, 'r+b') as myfile:
        params = {'file': myfile}
        manager.upload_to_experiment(exp_number, params)


# ----------------------------------------------------- GUI ------------------------------------------------------------
def parse_cfg():
    with open("etcs/lister-config.json") as json_data_file:
        data = json.load(json_data_file)
    token = data['elabftw']['token']
    endpoint = data['elabftw']['endpoint']
    exp_no = data['elabftw']['exp_no']
    output_file_name = data['elabftw']['output_file_name']
    return token, endpoint, output_file_name, exp_no

@Gooey(optional_cols=1, program_name="LISTER: Life Science Experiment Metadata Parser", sidebar_title='Source Format:',
           default_size=(800, 650)) # , image_dir='resources/')
def parse_args():
    token, endpoint, output_file_name, exp_no = parse_cfg()
    settings_msg = 'Choose your source: an eLabFTW entry, a DOCX or a Markdown file.'
    parser = GooeyParser(description=settings_msg)
    subs = parser.add_subparsers(help='commands', dest='command')

    # ELABFTW PARAMETERS
    elab_arg_parser = subs.add_parser(
        'eLabFTW', help='Parse metadata from an eLabFTW experiment entry')
    elab_arg_parser.add_argument('output_file_name',
                                 metavar='Output file name',
                                 help='[FILENAME] for your metadata and log outputs, without extension',
                                 # This will automatically generate [FILENAME].xlsx,  [FILENAME].json, and
                                 # [FILENAME].log files in the specified output folder
                                 default=output_file_name,
                                 type=str)
    elab_arg_parser.add_argument('exp_no',
                                 metavar='eLabFTW experiment ID',
                                 help='Integer indicated in the URL of the experiment',
                                 default=exp_no,
                                 type=int)
    elab_arg_parser.add_argument('endpoint',
                                 metavar = "eLabFTW API endpoint URL",
                                 help='Ask your eLabFTW admin to provide the endpoint URL for you',
                                 default=endpoint,
                                 type=str)
    elab_arg_parser.add_argument('base_output_dir',
                                 metavar = 'Base output directory',
                                 help='Local directory generally used to save your outputs',
                                 type=str,
                                 default='output',
                                 widget='DirChooser')
    elab_arg_parser.add_argument('token',
                                 metavar='eLabFTW API Token',
                                 help='Ask your eLabFTW admin to generate an API token for you',
                                 default=token,
                                 # Ask your eLabFTW admin to instance to generate one for you
                                 type=str)
    elab_arg_parser.add_argument('-f', '--uploadToggle',
                                    metavar='Upload',
                                    action='store_true',
                                    help='Upload extracted JSON/XLSX metadata to the corresponding experiment '
                                         '(for latest eLabFTW instance only)')

    # DOCX PARAMETERS
    docx_arg_parser = subs.add_parser(
        'DOCX', help='Parse metadata from DOCX files')
    docx_arg_parser.add_argument('output_file_name',
                                 metavar = 'Output file name',
                                 help='[FILENAME] for your metadata and log outputs, without extension',
                                 # This will automatically generate [FILENAME].xlsx,  [FILENAME].json, and
                                 # [FILENAME].log files in the specified output folder
                                 type=str,
                                 default='cpc03-CG')
    docx_arg_parser.add_argument('base_output_dir',
                                 metavar='Base output directory',
                                 help='Local directory generally used to save your outputs',
                                 type=str,
                                 default='output',
                                 widget='DirChooser')
    docx_arg_parser.add_argument('input_file',
                                 metavar='Input file',
                                 help='DOCX file to be parsed',
                                 gooey_options={
                                     'wildcard': "Microsoft WOrd Document (*.docx)|*.docx|" 
                                     "All files (*.*)|*.*",
                                     'default_dir': 'input/cpc/',
                                     'default_file': "cpc03-CG.md"
                                     # 'message': "pick me"
                                 },
                                 type=str,
                                 widget='FileChooser',
                                 default='input/cpc/cpc03-CG.docx')

    # MD PARAMETERS
    md_arg_parser = subs.add_parser(
        'MD', help='Parse metadata from Markdown files')
    md_arg_parser.add_argument('output_file_name',
                               metavar='Output file name',
                               help='[FILENAME] for your metadata and log outputs, without extension',
                               # This will automatically generate [FILENAME].xlsx,  [FILENAME].json, and
                               # [FILENAME].log files in the specified output folder
                               default='cpc03-CG-md',
                               type=str)
    md_arg_parser.add_argument('base_output_dir',
                               metavar='Base output directory',
                               help='Local directory generally used to save your outputs',
                               type=str,
                               default='output',
                               widget='DirChooser')
    md_arg_parser.add_argument('input_file',
                               metavar='Input file',
                               gooey_options={
                                   'wildcard':
                                       "Markdown file (*.md)|*.md|"
                                   "All files (*.*)|*.*",
                                   'default_dir': 'input/cpc/',
                                   'default_file': "cpc03-CG.md"
                                   # 'message': "pick me"
                               },
                               help='MD file to be parsed',
                               type=str,
                               default='input/cpc/cpc03-CG.md',
                               widget='FileChooser')
    args = parser.parse_args()
    return args


# ------------------------------------------------ MAIN FUNCTION ------------------------------------------------------
def main():
    global output_file_name, input_file
    global output_path_prefix, output_file_prefix, base_output_dir
    global token, exp_no, endpoint

    args = parse_args()

    # required for all input formats
    output_file_name = args.output_file_name
    base_output_dir = args.base_output_dir
    output_path_prefix = base_output_dir + "/" + output_file_name + "/"
    output_file_prefix = output_path_prefix + output_file_name

    if args.command == 'eLabFTW':
        token = args.token
        exp_no = args.exp_no
        endpoint = args.endpoint
        nkvmu, log = extract_elab_exp_content(exp_no, endpoint, token)
    elif args.command == 'DOCX':
        input_file = args.input_file
        document = get_docx_content(input_file)
        nkvmu, log = extract_docx_content(document)
    elif args.command == 'MD':
        input_file = args.input_file
        # -- use below when transforming from md->docx is needed, takes longer and pandoc must be installed.
        # kv, log = extract_md_exp_content_via_pandoc(input_file)
        # -- use below to transform md->text is needed prior to extraction (faster).
        nkvmu, log = extract_md_via_text(input_file)

    # Writing to JSON and XLSX
    write_to_json(nkvmu, log)
    write_to_xlsx(nkvmu, log)

    # may not work yet on eLabFTW v 3.6.7 - test later once HHU eLabFTW instance is updated
    if args.command == 'eLabFTW' and args.uploadToggle == True:
       upload_to_elab_exp(exp_no, endpoint, token, output_file_prefix + ".xlsx")
       upload_to_elab_exp(exp_no, endpoint, token,  output_file_prefix + ".json")


if __name__ == "__main__":
    main()