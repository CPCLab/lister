import json
import re
from enum import Enum
import xlsxwriter
from docx import Document
from bs4 import BeautifulSoup, Tag
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
import PyInstaller
import zipfile
import argparse
from gooey import Gooey, GooeyParser
import sys
from message import display_message
import ssl
import platform
from pathlib import Path
import pathlib
import pandas as pd


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
    INACCESSIBLE_ATTACHMENT = "WARNING: File with name %s and ID %s is not accessible, with the exception: " \
                              "\n %s. \n Try contacting eLabFTW administrator reporting the exception mentioned."  \
                     "Check the following part: %s"
    INVALID_KV_SET_ELEMENT_NO = "ERROR: The number of key value element set must be either two (key-value) or four " \
                                "(key-value-measure-unit). There are %s element(s) found in this key-value set: %s."


class Regex_patterns(Enum):
    EXPLICIT_KEY = r':.+?:' # catch explicit key which indicated within ":" sign
    KV_OR_FLOW = r'\{.+?\}|<.+?>'  # find any occurrences of either KV or control flow
    KV = r'\{.+?\}'  # find any occurrences of KV
    FLOW = r'<.+?>'  # find any occurrences of control flows
    DOI = r"\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![\"&\'<>])\S)+)\b" # catch DOI
    COMMENT = "\(.+?\)"  # define regex for parsing comment
    COMMENT_W_CAPTURE_GROUP = "(\(.+?\))"
    COMMENT_VISIBLE = "\(:.+?:\)"
    COMMENT_INVISIBLE = "\(_.+?_\)"
    SEPARATOR_AND_KEY = r"\|(\s*\w\s*\.*)+\}" # catch the end part of KV pairs (the key, tolerating trailing spaces)
    BRACKET_MARKUPS = r"([{}<>])" # catch KV/section bracket annotations
    SEPARATOR_COLON_MARKUP = r"([|:])" # catch separator annotation
    PRE_PERIOD_SPACES = '\s+\.'
    PRE_COMMA_SPACES = '\s+,'
    SUBSECTION = '(sub)*section'
    SUBSECTION_W_EXTRAS = r'(sub)*section.+'


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


# no arguments are passed so no validation is needed.
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


def get_comment_properties(str_with_brackets):
    reference = ""
    comment = str_with_brackets[1:-1]
    # doi_regex = r"\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![\"&\'<>])\S)+)\b"
    isVisible = is_explicit_key(comment)
    isReference = bool(re.search(Regex_patterns.DOI.value, comment))
    if isReference:
        reference = re.match(Regex_patterns.DOI.value, comment).group(0)
        # print("REFERENCE: ", reference)
    # print("VISIBILITY?: %s" % str(isVisible))
    # print("REFERENCE?: %s STRING: %s" % (str(isReference), comment))
    return isVisible, isReference, reference


# only process the comment that is within (key value measure unit) pairs and remove its content
# (unless if it is begun with "!")
def process_internal_comment(str_with_brackets):
    # comment_regex = "\(.+?\)"
    comment = re.search(Regex_patterns.COMMENT.value, str_with_brackets)
    comment = comment.group(0)
    remains = str_with_brackets.replace(comment, '')
    # comment = comment[1:-1]
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
        section_keyword = cf_split[0].lower()
        section_level = section_keyword.count("sub")
        key_val.append(["-", Ctrl_metadata.FLOW_SECTION.value + " level " + str(section_level), cf_split[1], "", ""])
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
    elif len(kv_split) == 3:
        val = kv_split[0]
        unit = kv_split[1]
        key = kv_split[2]
        measure = ""
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
    # elif flow_type.casefold() == "section".casefold():
    elif re.match(Regex_patterns.SUBSECTION.value, flow_type, flags=re.IGNORECASE):
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
    if re.match(Regex_patterns.EXPLICIT_KEY.value, key):
       return True
    else:
        return False


def process_reg_bracket(line):
    global ref_counter
    references = []
    # split based on the existence of brackets - including the captured bracket block in the result
    line_elements = re.split(Regex_patterns.COMMENT_W_CAPTURE_GROUP.value, line)
    processed_line = ""
    for element in line_elements:
        if re.search(Regex_patterns.COMMENT.value, element):
            # _invisible_ comment - strip all content (brackets, underscores, content
            if re.search(Regex_patterns.COMMENT_INVISIBLE.value, element):
                processed_element = ""
            # visible comment - strip brackets and colons, keep the content
            elif re.search(Regex_patterns.COMMENT_VISIBLE.value, element):
                processed_element = element[2:-2]
            # comment that refer to DOI - strip all for now
            elif re.search(Regex_patterns.DOI.value, element[1:-1]):
                ref_counter = ref_counter + 1
                processed_element = " [" + str(ref_counter) + "]"
                references.append(element[1:-1])
            # otherwise, keep as is.
            else:
                processed_element = element
        else:
            processed_element = element
        processed_line = processed_line + processed_element
    return processed_line, references


def strip_markup_and_explicit_keys(line):
    # strip keys that are not marked visible (keys that are not enclosed with colon)
    stripped_from_explicit_keys = re.sub(Regex_patterns.SEPARATOR_AND_KEY.value, '', line)
    # strip curly and angle brackets
    stripped_from_markup = re.sub(Regex_patterns.BRACKET_MARKUPS.value, '', stripped_from_explicit_keys)
    # process based on the types within regular comment
    comments_based_strip, references = process_reg_bracket(stripped_from_markup)

    # strip separator (pipe symbol)
    stripped_from_markup = re.sub(Regex_patterns.SEPARATOR_COLON_MARKUP.value, ' ', comments_based_strip)
    # strip unnecessary whitespaces
    stripped_from_trailing_spaces = re.sub(Regex_patterns.PRE_PERIOD_SPACES.value, '.', stripped_from_markup)
    stripped_from_trailing_spaces = re.sub(Regex_patterns.PRE_COMMA_SPACES.value, ',', stripped_from_trailing_spaces)
    stripped_from_trailing_spaces = " ".join(stripped_from_trailing_spaces.split()) # strip from trailing whitespaces
    return stripped_from_trailing_spaces, references


def remove_empty_tags(soup):
    for x in soup.find_all():
       # if the text within a tag is empty, and tag name is not img/br and it is not img within p tag:
       if len(x.get_text(strip=True)) == 0 and x.name not in ['img','br', 'td','tr', 'table'] and len(x.select("p img")) == 0 :
           x.extract()
    return soup


def get_nonempty_body_tags(exp):
    html_body = exp["body"]
    soup = BeautifulSoup(html_body, "html.parser")
    non_empty_soup = remove_empty_tags(soup)
    tagged_contents = non_empty_soup.currentTag.tagStack[0].contents
    return tagged_contents


def generate_uploads_dict(exp):
    # print(exp['uploads'])
    for upload in exp['uploads']:
        print(upload)


def split(text, separators):
    default_sep = separators[0]
    for sep in separators[1:]:
        text = text.replace(sep, default_sep)
    return [i.strip() for i in text.split(default_sep)]


def get_upl_long_name(img_path):
    splitted_path = split(img_path, ('&','='))
    return(splitted_path[1]) # strip first 19 chars to get the long_name field in the upload dictionary


def get_upl_id(exp, content):
    img_path = content.img['src']
    upl_long_name = get_upl_long_name(img_path)
    uploads = exp['uploads']
    if len(uploads)>0:
        # get upload that match specified "long_name", in elabftw, the long_name is used as a filename hence will be used in the image url
        # e.g. long_name: '21/21e1e300442a68bcbc5dc743f7b3f129b6ab4224859be14c9c7e365ceac7b835a4f00064764b16fe195
        # problem: experiment that imports image from database entry does not have upload id (?) - hence need to discuss with dev
        matched_upl = next(upload for upload in uploads if upload['long_name'] == upl_long_name)
        upl_id = matched_upl['id']
        real_name = matched_upl['real_name']
    else:
        upl_id = ""
        real_name = ""
    return upl_id, real_name


def add_img_to_doc(manager, document, upl_id, real_name):
    log = ""
    # if real_name == "":
        # if img name is empty, create a random img name using 7 digits of random uppercase alphanum chars
        # real_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))
    if real_name:
        with open(output_path_prefix + real_name, 'wb') as img_file:
            try:
                if real_name == "":
                    # ‚img_file.write(manager.get_upload(upl_id))
                    print("IMAGE INACCESSIBLE") # need to discuss wuth elabftw dev
                    pass
                else:
                    img_file.write(manager.get_upload(upl_id))
                document.add_picture(output_path_prefix + real_name)
            except Exception as e:
                log = log + Misc_error_and_warning_msg.INACCESSIBLE_ATTACHMENT.value % (
                    real_name, upl_id, str(e))
                pass
    else:
        print("Image found in the experiment, but not attached. Parsing this image is disabled for security reason."
                  "See https://github.com/elabftw/elabftw/issues/3764. Fix pending until eLabFTW API V2 is released.")


def print_whole_df(df):
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(df)


def add_table_to_doc(doc, content):
    html_str_table = str(content.contents)[1:-1]
    dfs = pd.read_html("<table>" + html_str_table + "</table>")
    df = dfs[0]
    # print_whole_df(df)
    t = doc.add_table(df.shape[0], df.shape[1], style="Light Grid Accent 3")

    # process table header, merge if it has similar value with the next cell and skip adding NaN value to the cell
    for h in range(df.shape[-1]):
        if not pd.isna(df.values[0, h]):
            t.cell(0, h).text = str(df.values[0, h])
        if h < (df.shape[-1]-1):
            if df.values[0, h] == df.values[0, h + 1]:
                t.cell(0, h).merge(t.cell(0, h+1))
                h = h+1

    # process remaining table entries
    for i in range(1, df.shape[0]):
        for j in range(df.shape[-1]):
            if not pd.isna(df.values[i, j]):
                t.cell(i, j).text = str(df.values[i, j])


def get_section_title(line):
    words = line.split()
    if len(words)>1:
        return ' '.join(words[1:])
    else:
        return ""


def serialize_to_docx_detailed(manager, exp):
    document = Document()
    all_references = []
    tagged_contents = get_nonempty_body_tags(exp)
    watched_tags = ['p','h1','h2','h3','h4','h5','h6']
    # print(tagged_contents)
    for content in tagged_contents: # iterate over list of tags
        if isinstance(content, Tag):
            if len(content.select("p img")) > 0:
                print("An image is found, serializing to docx...")
                # get upload id for that particular image
                upl_id, real_name = get_upl_id(exp, content)
                # print(exp)
                add_img_to_doc(manager, document, upl_id, real_name)
            elif any(x in content.name for x in watched_tags):
            # elif content.name == "p" or content.name == "h1" content.name == "" :
                line, references = strip_markup_and_explicit_keys(str(content.string))
                if len(references) > 0:
                    all_references.append(references)

                # check if the line is either goal, procedure, result, or reference
                if re.match(r'Goal:*|Procedure:*|Result:*', line, re.IGNORECASE):
                    document.add_heading(line, level=1)

                # check if the line is a section
                # elif re.match(r'Section.+', line, re.IGNORECASE):
                elif re.match(Regex_patterns.SUBSECTION_W_EXTRAS.value, line, re.IGNORECASE):
                    section_title = get_section_title(line)
                    subsection_level = line.count("sub")
                    line = re.sub(Regex_patterns.SUBSECTION_W_EXTRAS.value, '', line)
                    if subsection_level == 0:
                        document.add_heading(section_title, level=2)
                    elif subsection_level == 1:
                        document.add_heading(section_title, level=3)
                    else:
                        document.add_heading(section_title, level=4)

                else:
                    line = re.sub('\s{2,}', ' ',
                                  line)  # replace superfluous whitespaces in preceding text with a single space
                    line = re.sub(r'\s([?.!"](?:\s|$))', r'\1', line)

                    document.add_paragraph(line)

            if content.name == "table":
                # create a table accordingly in the docx document
                print("A table is found, writing to docx...")
                # print(content)
                add_table_to_doc(document, content)
                pass
            if content.name == "img":
                print("An image is found, serializing to docx...")
                upl_id, real_name = get_upl_id(exp, content)
                add_img_to_doc(manager, document, upl_id, real_name)

    if len(all_references) > 0:
        document.add_heading("Reference", level=1)
        for reference in all_references:
            document.add_paragraph(reference, style='List Number')
    document.save(output_file_prefix + '.docx')


def print_comments(overall_comments, internal_comments, external_comments):
    if len(overall_comments) > 0:
        print("OVERALL COMMENTS TYPE: %s. CONTENT: %s" % (str(type(overall_comments)), str(overall_comments)))
    if len(internal_comments) > 0:
        print("INTERNAL COMMENTS TYPE: %s, CONTENT: %s", (str(type(internal_comments)), str(internal_comments)))
    if len(external_comments) > 0:
        print("EXTERNAL COMMENTS TYPE: %s, CONTENT: %s", (str(type(external_comments)), str(external_comments)))


def parse_lines_for_docx(lines, internal_comments):
    references = []
    narrative_lines = []
    for line in lines:
        # Extract overall comments, including those within KV pairs
        overall_comments = re.findall(Regex_patterns.COMMENT.value, line)
        # get overall narrative lines for a clean docx document - completely separated from line parsing
        narrative_line = strip_markup_and_explicit_keys(line)
        narrative_lines.append(narrative_line.strip())
    external_comments = list(set(overall_comments) - set(internal_comments))
    # print_comments(overall_comments, internal_comments, external_comments)
    for external_comment in external_comments:
        isVisible, isReference, reference = get_comment_properties(external_comment)
        if reference != "":
            references.append(reference)
    return narrative_lines, references


def parse_list_for_metadata(lines):
    par_no = 0
    multi_nkvmu_pair = []
    multi_nk_pair = []
    log = ""

    for line in lines:
        internal_comments = []

        # Check bracketing validity
        bracketing_log, is_bracket_error = check_bracket_num(par_no, line)
        log = log + bracketing_log # + "\n"
        if is_bracket_error:
            write_log(log)
            break

        # Extract KV and flow metadata
        kv_and_flow_pairs = re.findall(Regex_patterns.KV_OR_FLOW.value, line)
        para_len = len(split_into_sentences(line))
        if para_len > 0:
            par_no = par_no + 1  # count paragraph index, starting from 1 only if it consists at least a sentence
        for kv_and_flow_pair in kv_and_flow_pairs:
            if re.match(Regex_patterns.KV.value, kv_and_flow_pair):
                kvmu_set = extract_kvmu(kv_and_flow_pair) #returns tuple with key, value, measure, unit, log
                # measure, unit, log could be empty
                if kvmu_set[0] != "" and kvmu_set[1] != "":
                    if re.search(Regex_patterns.COMMENT.value, kvmu_set[0]):
                        key, comment = process_internal_comment(kvmu_set[0])
                        internal_comments.append(comment)
                    else:
                        key = kvmu_set[0]
                    if re.search(Regex_patterns.COMMENT.value, kvmu_set[1]):
                        val, comment = process_internal_comment(kvmu_set[1])
                        internal_comments.append(comment)
                    else:
                        val = kvmu_set[1]
                    if re.search(Regex_patterns.COMMENT.value, kvmu_set[2]):
                        measure, comment = process_internal_comment(kvmu_set[2])
                        internal_comments.append(comment)
                    else:
                        measure = kvmu_set[2]
                    if re.search(Regex_patterns.COMMENT.value, kvmu_set[3]):
                        unit, comment = process_internal_comment(kvmu_set[3])
                        internal_comments.append(comment)
                    else:
                        unit = kvmu_set[3]
                    single_nk_pair = [par_no, key]
                    if (single_nk_pair in multi_nk_pair):
                        log = log + Misc_error_and_warning_msg.SIMILAR_PAR_KEY_FOUND.value % (single_nk_pair) + "\n"
                    if is_explicit_key(key):
                        key = strip_colon(key)
                    single_nkvmu_pair = [par_no, key, val, measure, unit]
                    multi_nk_pair.append(single_nk_pair)
                    multi_nkvmu_pair.append(single_nkvmu_pair)
            if re.match(Regex_patterns.FLOW.value, kv_and_flow_pair):
                flow_metadata, flow_log, is_flow_error = extract_flow_type(par_no, kv_and_flow_pair)
                log = log + flow_log # + "\n"
                if is_flow_error:
                    write_log(log)
                    break
                multi_nkvmu_pair.extend(flow_metadata)
    return multi_nkvmu_pair, internal_comments, log


def extract_docx_content(doc_content):
    par_no = 0
    par_lines = []
    for para in doc_content.paragraphs:
        par_lines.append(para.text)
        par_no = par_no + 1
    par_lines = list(line for line in par_lines if line)
    multi_nkvmu_pair, log = parse_list_for_metadata(par_lines)
    return multi_nkvmu_pair, log


# ----------------------------------------- SERIALIZING TO FILES ------------------------------------------------------
def write_to_json(list):
    json.dump(list, open(output_file_prefix + ".json", 'w', encoding="utf-8"), ensure_ascii=False)


def format_to_linear(list):
    linear_lines = []
    for line in list:
        if line[0] != "-":
            linear_key = str(line[0]) + "_" + str(line[1])
        else:
            linear_key = str(line[1])
        if not line[4]:
            linear_value = str(line[2])
        else:
            linear_value = str(line[2]) + "_" + str(line[3]) + "_" + str(line[4])
        linear_line = [linear_key,linear_value]
        linear_lines.append(linear_line)
    return(linear_lines)


def write_to_linear_json(list):
    kv = format_to_linear(list)
    json.dump(kv, open(output_file_prefix + ".linear.json", 'w', encoding="utf-8"), ensure_ascii=False)


def write_log(log):
    log = log.strip()
    print("WRITING LOGS...")
    print(log)
    with open(output_file_prefix + ".log", 'w', encoding="utf-8") as f:
        f.write(log)


def write_to_xlsx(nkvmu, log):
    header = ["PARAGRAPH NUMBER", "KEY", "VALUE", "MEASURE", "UNIT"]
    with xlsxwriter.Workbook(output_file_prefix + ".xlsx") as workbook:
        # formatting cells
        header_format = workbook.add_format({'bold': True, 'bg_color':'9bbb59', 'font_color':'ffffff'})
        default_format = workbook.add_format({'border':1, 'border_color': '9bbb59'})
        section_format = workbook.add_format({'border':1, 'border_color': '9bbb59', 'bg_color':'ebf1de'})
        # creating and formatting worksheet
        worksheet = workbook.add_worksheet()
        worksheet.write_row(0, 0, header, header_format)
        worksheet.set_column('A:A', 19)
        worksheet.set_column('B:B', 18)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('D:E', 15)
        for row_no, data in enumerate(nkvmu):
            key = data[1]
            # do not use regex here or it will be very slow
            # if re.match(Regex_patterns.SUBSECTION.value, data[1].lower()):
            if len(key)>=7 and key[0:7].casefold() == "section".casefold():
                worksheet.write_row(row_no + 1, 0, data, section_format)
            else:
                worksheet.write_row(row_no + 1, 0, data, default_format)

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
    # soup = BeautifulSoup(html_content, "html5lib")
    soup = BeautifulSoup(html_content, "html.parser")
    non_break_space = u'\xa0'
    text = soup.get_text().splitlines()

    # fetching the experiment paragraph, line by line
    lines = [x for x in text if x != '\xa0']  # Remove NBSP if it is on a single list element
    # Replace NBSP with space if it is inside the text
    line_no = 1
    clean_lines = []
    for line in lines:
        line = line.replace(non_break_space, ' ')
        clean_lines.append(line)
        line_no = line_no + 1
    multi_nkvmu_pair, internal_comments, log = parse_list_for_metadata(clean_lines)
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
    for img in imgs:
        file_path = img.get('src')
        loaded_img = Image.open(file_path)
        path_tail = os.path.split(file_path)
        loaded_img.save(output_path_prefix + path_tail[1])


# DEPRECATED: no longer functions as it breaks in later eLabFTW (noticed in eLabFTW 4.3.5)
def extract_imgs_from_html(current_endpoint, html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')
    imgs = soup.findAll("img")
    parsed_uri = urlparse(current_endpoint)
    base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
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
    multi_nkvmu_pair, log = parse_list_for_metadata(lines)
    return multi_nkvmu_pair, log


def fetch_uploads(manager, uploads):
    for upload in uploads:
        with open(output_path_prefix + upload["real_name"], 'wb') as attachment:
            print("Attachment found: ID: %s, with name %s" % (upload["id"], upload["real_name"]))
            try:
                attachment.write(manager.get_upload(upload["id"]))
            except Exception as e:
                log = log + Misc_error_and_warning_msg.INACCESSIBLE_ATTACHMENT.value % (upload["real_name"], upload["id"], str(e))
                pass


def get_elab_experiment(exp_number, current_endpoint, current_token):
    # PLEASE CHANGE THE 'VERIFY' FLAG TO TRUE UPON DEPLOYMENT
    ssl._create_default_https_context = ssl._create_unverified_context
    manager = elabapy.Manager(endpoint=current_endpoint, token=current_token, verify=False)
    exp = manager.get_experiment(exp_number)
    return(manager, exp)


def extract_kv_from_elab_exp(manager, exp):
    # EXTRACT KEY VALUES
    # extract_imgs_from_html(current_endpoint, exp["body"])
    kv, log = get_kv_log_from_html(exp["body"])
    # FETCH ATTACHMENT
    uploads = exp["uploads"]
    fetch_uploads(manager, uploads)
    return kv, log


def upload_to_elab_exp(exp_number, current_endpoint, current_token, file_with_path):
    manager = elabapy.Manager(endpoint=current_endpoint, token=current_token, verify=False)
    with open(file_with_path, 'r+b') as myfile:
        params = {'file': myfile}
        manager.upload_to_experiment(exp_number, params)


def manage_output_path(dir_name, file_name):
    if platform.system()=="Darwin": # enforce output path's base to be specific to ~/Apps/lister/ + output + filename
        output_path = dir_name
    else: # in windows and linux, use the executable's directory as a base to provide the outputs instead of home dir‚
        output_path = dir_name + "/" + file_name + "/"
    return output_path


def manage_input_path():
    input_path = ""
    if platform.system()=="Darwin": # enforce input path to be specific to ~/Apps/lister/
        home = str(Path.home())
        input_path = home + "/Apps/lister/"
    return input_path


# ----------------------------------------------------- GUI ------------------------------------------------------------
def parse_cfg():
    # Manual debugging as Gooey does not support debugging directly
    # dirname, filename = os.path.split(os.path.abspath(__file__))
    # print("CURRENT CONFIG DIRECTORY: %s" % (str(dirname))) # this shows from where the executable was actually run
    input_file = manage_input_path() + "config.json"
    print("CONFIG FILE: %s" % (input_file))
    with open(input_file) as json_data_file:
        data = json.load(json_data_file)
    token = data['elabftw']['token']
    endpoint = data['elabftw']['endpoint']
    exp_no = data['elabftw']['exp_no']
    output_file_name = data['elabftw']['output_file_name']
    return token, endpoint, output_file_name, exp_no


def get_default_output_path(file_name):
    if platform.system()=="Darwin": # enforce output path's base to be specific to ~/Apps/lister/ + output + filename
        home = str(Path.home())
        output_path = home + "/Apps/lister/output/" + file_name + "/"
        print("OUTPUT PATH: %s" % (output_path))
    else: # in windows and linux, use the executable's directory as a base to provide the outputs instead of home dir‚
        current_path = pathlib.Path().resolve()
        output_path = str(current_path) + "/output/"
    return output_path


@Gooey(optional_cols=1, program_name="LISTER: Life Science Experiment Metadata Parser", sidebar_title='Source Format:',
           default_size=(900, 650)) # , image_dir='resources/')
def parse_args():
    token, endpoint, output_file_name, exp_no = parse_cfg()
    settings_msg = 'Choose your source: an eLabFTW entry, a DOCX or a Markdown file.'
    parser = GooeyParser(description=settings_msg)
    subs = parser.add_subparsers(help='commands', dest='command')

    base_output_path = get_default_output_path(output_file_name)

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
                                 default=base_output_path,
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
                                 default=base_output_path,
                                 widget='DirChooser')
    docx_arg_parser.add_argument('input_file',
                                 metavar='Input file',
                                 help='DOCX file to be parsed',
                                 gooey_options={
                                     'wildcard': "Microsoft WOrd Document (*.docx)|*.docx|" 
                                     "All files (*.*)|*.*",
                                     'default_dir': 'input/cpc/',
                                     'default_file': "cpc03-CG.md"
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
                               default=base_output_path,
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
ref_counter = 0
def main():
    global output_file_name, input_file
    global output_path_prefix, output_file_prefix, base_output_dir
    global token, exp_no, endpoint


    args = parse_args()
    output_path_prefix = manage_output_path(args.base_output_dir, args.output_file_name)
    output_file_prefix = output_path_prefix + args.output_file_name

    if not os.path.isdir(output_path_prefix):
        print("Output path %s is not available, creating the path directory..." % (output_path_prefix))
        os.makedirs(output_path_prefix)

    if args.command == 'eLabFTW':
        token = args.token
        exp_no = args.exp_no
        endpoint = args.endpoint
        manager, exp = get_elab_experiment(exp_no, endpoint, token)
        nkvmu, log = extract_kv_from_elab_exp(manager, exp)
        serialize_to_docx_detailed(manager, exp)
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
    write_to_json(nkvmu)
    write_to_linear_json(nkvmu)
    write_to_xlsx(nkvmu, log)

    # may not work yet on eLabFTW v 3.6.7 - test later once HHU eLabFTW instance is updated
    if args.command == 'eLabFTW' and args.uploadToggle == True:
       upload_to_elab_exp(exp_no, endpoint, token, output_file_prefix + ".xlsx")
       upload_to_elab_exp(exp_no, endpoint, token,  output_file_prefix + ".json")


if __name__ == "__main__":
    main()