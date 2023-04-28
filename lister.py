import json
import re
from enum import Enum
import xlsxwriter
from docx import Document
from bs4 import BeautifulSoup, Tag
import elabapy
import os
import PyInstaller
from gooey import Gooey, GooeyParser
import ssl
import platform
from pathlib import Path
import pathlib
import pandas as pd
from docx.shared import Mm, RGBColor
from lxml import etree
import latex2mathml.converter
import unicodedata
import elabapi_python
from pathvalidate import sanitize_filepath
from typing import Any, Tuple


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
                        "Check the value '{0}' in the following set of values: '{1}'."
    UNRECOGNIZED_OPERATOR = "ERROR: The logical operator is not recognized. " \
                            "Please check the operator '{0}' in the following set of values: {1}. " \
                            "Only 'e', 'ne', 'lt', 'lte', 'gt', 'gte' and 'between' are supported."
    UNRECOGNIZED_FLOW_TYPE = "WARNING: The flow type is not recognized. " \
                             "Please check the flow type {0} in the following set of values: {1}."
    RANGE_NOT_TWO_ARGS = "ERROR: There should only be two numerical arguments on a range separated by a dash (-). " \
                         "Please check the following set of values: {0}."
    RANGE_NOT_NUMBERS = "ERROR: The range values should only contain numbers." \
                        "Check the following part: {0}."
    INVALID_ITERATION_OPERATOR = "ERROR: {0} is not a valid iteration operators. Only +, -, *, / and %% are supported." \
                                 "Check the following part: {1}."
    IMPROPER_ARGNO = "ERROR: Expected number of arguments in the '{0}' statement is {1}, but {2} was found." \
                     "Check the following part: '{3}'"
    SIMILAR_PAR_KEY_FOUND = "WARNING: A combination of similar paragraph number and key has been found, '{0}'. Please " \
                            "make sure that this is intended."
    INACCESSIBLE_ATTACHMENT = "WARNING: File with name '{0}' is not accessible, with the exception: " \
                              "\n {1}. \n Try contacting eLabFTW administrator reporting the exception mentioned."
    INVALID_KV_SET_ELEMENT_NO = "ERROR: The number of key value element set must be either two (key-value) or four " \
                                "(key-value-measure-unit). There are {0} element(s) found in this key-value set: {1}."
    SINGLE_PAIRED_BRACKET = "WARNING: A Key-Value split with length = 1 is found. This can be caused by a " \
                            "mathematical formula, which is okay and hence no KV pair is written to the metadata. " \
                            "Otherwise please check this pair: {0}."
    MISSING_MML2OMML = "WARNING: Formula is found on the experiment entry. Parsing this formula to docx file requires " \
                       "MML2OMML.XSL file from Microsoft Office to be put on the same directory as config.json file. " \
                       "It is currently downloadable from https://www.exefiles.com/en/xsl/mml2omml-xsl/, Otherwise, " \
                       "formula parsing is disabled."
    NON_TWO_COLS_LINKED_TABLE = "WARNING: The linked category '{0}' has a table that with {1} column instead of 2. " \
                                "This linked item is skipped. Please recheck and consider using two columns to " \
                                "allow key-value format."


class Regex_patterns(Enum):
    EXPLICIT_KEY = r':.+?:'  # catch explicit key which indicated within ":" sign
    SORROUNDED_W_COLONS = r'^:.+?:$'  # catch explicit key which indicated within ":" sign
    KV_OR_FLOW = r'\{.+?\}|<.+?>'  # find any occurrences of either KV or control flow
    KV = r'\{.+?\}'  # find any occurrences of KV
    FLOW = r'<.+?>'  # find any occurrences of control flows
    DOI = r"\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![\"&\'<>])\S)+)\b"  # catch DOI
    COMMENT = "\(.+?\)"  # define regex for parsing comment
    FORMULA = "\$.*\$"  # define regex for parsing comment
    COMMENT_W_CAPTURE_GROUP = "(\(.+?\)*.*\))"
    COMMENT_VISIBLE = "\(:(.+?):\)"
    # COMMENT_VISIBLE = "\(:.+?:\)"
    COMMENT_INVISIBLE = "\(_.+?_\)"
    SEPARATOR_AND_KEY = r"\|(\s*\w\s*\.*)+\}"  # catch the end part of KV pairs (the key, tolerating trailing spaces)
    BRACKET_MARKUPS = r"([{}<>])"  # catch KV/section bracket annotations
    SEPARATOR_COLON_MARKUP = r"([|:])"  # catch separator and colon annotation
    SEPARATOR_MARKUP = r"([|])"  # catch separator annotation
    PRE_PERIOD_SPACES = '\s+\.'
    PRE_COMMA_SPACES = '\s+,'
    SUBSECTION = '(sub)*section'
    SUBSECTION_W_EXTRAS = r'(sub)*section.+'
    SPAN_ATTR_VAL = r"(\w+-?\w+):(#?\w+?);"


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
    '''
    Split a line into proper sentences.

    :param str content: a line string that potentially consists of multiple sentences.
    :return: list sentences: list of split sentences, with regular/annotation bracket still intact.
    '''
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
# Used in several control flow validation functions.
def is_valid_comparative_operator(operator):
    operators_list = ["e", "ne", "lt", "lte", "gt", "gte", "between"]
    if operator.lower() in operators_list:
        return True
    else:
        return False


# Used in several control flow validation functions.
def is_valid_iteration_operator(operator):
    operators_list = ["+", "-", "*", "/", "%"]
    if operator.lower() in operators_list:
        return True
    else:
        return False


# Used in several control flow validation functions.
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
    '''
    Check if there is any bracketing error over the text line

    :param int par_no: paragraph number for the referred line
    :param str text: string of the line
    :return: tuple (log, is_error)
        WHERE
        str log: error log (if any)
        bool is_error:flag if the checked line contains bracketing error
    '''
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


# Used in process_foreach()
def validate_foreach(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements == Arg_num.ARG_NUM_FOREACH.value:
        if is_num(cf_split[1]):  # or
            # https://stackoverflow.com/questions/36330860/pythonically-check-if-a-variable-name-is-valid
            is_error = True
            log = log + Misc_error_and_warning_msg.ARGUMENT_MISMATCH.value.format(cf_split[1], cf_split) + "\n"
    else:
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value.format(
            cf_split[0].upper(), Arg_num.ARG_NUM_FOREACH.value, elements,
            cf_split) + "\n"
        is_error = True
    return log, is_error


# Used in process_while().
def validate_while(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements == Arg_num.ARG_NUM_WHILE.value:
        if is_num(cf_split[1]):
            is_error = True
            log = log + Misc_error_and_warning_msg.ARGUMENT_MISMATCH.value.format(cf_split[1], cf_split) + "\n"
        if not is_valid_comparative_operator(cf_split[2]):
            is_error = True
            log = log + Misc_error_and_warning_msg.UNRECOGNIZED_OPERATOR.value.format(cf_split[2], cf_split) + "\n"
    else:
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value.format(
            cf_split[0].upper(), Arg_num.ARG_NUM_WHILE.value, elements,
            cf_split) + "\n"
        is_error = True
    # note that the last value (comparison point is not yet checked as it can be digit, binary or possibly other things)
    return log, is_error


# Used in process_if().
def validate_if(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements == Arg_num.ARG_NUM_IF.value:
        if is_num(cf_split[1]):
            is_error = True
            log = log + Misc_error_and_warning_msg.ARGUMENT_MISMATCH.value.format(cf_split[1], cf_split) + "\n"
        if not is_valid_comparative_operator(cf_split[2]):
            is_error = True
            log = log + Misc_error_and_warning_msg.UNRECOGNIZED_OPERATOR.value.format(cf_split[2], cf_split) + "\n"
    else:
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value.format(
            cf_split[0].upper(), Arg_num.ARG_NUM_IF.value, elements,
            cf_split) + "\n"
        is_error = True
    # note that the last value (comparison point) is not yet checked as it can be digit, binary or possibly other things
    return log, is_error


# Used in process_elseif().
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
            log = log + Misc_error_and_warning_msg.ARGUMENT_MISMATCH.value.format(cf_split[1], cf_split) + "\n"
        if not is_valid_comparative_operator(cf_split[2]):
            is_error = True
            log = log + Misc_error_and_warning_msg.UNRECOGNIZED_OPERATOR.value.format(cf_split[2], cf_split) + "\n"
    else:
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value.format(
            cf_split[0].upper(), Arg_num.ARG_NUM_ELSEIF.value, elements,
            cf_split) + "\n"
        is_error = True
    # note that the last value (comparison point is not yet checked as it can be digit, binary or possibly other things)
    return log, is_error


# Used in else().
def validate_else(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements != Arg_num.ARG_NUM_ELSE.value:
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value.format(
            cf_split[0].upper(), Arg_num.ARG_NUM_ELSE.value, elements,
            cf_split) + "\n"
        is_error = True
    return log, is_error


# Used in process_range().
def validate_range(flow_range):
    is_error = False
    log = ""
    range_values = re.split("-", flow_range[1:-1])
    if len(range_values) == 2:
        if not (is_num(range_values[0]) and is_num(range_values[0])):
            is_error = True
            log = log + Misc_error_and_warning_msg.RANGE_NOT_NUMBERS.value.format(flow_range) + "\n"
    else:
        is_error = True
        log = log + Misc_error_and_warning_msg.RANGE_NOT_TWO_ARGS.value.format(flow_range) + "\n"
    return log, is_error


# Used in process_for().
def validate_for(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements == Arg_num.ARG_NUM_FOR.value:  # validating number of arguments in FOR
        if is_num(cf_split[1]):  # in case 2nd argument is number, throw an error
            is_error = True
            log = log + Misc_error_and_warning_msg.ARGUMENT_MISMATCH.value.format(cf_split[1], cf_split) + "\n"
        range_error_log, is_range_error = validate_range(cf_split[2])
        if is_range_error == True:  # check whether it is a valid range
            is_error = True
            log = log + range_error_log + "\n"
        if not is_valid_iteration_operator(cf_split[3]):  # check whether it is a valid operator
            is_error = True
            log = log + Misc_error_and_warning_msg.INVALID_ITERATION_OPERATOR.value.format(cf_split[3], cf_split) + "\n"
    else:  # if number of argument is invalid
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value.format(
            cf_split[0].upper(), Arg_num.ARG_NUM_FOR.value, elements,
            cf_split) + "\n"
        is_error = True
    return log, is_error


# Used in process_iterate().
def validate_iterate(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements == Arg_num.ARG_NUM_ITERATE.value:
        if not is_valid_iteration_operator(cf_split[1]):
            is_error = True
            log = log + Misc_error_and_warning_msg.INVALID_ITERATION_OPERATOR.value.format(cf_split[1], cf_split) + "\n"
    else:  # if number of argument is invalid
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value.format(
            cf_split[0].upper(), Arg_num.ARG_NUM_ITERATE.value, elements,
            cf_split) + "\n"
        is_error = True
    return log, is_error


# Used in process_section().
def validate_section(cf_split):
    log = ""
    is_error = False
    elements = len(cf_split)
    if elements != Arg_num.ARG_NUM_SECTION.value:
        log = log + Misc_error_and_warning_msg.IMPROPER_ARGNO.value.format(
            cf_split[0].upper(), Arg_num.ARG_NUM_SECTION.value,
            elements, cf_split) + "\n"
        is_error = True
    return log, is_error


# --------------------------------------- CONTROL-FLOW PROCESSING FUNCTIONS -------------------------------------------
def process_foreach(par_no, cf_split):
    '''
    Converts key-value based on foreach control-metadata entry.

    :param int par_no: paragraph number where string fragment containing the referred pair was found.
    :param list cf_split: list of split string.
    :returns: tuple (key_val, log, is_error)
        WHERE
        list key_val: list of list, each list contain a full control-flow metadata,
        str log: log resulted from running this and subsequent functions,
        bool is_error: flag that indicates whether an error occured.
    '''
    key_val = []
    log, is_error = validate_foreach(cf_split)
    if is_error:
        # write_log(log, output_path+output_fname)
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
    '''
    Convert key value based on while control-metadata entry.

    :param int par_no: paragraph number where string fragment containing the referred pair was found.
    :param list cf_split: list of split string.
    :returns: tuple (key_val, log, is_error)
        WHERE
        list key_val: list of list, each list contain a full control-flow metadata,
        str log: log resulted from running this and subsequent functions,
        bool is_error: flag that indicates whether an error occured.
    '''
    key_val = []
    log, is_error = validate_while(cf_split)
    if is_error:
        # write_log(log, output_path+output_fname)
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
    '''
    Convert key-value based on if control-metadata entry.

    :param int par_no: paragraph number where string fragment containing the referred pair was found.
    :param list cf_split: list of split string.
    :returns: tuple (key_val, log, is_error)
        WHERE
        list key_val: list of list, each list contain a full control-flow metadata,
        str log: log resulted from running this and subsequent functions,
        bool is_error: flag that indicates whether an error occured.
    '''
    key_val = []
    log, is_error = validate_if(cf_split)
    if is_error:
        # write_log(log, output_path+output_fname)
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
    '''
    Convert key-value based on else-if control-metadata entry.

    :param int par_no: paragraph number where string fragment containing the referred pair was found.
    :param list cf_split: list of split string.
    :returns: tuple (key_val, log, is_error)
        WHERE
        list key_val: list of list, each list contain a full control-flow metadata,
        str log: log resulted from running this and subsequent functions,
        bool is_error: flag that indicates whether an error occurs.
    '''
    key_val = []
    log, is_error = validate_elseif(cf_split)
    if is_error:
        # write_log(log, output_path+output_fname)
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
    if re.search("\[.*?\]", flow_compared_value):
        key_val.append([par_no, Ctrl_metadata.FLOW_RANGE.value, flow_compared_value])
        start, end, range_log, range_is_error = process_range(flow_compared_value)
        key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_STRT.value, start])
        key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_END.value, end])
    else:
        key_val.append([par_no, Ctrl_metadata.FLOW_CMPRD_VAL.value, flow_compared_value])
    return key_val, log, is_error


def process_else(par_no, cf_split):
    '''
    Convert key value based on else control-metadata entry.

    :param int par_no: paragraph number where string fragment containing the referred pair was found.
    :param list cf_split: list of split string.
    :returns: tuple (key_val, log, is_error)
        WHERE
        list key_val: list of list, each list contain a full control-flow metadata,
        str log: log resulted from running this and subsequent functions,
        bool is_error: flag that indicates whether an error occured.
    '''
    print(cf_split)
    key_val = []
    is_error = False
    log, is_error = validate_else(cf_split)
    if is_error:
        # write_log(log, output_path+output_fname)
        print(log)
        exit()
    step_type = "conditional"
    key_val.append([par_no, Ctrl_metadata.STEP_TYPE.value, step_type])
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type])
    return key_val, log, is_error


def process_range(flow_range):
    '''
    Convert key value based on range control-metadata entry. Please consult LISTER documentation on GitHub.

    :param int par_no: paragraph number where string fragment containing the referred pair was found.
    :param list cf_split: list of split string.
    :returns: tuple (key_val, log, is_error)
        WHERE
        list key_val: list of list, each list contain a full control-flow metadata,
        str log: log resulted from running this and subsequent functions,
        bool is_error: flag that indicates whether an error occured.
    '''
    log, is_error = "", False
    log, is_error = validate_range(flow_range)
    if is_error:
        # write_log(log, output_path+output_fname)
        print(log)
        exit()
    else:
        range_values = re.split("-", flow_range[1:-1])
    return float(range_values[0]), float(range_values[1]), log, is_error


def process_for(par_no, cf_split):
    '''
    Convert key value based on for control-metadata entry. Please consult LISTER documentation on GitHub.

    :param int par_no: paragraph number where string fragment containing the referred pair was found.
    :param list cf_split: list of split string.
    :returns: tuple (key_val, log, is_error)
        WHERE
        list key_val: list of list, each list contain a full control-flow metadata,
        str log: log resulted from running this and subsequent functions,
        bool is_error: flag that indicates whether an error occured.
    '''
    key_val = []
    for_log = ""
    is_error = False
    for_validation_log, is_for_error = validate_for(cf_split)
    if is_for_error:
        # write_log(log, output_path+output_fname)
        for_log = for_log + "\n" + for_validation_log
        is_error = True
        print(for_validation_log)
        exit()
    step_type = "iteration"
    key_val.append([par_no, Ctrl_metadata.STEP_TYPE.value, step_type])
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type])
    flow_param = cf_split[1]
    key_val.append([par_no, Ctrl_metadata.FLOW_PARAM.value, flow_param])
    flow_range = cf_split[2]
    key_val.append([par_no, Ctrl_metadata.FLOW_RANGE.value, flow_range])
    start, end, range_log, is_range_error = process_range(flow_range)
    if is_range_error:
        for_log = for_log + "\n" + range_log
        print(range_log)
        is_error = True
    key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_STRT.value, start])
    key_val.append([par_no, Ctrl_metadata.FLOW_ITRTN_END.value, end])
    flow_operation = cf_split[3]
    key_val.append([par_no, Ctrl_metadata.FLOW_OPRTN.value, flow_operation])
    flow_magnitude = cf_split[4]
    key_val.append([par_no, Ctrl_metadata.FLOW_MGNTD.value, flow_magnitude])
    return key_val, for_log, is_error


# should happen only after having 'while' iterations to provide additional steps on the iterator
def process_iterate(par_no, cf_split):
    '''
    Convert key value based on while control-metadata entry. Please consult LISTER documentation on GitHub.

    :param int par_no: paragraph number where string fragment containing the referred pair was found.
    :param list cf_split: list of split string.
    :returns: tuple (key_val, log, is_error)
        WHERE
        list key_val: list of list, each list contain a full control-flow metadata,
        str log: log resulted from running this and subsequent functions,
        bool is_error: flag that indicates whether an error occured.
    '''
    key_val = []
    iterate_log = ""
    is_error = False
    log, is_error = validate_iterate(cf_split)
    if is_error:
        iterate_log = iterate_log + "\n" + log
        # write_log(log, output_path+output_fname)
        print(log)
        exit()
    flow_type = cf_split[0]
    key_val.append([par_no, Ctrl_metadata.FLOW_TYPE.value, flow_type + "  (after while)"])
    flow_operation = cf_split[1]
    key_val.append([par_no, Ctrl_metadata.FLOW_OPRTN.value, flow_operation])
    flow_magnitude = cf_split[2]
    key_val.append([par_no, Ctrl_metadata.FLOW_MGNTD.value, flow_magnitude])
    return key_val, iterate_log, is_error


def strip_unwanted_mvu_colons(word):
    '''
    Remove surrounding colon on word(s) within annotation bracket, if it belongs value/measure/unit category.

    :param str word: string with or without colons.
    :return: str word without colons.
    '''
    if re.search(Regex_patterns.SORROUNDED_W_COLONS.value, word):
        print("Surrounding colons in the value/measure/unit {} is removed".format(word))
        word = word[1:-1]  # if there are colons surrounding the word remains, remove it
    return word


# only process the comment that is within (key value measure unit) pairs and remove its content
# (unless if it is begun with "!")
def process_internal_comment(str_with_brackets):
    '''
    Separates actual part of a lister bracket annotation fragment (key/value/measure/unit) with the trailing comments.

    Internal comment refers to any comment that is available within a fragment of a lister bracket annotation.
    Internal comment will     not be bypassed to the metadata output.
    However, internal comment is important to be provided to make the experiment clear-text readable in the docx output.

    :param str str_with_brackets: a lister bracket annotation fragment with a comment.
    :returns: tuple (actual_fragment, internal_comment)
        WHERE
        str actual_fragment:  string containing the actual element of metadata, it can be either key/value/measure/unit,
        str internal_comment: string containing the comment part of the string fragment, with brackets retained.
    '''

    comment = re.search(Regex_patterns.COMMENT.value, str_with_brackets)
    comment = comment.group(0)
    remains = str_with_brackets.replace(comment, '')
    actual_fragment, internal_comment = remains.strip(), comment.strip()
    return actual_fragment, internal_comment


def process_section(cf_split):
    '''
    Convert key value based on section to a full section metadata entry

    :param list cf_split: list of strings split e.g., ['Section', 'Remarks']
    :returns: tuple (key_val, log, is_error)
        WHERE
        list key_val: list of list, each list contain a full section-metadata line
                    e.g. [['-', 'section level 0', 'Precultures', '', '']],
        str log: log resulted from running this and subsequent functions,
        bool is_error: flag that indicates whether an error occured.
    '''
    key_val = []
    section_log = ""
    is_error = False
    log, is_sect_error = validate_section(cf_split)
    if is_sect_error:
        is_error = True
        section_log = section_log + "\n" + log
        exit()
    else:
        section_keyword = cf_split[0].lower()
        section_level = section_keyword.count("sub")
        key_val.append(["-", Ctrl_metadata.FLOW_SECTION.value + " level " + str(section_level), cf_split[1], "", ""])
    return key_val, section_log, is_error


# ---------------------------------------- METADATA EXTRACTION FUNCTIONS ----------------------------------------------
# parse opened document, first draft of sop
def conv_bracketedstring_to_kvmu(kvmu):
    '''
    Extract lines to a tuple containing key, value, measure, and log.

    :param str kvmu: a string fragment with a single lister bracketing annotation.
    :returns: tuple (key, val, measure, unit, log)
        WHERE
        str key: the key portion of the string fragment,
        str val: the val portion of the string fragment,
        str measure: the measure portion of the string fragment,
        str unit: the unit portion of the string fragment,
        str log: log resulted from executing this and underlying functions.
    '''
    log = ""
    source_kvmu = kvmu
    kvmu = kvmu[1:-1]
    kv_split = re.split("\|", kvmu)
    if len(kv_split) == 2:
        key = kv_split[1]
        val = strip_unwanted_mvu_colons(kv_split[0])
        measure = ""
        unit = ""
    elif len(kv_split) == 3:
        val = strip_unwanted_mvu_colons(kv_split[0])
        unit = strip_unwanted_mvu_colons(kv_split[1])
        key = kv_split[2]
        measure = ""
    elif len(kv_split) == 4:
        measure = strip_unwanted_mvu_colons(kv_split[0])
        unit = strip_unwanted_mvu_colons(kv_split[1])
        key = kv_split[3]
        val = strip_unwanted_mvu_colons(kv_split[2])
    elif len(kv_split) == 1:
        key = ""
        val = ""
        measure = ""
        unit = ""
        print(Misc_error_and_warning_msg.SINGLE_PAIRED_BRACKET.value.format(kvmu))
        log = Misc_error_and_warning_msg.SINGLE_PAIRED_BRACKET.value.format(kvmu)
    else:
        log = Misc_error_and_warning_msg.INVALID_KV_SET_ELEMENT_NO.value.format(len(kv_split), str(source_kvmu))
        raise SystemExit(log)
    key = key.strip()
    val = val.strip()
    measure = measure.strip()
    unit = unit.strip()
    return key, val, measure, unit, log


def extract_flow_type(par_no, flow_control_pair):
    '''
    Extracts the type of flow found on any annotation with angle brackets, which can be control flow or sectioning.

    :param int par_no: paragraph number on where the control flow fragment string was found.
    :param str flow_control_pair: the control-flow pair string to be extracted for metadata.
    :returns: tuple (key_val, flow_log, is_error)
        WHERE
        list key_val: list of list, each list contain a full complete control flow metadata line
                    e.g. [['-', 'section level 0', 'Precultures', '', '']],
        str flow_log: log resulted from running this and subsequent functions,
        bool is_error: flag that indicates whether an error occured.
    '''

    flow_log = ""
    is_error = False
    key_val = []
    cf = flow_control_pair[1:-1]
    cf_split = re.split("\|", cf)
    flow_type = cf_split[0]
    flow_type = flow_type.strip()
    flow_type = flow_type.lower()
    if flow_type == "for each":
        key_val, log, is_error = process_foreach(par_no, cf_split)
        if log != "":
            flow_log = flow_log + "\n" + log
    elif flow_type == "while":
        key_val, log, is_error = process_while(par_no, cf_split)
        if log != "":
            flow_log = flow_log + "\n" + log
    elif flow_type == "if":
        key_val, log, is_error = process_if(par_no, cf_split)
        if log != "":
            flow_log = flow_log + "\n" + log
    elif flow_type == "else if" or flow_type == "elif":
        key_val, log, is_error = process_elseif(par_no, cf_split)
        if log != "":
            flow_log = flow_log + "\n" + log
    elif flow_type == "else":
        key_val, log, is_error = process_else(par_no, cf_split)
        if log != "":
            flow_log = flow_log + "\n" + log
    elif flow_type == "for":
        key_val, log, is_error = process_for(par_no, cf_split)
        if log != "":
            flow_log = flow_log + "\n" + log
    # elif flow_type.casefold() == "section".casefold():
    elif re.match(Regex_patterns.SUBSECTION.value, flow_type, flags=re.IGNORECASE):
        key_val, log, is_error = process_section(cf_split)
        if log != "":
            flow_log = flow_log + "\n" + log
    elif flow_type == "iterate":
        key_val, log, is_error = process_iterate(par_no, cf_split)
        if log != "":
            flow_log = flow_log + "\n" + log
    else:
        is_error = True
        log = Misc_error_and_warning_msg.UNRECOGNIZED_FLOW_TYPE.value.format(cf_split[0].upper(), cf_split) + "\n"
        flow_log = flow_log + "\n" + log
        print(flow_log)
    return key_val, flow_log, is_error


# Used in parse_lines_to_kv().
def strip_colon(key):
    '''
    Strip colon found on key string.
    '''
    stripped_key = re.sub('\:', '', key)
    return stripped_key


# Used in parse_lines_to_kv().
def is_explicit_key(key):
    '''
    Check whether the string is an explicit key.

    :param str key: checked string.
    :return: bool stating whether the key is a LISTER explicit key.

'''
    if re.match(Regex_patterns.EXPLICIT_KEY.value, key):
        return True
    else:
        return False


def latex_formula_to_docx(latex_formula):
    '''
    Convert latex formula to docx formula.

    This function requires MML2OMML.XSL style sheet, which normally shipped with Microsoft Office suite.
    The style sheet file should be placed in the same directory as config.json file. Please check LISTER's readme.

    :param str latex_formula: latex string to be converted to docx formula representation.
    :return: docx_formula that is going to be written to the docx file.
    '''
    log = ""
    mathml = latex2mathml.converter.convert(latex_formula)
    tree = etree.fromstring(mathml)
    try:
        xslt = etree.parse('MML2OMML.XSL')  # please check whether path on mac is ok
        transform = etree.XSLT(xslt)
        new_dom = transform(tree)
        docx_formula = new_dom.getroot()
    except Exception as e:
        docx_formula = None
        log = log + Misc_error_and_warning_msg.MISSING_MML2OMML.value
        print(log)
        pass
    return docx_formula, log


def process_reg_bracket(line):
    '''
    Process strings with regular brackets (), which can be (_invisible comment_), (regular comment), or (DOI).
    Maintain and update DOI numerical index.

    The string is returned to prepare for further docx content processing, in which the invisible comment will not be
    included, visible regular comment is still there but without brackets, and the DOI is provided with numerical
    index reference.

    :param str line: the comment string (with bracket) to be processed.
    :return: tuplle (processed_line, references)
        WHERE
        str processed_line is the processed string to be written as a part of docx content,
        list references is the list of available DOI references.
    '''
    global ref_counter
    references = []
    # split based on the existence of brackets - including the captured bracket block in the result
    line_elements = re.split(Regex_patterns.COMMENT_W_CAPTURE_GROUP.value, line)
    processed_line = ""
    for element in line_elements:
        found_dois = re.findall(Regex_patterns.DOI.value, element)
        found_doi_length = len(found_dois)
        if re.search(Regex_patterns.COMMENT.value, element):
            # _invisible_ comment - strip all content (brackets, underscores, content
            if re.search(Regex_patterns.COMMENT_INVISIBLE.value, element):
                processed_element = ""
            # visible comment - strip brackets and colons, keep the content
            elif re.search(Regex_patterns.COMMENT_VISIBLE.value, element):
                element = re.sub(Regex_patterns.SEPARATOR_MARKUP.value, '', element)
                visible_comments = re.split(Regex_patterns.COMMENT_VISIBLE.value, element)
                concatenated_string = ""
                for visible_comment in visible_comments:
                    concatenated_string = concatenated_string + visible_comment
                processed_element = concatenated_string
            # comment that refer to DOI - strip all for now
            elif found_doi_length > 0:
                processed_element = ""
                for doi in found_dois:
                    ref_counter = ref_counter + 1
                    processed_element = processed_element + " [" + str(ref_counter) + "]"
                    references.append(doi)
            # otherwise, keep as is.
            else:
                processed_element = element
        else:
            processed_element = element
        processed_line = processed_line + processed_element
    return processed_line, references


def strip_markup_and_explicit_keys(line):
    '''
    Strip keys that are marked as in visible (i.e., keys that are enclosed with colon) and extract any occuring
    pattern of DOI as reference, strip curly and angle brackets, reformat any annotation with regular bracket and fetch
    the DOI references, and strip unnecessary white spaces.

    :param bs4.element.NavigableString/str line: string to be inspected.
    :return: list of string containing DOI number.
    '''
    stripped_from_explicit_keys = re.sub(Regex_patterns.SEPARATOR_AND_KEY.value, '', line)
    # print(stripped_from_explicit_keys)
    # strip curly and angle brackets
    stripped_from_markup = re.sub(Regex_patterns.BRACKET_MARKUPS.value, '', stripped_from_explicit_keys)
    # process based on the types within regular comment
    comments_based_strip, references = process_reg_bracket(stripped_from_markup)
    # strip separator (pipe symbol)
    stripped_from_markup = re.sub(Regex_patterns.SEPARATOR_COLON_MARKUP.value, ' ', comments_based_strip)
    # strip unnecessary whitespaces
    stripped_from_trailing_spaces = re.sub(Regex_patterns.PRE_PERIOD_SPACES.value, '.', stripped_from_markup)
    stripped_from_trailing_spaces = re.sub(Regex_patterns.PRE_COMMA_SPACES.value, ',', stripped_from_trailing_spaces)
    # stripped_from_trailing_spaces = " ".join(stripped_from_trailing_spaces.split())  # strip from trailing whitespaces
    return stripped_from_trailing_spaces, references


# Used in remove_empty_tags().
def remove_empty_tags(soup):
    for x in soup.find_all():
        # if the text within a tag is empty, and tag name is not img/br/etc.. and it is not img within p tag:
        if len(x.get_text(strip=True)) == 0 and x.name not in ['img', 'br', 'td', 'tr', 'table', 'h1', 'h2', 'h3',
                                                               'h5', 'h6'] and len(x.select("p img")) == 0:
            x.extract()
    return soup


def get_nonempty_body_tags(exp):
    '''
    Clean up the source-html from empty-content html tags.

    :param bs4.soup exp: beautifulSoup4.soup experiment object.
    :return: list tagged_contents: list of non-empty html tags as well as new lines.
    '''
    html_body = exp["body"]
    soup = BeautifulSoup(html_body, "html.parser")
    non_empty_soup = remove_empty_tags(soup)
    tagged_contents = non_empty_soup.currentTag.tagStack[0].contents
    return tagged_contents


# Used in get_attachment_long_name()
def split(text, separators):
    default_sep = separators[0]
    for sep in separators[1:]:
        text = text.replace(sep, default_sep)
    return [i.strip() for i in text.split(default_sep)]


def get_attachment_long_name(img_path):
    '''
    Get upload long name from the img path.
    '''
    splitted_path = split(img_path, ('&', '='))
    return (splitted_path[1])  # strip first 19 chars to get the long_name field in the upload dictionary


def get_attachment_id(exp, content):
    '''
    Get upload id from given experiment and content.
    :param dict exp: a dictionary containing details of an experiment (html body, status, rating, next step, etc).
    :param bs4.element.Tag content: a bs4 Tag object containing <h1>/<p><img alt=... src=...> Tag that provides the
            link to a particular image file.
    :return: tuple (upl_id, real_name)
        WHERE
        str upl_id: upload id of the image attachment, used to access the image through API,
        str real_name: the name of the file when it was uploaded to eLabFTW.
    '''
    img_path = content.img['src']
    upl_long_name = get_attachment_long_name(img_path)
    uploads = exp['uploads']
    if len(uploads) > 0:
        try:
            matched_upl = next(upload for upload in uploads if upload['long_name'] == upl_long_name)
            upl_id = matched_upl['id']
            real_name = matched_upl['real_name']
        except Exception as e:
            log = Misc_error_and_warning_msg.INACCESSIBLE_ATTACHMENT.value.format("NULL", str(e))
            upl_id = ""
            real_name = ""
            print(log)
            print("Attachment download is skipped...")
            pass
    else:
        upl_id = ""
        real_name = ""
    return upl_id, real_name


# Used in add_img_to_doc()
def get_text_width(document):
    '''
    Return the text width in mm.
    '''
    section = document.sections[0]
    return (section.page_width - section.left_margin - section.right_margin) / 36000


def add_img_to_doc(document, real_name, path):
    '''
    Add image to the document file, based on upload id and image name when it was uploaded.

    :param str elabapy.Manager manager: manager object to get access to the eLabFTW API.
    :param str document: the document object that is being modified.
    :param str upl_id: upload id of the image/attachment that is going to be inserted to the document file.
    :param str real_name: real name of the image when it was uploaded to eLabFTW.
    '''
    log = ""
    if real_name:
        img_saving_path = path + '/attachments/'
        sanitized_img_saving_path = sanitize_filepath(img_saving_path, platform="auto")
        try:
            document.add_picture(sanitized_img_saving_path + "/" + real_name, width=Mm(get_text_width(document)))
        except Exception as e:
            log = log + Misc_error_and_warning_msg.INACCESSIBLE_ATTACHMENT.value.format(real_name, str(e))
            pass
        print(log)


# helper function to print dataframe, used for development and debugging
def print_whole_df(df):
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(df)


def add_table_to_doc(doc, content):
    '''
    Add table content to docx instance.

    :param doc: python-docx instance of the modified document.
    :param bs4.Elements.Tag content: html table tag.
    '''
    html_str_table = str(content.contents)[1:-1]
    dfs = pd.read_html("<table>" + html_str_table + "</table>")
    # read_html unfortunately does not retain styles/formatting, hence write your own html table parser if formatting
    # needs to be retained.
    df = dfs[0]
    # print_whole_df(df)
    t = doc.add_table(df.shape[0], df.shape[1], style="Light Grid Accent 3")

    # process table header, merge if it has similar value with the next cell and skip adding NaN value to the cell
    for h in range(df.shape[-1]):
        if not pd.isna(df.values[0, h]):
            t.cell(0, h).text = str(df.values[0, h])
        if h < (df.shape[-1] - 1):
            if df.values[0, h] == df.values[0, h + 1]:
                t.cell(0, h).merge(t.cell(0, h + 1))
                h = h + 1

    # process remaining table entries
    for i in range(1, df.shape[0]):
        for j in range(df.shape[-1]):
            if not pd.isna(df.values[i, j]):
                t.cell(i, j).text = str(df.values[i, j])


# Used in write_tag_to_doc()
def get_section_title(line):
    words = line.split()
    if len(words) > 1:
        return ' '.join(words[1:])
    else:
        return ""


# Used in write_tag_to_doc()
def get_span_attr_val(c):
    found = re.findall(Regex_patterns.SPAN_ATTR_VAL.value, c.get("style"))
    attr, val = found[0]
    return attr, val


def remove_extra_spaces(line):
    return re.sub(' +', ' ', line)


# TODO: check why some invisible key elements passed the invisibility checks.
def write_tag_to_doc(document, tag_item):
    '''
    writes and format html tag content to docx document.
    :param document: python-docx document instance.
    :param  bs4.element.Tag tag_item: tag to be processed and written to document.
    :return: list all_references containing the whole DOI found in the document.
    '''
    all_references = []
    p = document.add_paragraph()
    if isinstance(tag_item, Tag):
        section_toggle = False
        subsection_level = 0
        for subcontent in tag_item.contents:
            # strip_markup_and_explicit_keys()
            if isinstance(subcontent, Tag):
                # print("ORIGINAL CONTENT OF SUBCONTENT.GETTEXT() WITHIN A TAG INSTACE : " + subcontent.get_text())
                line, references = strip_markup_and_explicit_keys(subcontent.get_text())
                # print("LINE FROM TAG INSTANCE: " + line)
            else:
                if re.match(Regex_patterns.FORMULA.value, subcontent):
                    references = []
                    line = ""
                    formulas = re.findall(Regex_patterns.FORMULA.value, subcontent)
                    processed_subcontent = str(subcontent)
                    for formula in formulas:
                        stripped_formula = formula[1:-1]
                        processed_subcontent = processed_subcontent.replace(formula, '')
                        docx_formula, docx_formula_log = latex_formula_to_docx(stripped_formula)
                        if docx_formula != None:
                            p._element.append(docx_formula)
                            p.add_run(remove_extra_spaces(processed_subcontent))
                else:
                    line, references = strip_markup_and_explicit_keys(subcontent.string)
                    # print("LINE FROM NON-TAG INSTANCE: " + line)

            if len(references) > 0:
                all_references.extend(references)

            # check if the line is either goal, procedure, or result - but only limit that to one word
            if re.match(r'Goal:*|Procedure:*|Result:*', line, re.IGNORECASE) and len(line.split()) == 1:
                document.add_heading(line, level=1)
            # check if the line is a section with following characters
            elif re.match(Regex_patterns.SUBSECTION_W_EXTRAS.value, line, re.IGNORECASE):
                section_title = get_section_title(line)
                subsection_level = line.count("sub")
                if subsection_level == 0:
                    document.add_heading(section_title, level=2)
                elif subsection_level == 1:
                    document.add_heading(section_title, level=3)
                else:
                    document.add_heading(section_title, level=4)
            # check if it is a subscript text
            elif subcontent.name == "sub":
                # sub_text = p.add_run(line + " ")
                # print("SUB : " + line)
                sub_text = p.add_run(remove_extra_spaces(line))
                sub_text.font.subscript = True
            # check if it is an italic-formatted text
            elif subcontent.name == "em":
                # print("EM : " + line)
                italic_text = p.add_run(remove_extra_spaces(line))
                # italic_text = p.add_run(" " + line + " ")
                italic_text.font.italic = True
            # # check if it is a span tag
            elif subcontent.name == "span":
                attr, val = get_span_attr_val(subcontent)
                # check if the line is a section without being followed by other characters, hence it needs the following
                # chars from the next line as its section title. This case tends to happen when a section in a line is
                # not covered within the same span tag hierarchy as its label.
                if re.match(Regex_patterns.SUBSECTION.value, line, re.IGNORECASE):
                    section_toggle = True
                    subsection_level = line.count("sub")
                elif(section_toggle):
                    # do not use get_section_title() here as it will remove the first word of the line.
                    # the 'section' part have already been removed in this span section.
                    if subsection_level == 0:
                        document.add_heading(line, level=2)
                    elif subsection_level == 1:
                        document.add_heading(line, level=3)
                    else:
                        document.add_heading(line, level=4)
                    section_toggle = False
                elif attr == "color":
                    # print("COLOR : " + line)
                    color_text = p.add_run(remove_extra_spaces(line))
                    color_text.font.color.rgb = RGBColor.from_string(val[1:])
                elif attr == "font-style" and attr == "italic":
                    # print("FONT STYLE AND ITALIC : " + line)
                    styled_text = p.add_run(remove_extra_spaces(line))
                    styled_text.italic = True
                else:
                    # print("NON SUBSECT/HEADING/COLOR/FSTYLE : " + line)
                    p.add_run(remove_extra_spaces(line))
            # check if it is bold format
            elif subcontent.name == "strong":
                # print("STRONG : " + line)
                bold_text = p.add_run(remove_extra_spaces(line))
                bold_text.bold = True
            # check if it is superscript format
            elif subcontent.name == "sup":
                # print("SUP : " + line)
                # super_text = p.add_run(line + " ")
                super_text = p.add_run(remove_extra_spaces(line))
                super_text.font.superscript = True
            else:
                # print("NON SUP/STRONG/SPAN/EM/SUB/SECT/SUBSECT : " + line)
                p.add_run(remove_extra_spaces(line))

    else:
        line, references = strip_markup_and_explicit_keys(tag_item.string)
        if len(references) > 0:
            all_references.extend(references)
        # print("NON-TAG INSTANCE : " + line)
        p.add_run(remove_extra_spaces(line))
        # print("*"*50)
    return all_references


def derive_fname_from_exp(exp):
    exp_title = exp["title"]
    fname_from_exp = slugify(exp_title)
    return fname_from_exp


def write_to_docx(manager, exp, path):
    '''
    fetch an experiment, clean the content from LISTER annotation markup and serialize the result to a docx file.

    :param elabapy.Manager manager: elabapy Manager object, required to access the experiment from eLabFTW.
    :param dict exp: dictionary containing the properties of the experiment, including its HTML body content.
    :param str path: the path for writing the docx file, typically named based on experiment title or ID.
    '''

    document = Document()
    all_references = []
    tagged_contents = get_nonempty_body_tags(exp)
    watched_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'strong', 'sub', 'em', 'sup']
    for content in tagged_contents:  # iterate over list of tags
        if isinstance(content, Tag):
            if len(content.select("img")) > 0:
                upl_id, real_name = get_attachment_id(exp, content)
                add_img_to_doc(document, real_name, path)
            elif any(x in content.name for x in watched_tags):
                references = write_tag_to_doc(document, content)
                if len(references) > 0:
                    all_references.extend(references)
            if content.name == "table":
                print("A table is found, writing to docx...")
                add_table_to_doc(document, content)
            if content.name == "img":
                print("An image is found, serializing to docx...")
                upl_id, real_name = get_attachment_id(exp, content)
                add_img_to_doc(manager, document, upl_id, real_name, path)

    if len(all_references) > 0:
        document.add_heading("Reference", level=1)
        for reference in all_references:
            document.add_paragraph(reference, style='List Number')
    document.save(path + '/' + derive_fname_from_exp(exp) + '.docx')


def parse_lines_to_kv(lines):
    '''
    Get a list of [order, key, value, measure, unit] or ['-', sec. level, section name, '', ''] from nbsp-clean lines.
    :param list lines: list of lines cleaned up from nbsp.
    :return: tuple (nkvmu_pairs, internal_comments, log)
        WHERE
        list nkvmu_pairs: list of [order, key, value, measure, unit] or ['-', section level, section name, '', ''],
        str internal_comments: placeholder for found internal comments within key-value pairs - currently unused,
        str log: log from running subsequent functions.
    '''
    par_no = 0
    nkvmu_pairs = []
    nkvmu_header = ["", "metadata section", "Experiment Context", "", ""]
    nkvmu_pairs.append(nkvmu_header)
    nk_pairs = []
    log = ""
    for line in lines:
        internal_comments = []

        # Check bracketing validity
        bracketing_log, is_bracket_error = check_bracket_num(par_no, line)
        log = log + bracketing_log  # + "\n"
        if is_bracket_error:
            # write_log(log, output_path+output_fname)
            break

        # Extract KV and flow metadata
        kv_and_flow_pairs = re.findall(Regex_patterns.KV_OR_FLOW.value, line)
        para_len = len(split_into_sentences(line))
        if para_len > 0:
            par_no = par_no + 1  # count paragraph index, starting from 1 only if it consists at least a sentence
        for kv_and_flow_pair in kv_and_flow_pairs:
            if re.match(Regex_patterns.KV.value, kv_and_flow_pair):
                kvmu_set = conv_bracketedstring_to_kvmu(
                    kv_and_flow_pair)  # returns tuple with key, value, measure, unit, log
                # measure, unit, log could be empty
                if kvmu_set[4] != "":
                    log = log + "\n" + kvmu_set[4]
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
                    nk_pair = [par_no, key]
                    if (nk_pair in nk_pairs):
                        log = log + Misc_error_and_warning_msg.SIMILAR_PAR_KEY_FOUND.value.format(nk_pair) + "\n"
                    if is_explicit_key(key):
                        key = strip_colon(key)
                    nkvmu_pair = [par_no, key, val, measure, unit]
                    nk_pairs.append(nk_pair)
                    nkvmu_pairs.append(nkvmu_pair)
            if re.match(Regex_patterns.FLOW.value, kv_and_flow_pair):
                flow_metadata, flow_log, is_flow_error = extract_flow_type(par_no, kv_and_flow_pair)
                log = log + flow_log  # + "\n"
                if is_flow_error:
                    # write_log(log, output_path+output_fname)
                    break
                nkvmu_pairs.extend(flow_metadata)
    print(log)
    return nkvmu_pairs, internal_comments, log


# ----------------------------------------- SERIALIZING TO FILES ------------------------------------------------------
# Used to serialize extracted metadata to json file.
def write_to_json(lst, exp, path):
    """
    Write a list to a JSON file.
    :param lst: The list to write to the JSON file.
    :param exp: The experiment title or ID.
    :param path: The path for writing the JSON file.
    """
    filename = f"{derive_fname_from_exp(exp)}.json"
    with open(f"{path}/{filename}", "w", encoding="utf-8") as f:
        json.dump(lst, f, ensure_ascii=False)


def check_and_create_path(path):
    if not os.path.isdir(path):
        print("Output path %s is not available, creating the path directory..." % (path))
        os.makedirs(path)


# Used to write into the log file.
# def write_log(log, full_path=output_path_and_fname):
def write_log(log_text, path):
    """
    Write the log to a file.
    :param log_text: The log to be written to the file.
    :param path: The path for writing the log file.
    """
    log_text = log_text.strip()
    check_and_create_path(path)
    with open(f"{path}/lister-report.log", "w", encoding="utf-8") as f:
        f.write(log_text)


def write_to_xlsx(nkvmu, exp, path):
    '''
    Write extracted order/key/value/measure/unit to an Excel file.

    :param list nkvmu: list containing the order/key/value/measure/unit to be written.
    :param str log: log containing information necessary if this (and underlying) functions are not executed properly.
    :param str path: the path for writing the xlsx file, typically named based on experiment title or ID.
    '''

    check_and_create_path(path)
    header = ["PARAGRAPH NUMBER", "KEY", "VALUE", "MEASURE", "UNIT"]
    # json.dump(list, open(path + '/' + derive_fname_from_exp(exp) + ".json", 'w', encoding="utf-8"), ensure_ascii=False)
    # with xlsxwriter.Workbook(path + output_fname + ".xlsx") as workbook:
    with xlsxwriter.Workbook(path + '/' + derive_fname_from_exp(exp) + ".xlsx") as workbook:
        # formatting cells
        header_format = workbook.add_format({'bold': True, 'bg_color': '9bbb59', 'font_color': 'ffffff'})
        default_format = workbook.add_format({'border': 1, 'border_color': '9bbb59'})
        section_format = workbook.add_format({'border': 1, 'border_color': '9bbb59', 'bg_color': 'ebf1de'})
        # creating and formatting worksheet
        worksheet = workbook.add_worksheet()
        worksheet.write_row(0, 0, header, header_format)
        worksheet.set_column('A:A', 19)
        worksheet.set_column('B:B', 18)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('D:E', 15)
        for row_no, data in enumerate(nkvmu):
            key = data[1]
            # do not use regex here, or it will be very slow
            # if re.match(Regex_patterns.SUBSECTION.value, data[1].lower()):
            if len(key) >= 7 and key[0:7].casefold() == "section".casefold() or key.casefold() == "metadata section":
                worksheet.write_row(row_no + 1, 0, data, section_format)
            else:
                worksheet.write_row(row_no + 1, 0, data, default_format)


def remove_table_tag(soup):
    '''
    Remove table tags and its content from the soup object.

    :param bs4.BeautifulSoup soup: bs4 soup object.
    :return: bs4.BeautifulSoup soup object without table tag, and it's content.
    '''
    for table in soup("table"):
        table.decompose()
    return soup


def process_nbsp(soup):
    '''
    Remove non-break space (nbsp), and provide a 'clean' version of the lines.

    :param bs4.BeautifulSoup soup: soup object that is going to be cleaned up from nbsp.
    :return: list clean_lines lines without nbsp.
    '''
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
    return clean_lines


def conv_html_to_nkvmu(html_content):
    '''
    Turn html body content into extended key-value pair
            [order, key, value, measure (if applicable), unit (if applicable)] or
            [-, section level, section name, '', ''].

    :param str html_content: body of the html content, extracted from eLabFTW API experiment.
    :return: tuple (multi_nkvmu_pair, log)
        WHERE
        list multi_nkvmu_pair is a list of a list with
            [order, key, value, measure (if applicable), unit (if applicable)] or
            [-, section level, section name, '', ''],
        str log is a string log returned from the respectively-executed functions.
    '''
    # global log
    soup = BeautifulSoup(html_content, "html.parser")
    soup = remove_table_tag(soup)
    clean_lines = process_nbsp(soup)
    if clean_lines is not None:
        multi_nkvmu_pair, internal_comments, log = parse_lines_to_kv(clean_lines)
    return multi_nkvmu_pair, log


def get_and_save_attachments(manager, uploads, path):
    '''
    Get a list of attachments in the experiment entry and download these attachments.

    :param elabapy.Manager.Manage manager: an instance of manager object, containing eLabFTW API-related information.
    :param uploads: a list of dictionary, each list entry consists of dictionary with upload specific attributes
                    (e.g., file_size, real_name, long_name, hash, etc).
    :param str path: the path for downloading the attached files, typically named based on experiment title or ID.
    '''
    # global log
    upload_saving_path = path + '/' + 'attachments' + '/'
    check_and_create_path(upload_saving_path)

    for upload in uploads:
        with open(upload_saving_path + upload["real_name"], 'wb') as attachment:
            print("Attachment found: ID: %s, with name %s" % (upload["id"], upload["real_name"]))
            try:
                attachment.write(manager.get_upload(upload["id"]))
            except Exception as e:
                if not log:
                    log = Misc_error_and_warning_msg.INACCESSIBLE_ATTACHMENT.value.format(upload["real_name"],
                                                                                          str(upload["id"]), str(e))
                else:
                    log = log + Misc_error_and_warning_msg.INACCESSIBLE_ATTACHMENT.value.format(upload["real_name"],
                                                                                                str(upload["id"]),
                                                                                                str(e))
                pass


def get_api_v2endpoint(v1endpoint):
    v2endpoint = re.sub(r'http://', 'https://', v1endpoint)
    v2endpoint = re.sub(r'/v1', '/v2', v2endpoint)
    return v2endpoint


def create_apiv2_client(endpoint, token):
    endpoint_v2 = get_api_v2endpoint(endpoint)
    apiv2config = elabapi_python.Configuration()
    apiv2config.api_key['api_key'] = token
    apiv2config.api_key_prefix['api_key'] = 'Authorization'
    apiv2config.host = endpoint_v2
    apiv2config.debug = False
    apiv2config.verify_ssl = False
    apiv2_client = elabapi_python.ApiClient(apiv2config)
    apiv2_client.set_default_header(header_name='Authorization', header_value=token)
    return apiv2_client


def get_and_save_attachments_v2(path, apiv2_client, exp_id):
    '''
    Get a list of attachments in the experiment entry and download these attachments.

    :param elabapy.Manager.Manage manager: an instance of manager object, containing eLabFTW API-related information.
    :param uploads: a list of dictionary, each list entry consists of dictionary with upload specific attributes
                    (e.g., file_size, real_name, long_name, hash, etc).
    :param str path: the path for downloading the attached files, typically named based on experiment title or ID.
    '''

    log = ""

    experimentsApi = elabapi_python.ExperimentsApi(apiv2_client)
    uploadsApi = elabapi_python.UploadsApi(apiv2_client)
    exp = experimentsApi.get_experiment(int(exp_id))

    upload_saving_path = path + '/' + 'attachments'
    sanitized_upload_saving_path = sanitize_filepath(upload_saving_path, platform='auto')
    check_and_create_path(sanitized_upload_saving_path)

    for upload in uploadsApi.read_uploads('experiments', exp.id):
        with open(sanitized_upload_saving_path + "/" + upload.real_name, 'wb') as file:
            print("Attachment found: ID: {0}, with name {1}. Writing to {2}.".format(str(upload.id), upload.real_name,
                                                                                     upload_saving_path + "/" + upload.real_name))
            file.write(
                uploadsApi.read_upload('experiments', exp.id, upload.id, format='binary', _preload_content=False).data)
            file.flush()
    return log


def process_linked_db_item(manager, id):
    linked_item = manager.get_item(id)
    html_body = linked_item["body"]
    category = linked_item["category"]
    dfs = pd.read_html(html_body)
    df = pd.concat(dfs)
    df_col_no = df.shape[1]
    log = ""
    if df_col_no != 2:
        log = Misc_error_and_warning_msg.NON_TWO_COLS_LINKED_TABLE.value.format(category, df_col_no) + "\n"
        print(log)
        db_item_nkvmu_metadata = ""
        pass
    else:
        df.columns = ["metadata section", category]
        df.insert(loc=0, column="", value="")
        df = df.reindex(df.columns.tolist() + ['', ''], axis=1)
        filtered_df = df.fillna('')
        db_item_nkvmu_metadata = [filtered_df.columns.values.tolist()] + filtered_df.values.tolist()
    return db_item_nkvmu_metadata, log


def get_exp_info(exp):
    nkvmu_pairs = []
    nkvmu_pairs.append(["", "metadata section", "Experiment Info", "", ""])
    nkvmu_pairs.append(["", "title", exp['title'], "", ""])
    nkvmu_pairs.append(["", "creation date", exp['date'], "", ""])
    nkvmu_pairs.append(["", "category", exp['category'], "", ""])
    nkvmu_pairs.append(["", "author", exp['fullname'], "", ""])
    nkvmu_pairs.append(["", "tags", exp['tags'], "", ""])
    return nkvmu_pairs


def process_experiment(exp_no, endpoint, token, path):
    overall_log = ""

    manager, exp = get_elab_exp(exp_no, endpoint, token)
    # links = exp['links']
    # changed to reflect eLabFTW 4.4.3 dictionary keys name
    links = exp['items_links']
    # may need to configure this in the json file in the future
    excluded_item_types = ["MM", "Publication", "Protocols", "Protocol", "Methods", "Method"]
    filtered_links = []

    for link in links:
        # if link['name'].casefold() not in (item.casefold() for item in excluded_item_types):
        # changed to reflect eLabFTW 4.4.3 dictionary keys name
        if link['category'].casefold() not in (item.casefold() for item in excluded_item_types):
            filtered_links.append(link)

    overall_nkvmu = []
    for filtered_link in filtered_links:
        # changed to reflect eLabFTW 4.4.3 dictionary keys name
        # if len(filtered_link['itemid']) > 0:
        if filtered_link['itemid']:
            db_item_nkvmu_metadata, log = process_linked_db_item(manager, filtered_link['itemid'])
            overall_log = overall_log + "\n" + log
            overall_nkvmu.extend(db_item_nkvmu_metadata)

    exp_nkvmu_info = get_exp_info(exp)
    overall_nkvmu.extend(exp_nkvmu_info)
    exp_nkvmu, log = conv_html_to_nkvmu(exp["body"])
    overall_log = overall_log + "\n" + log
    overall_nkvmu.extend(exp_nkvmu)

    apiv2_client = create_apiv2_client(endpoint, token)
    # get_and_save_attachments(manager, exp["uploads"], path)
    log = get_and_save_attachments_v2(path, apiv2_client, int(exp_no))
    write_to_docx(manager, exp, path)

    # consult first with involved AGs whether uploading the parsing result makes sense
    # if args.uploadToggle == True:
    #    upload_to_elab_exp(exp_no, endpoint, token, output_file_prefix + ".xlsx")
    #    upload_to_elab_exp(exp_no, endpoint, token, output_file_prefix + ".json")

    # Writing to JSON and XLSX
    write_to_json(overall_nkvmu, exp, path)
    # write_to_linear_json(nkvmu)
    write_to_xlsx(overall_nkvmu, exp, path)
    write_log(overall_log, path)


def create_elab_manager(current_endpoint, current_token):
    # PLEASE CHANGE THE 'VERIFY' FLAG TO TRUE UPON DEPLOYMENT
    ssl._create_default_https_context = ssl._create_unverified_context
    manager = elabapy.Manager(endpoint=current_endpoint, token=current_token, verify=False)
    return manager


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def process_ref_db_item(db_item_no, endpoint, token, id, title):
    # Process reference database item, using the initial database ID for that container item (e.g., publication)

    manager = create_elab_manager(endpoint, token)

    # get the list of related experiments
    related_experiments = manager.send_req("experiments/?related=" + str(db_item_no), verb='GET')
    rel_exp_ids = [d['id'] for d in related_experiments if 'id' in d]

    # get the list of linked experiment IDs
    linked_experiments = manager.send_req("items/" + str(db_item_no) + "/experiment_links", verb='GET')
    linked_rel_exp = linked_experiments['experiments_links']
    linked_exp_ids = [x['itemid'] for x in linked_rel_exp if 'itemid' in x]

    # combine related experiment and linked experiment unique IDs into a new list
    exp_ids = list(set(rel_exp_ids + linked_exp_ids))

    for exp_id in exp_ids:
        exp_title = get_exp_title(endpoint, token, exp_id)
        exp_path = output_path + slugify(exp_title)
        process_experiment(exp_id, endpoint, token, exp_path)


def get_elab_exp(exp_number, current_endpoint, current_token):
    '''
    Get overall experiment object from specified experiment ID, eLabFTW endpoint, and eLabFTW token.

    :param int exp_number: experiment ID to be fetched.
    :param str current_endpoint: eLabFTW API endpoint URL.
    :param str current_token: eLabFTW token.
    :return: tuple (manager, exp)
        WHERE
        elabapy.Manager is an elabapy.Manager object of the experiment,
        dict exp is a python dictionary containing the experiment properties (id, title, html body, etc).
    '''
    # PLEASE CHANGE THE 'VERIFY' FLAG TO TRUE UPON DEPLOYMENT
    # ssl._create_default_https_context = ssl._create_unverified_context
    # manager = elabapy.Manager(endpoint=current_endpoint, token=current_token, verify=False)
    manager = create_elab_manager(current_endpoint, current_token)
    exp = manager.get_experiment(exp_number)
    return (manager, exp)


def manage_output_path(dir_name, file_name):
    '''
    Get the output path according to respective platform.

    If it is on macOS, just return the dir_name (which have already been appended with output filename),
    on Mindows/Linux, return the dir_name + output file_name.

    :param str dir_name: the home directory name for the output.
    :param str file_name: the output name.
    :return: str output_path is the output directory created from appending the home path and output path.
    '''
    if platform.system() == "Darwin":
        # on macOS, enforce output path's base to be specific to ~/Apps/lister/ + output + filename
        output_path = dir_name + file_name + "/"
    else:  # in windows and linux, use the executable's directory as a base to provide the outputs instead of home dir‚
        output_path = dir_name + "/" + file_name + "/"

    return output_path


def manage_input_path():
    '''
    Enforce reading input from a specific directory on macOS (on macOS, LISTER cannot get the input directly
    from the executable file's directory).
    '''
    input_path = ""
    if platform.system() == "Darwin":  # enforce input path to be specific to ~/Apps/lister/
        home = str(Path.home())
        input_path = home + "/Apps/lister/"
    return input_path


# ----------------------------------------------------- GUI ------------------------------------------------------------
def parse_cfg():
    '''
    Parse JSON config file, requires existing config.json file which should be specified on certain directory.

    The directory is OS-dependent. On Windows/Linux, it is in the same folder as the script/executables.
    On macOS, it is in the users' Apps/lister/config.json file.

    :returns: tuple (token, endpoint, output_file_name, exp_no)
        str token: eLabFTW API Token,
        str endpoint: eLabFTW API endpoint URL,
        str output_file_name: filename to be used for all the outputs (xlsx/json metadata, docx documentation, log file),
        int exp_no: the parsed experiment ID (int).

    '''

    input_file = manage_input_path() + "config.json"
    print("CONFIG FILE: %s" % (input_file))
    # using ...with open... allows file to be closed automatically.
    with open(input_file) as json_data_file:
        data = json.load(json_data_file)
    token = data['elabftw']['token']
    endpoint = data['elabftw']['endpoint']
    exp_no = data['elabftw']['exp_no']
    output_file_name = data['elabftw']['output_file_name']
    db_item_no = data['elabftw']['db_item_no']
    return token, endpoint, output_file_name, exp_no, db_item_no


def get_default_output_path(file_name: str) -> int:
    '''
    Create an output path based on the home path (OS-dependent) and output file name.
    The home path is OS-dependent. On Windows/Linux, it is in the output directory as the script/executables.
    On macOS, it is in the users' Apps/lister/output/ directory.

    :param str file_name: file name for the output.
    :returns: str output_path is the output path created from appending lister's output home directory and
    output file name.
    '''
    if platform.system() == "Darwin":  # enforce output path's base to be specific to ~/Apps/lister/ + output + filename
        home = str(Path.home())
        output_path = home + "/Apps/lister/output/" + file_name
        print("OUTPUT PATH: %s" % (output_path))
    else:  # in windows and linux, use the executable's directory as a base to provide the outputs instead of home dir.
        current_path = pathlib.Path().resolve()
        if platform.system() == "Windows":
            output_path = str(current_path) + "\output"
        else:
            output_path = str(current_path) + "/output/"
    return output_path


@Gooey(optional_cols=0, program_name="LISTER: Life Science Experiment Metadata Parser",
       default_size=(753, 753), navigation="TABBED")  # , image_dir='resources/')
def parse_gooey_args():
    '''
    Get arguments from an existing JSON config to be passed to Gooey's interface.

    Manual debugging (i.e., printout) is necessary when Gooey is used.

    :returns: args
        WHERE
        argparse.Namespace args is an object containing several attributes:
            - str command (e.g., eLabFTW),
            - str output_file_name,
            - int exp_no,
            - str endpoint,
            - str base_output_dir,
            - str token,
            - bool uploadToggle.
    '''
    token, endpoint, output_file_name, exp_no, db_item_no = parse_cfg()
    settings_msg = 'Please ensure to enter the fields below properly, or ask your eLabFTW admin if you have questions.'
    parser = GooeyParser(description=settings_msg)
    subs = parser.add_subparsers(help='commands', dest='command')

    base_output_path = get_default_output_path(output_file_name)

    # ELABFTW EXPERIMENT PARAMETERS
    elab_arg_parser = subs.add_parser('parse_experiment', prog="Parse Experiment",
                                      help='Parse metadata from an eLabFTW experiment entry')

    io_args = elab_arg_parser.add_argument_group("Input/Output Arguments", gooey_options={'columns': 1})
    radio_group = io_args.add_mutually_exclusive_group(required=True, gooey_options={
        'title': "Naming method for the outputs", 'initial_selection': 0})
    radio_group.add_argument("-t", "--title", metavar="Title", action="store_true",
                             help='Name files and folders based on experiment title')
    radio_group.add_argument("-i", "--id", metavar="ID", action="store_true",
                             help='Name files and folders based on the experiment ID')
    # radio_group.add_argument("-t", "--custom", metavar="Custom name", action="store_true",
    #                         help='Name output file using your input here:')
    # io_args.add_argument('output_file_name',
    # metavar='Output file name',
    # help='[FILENAME] for your metadata and log outputs, without extension',
    # This will automatically generate [FILENAME].xlsx,  [FILENAME].json, and
    # [FILENAME].log files in the specified output folder
    # default=output_file_name,
    # type=str)
    io_args.add_argument('base_output_dir',
                         metavar='Base output directory',
                         help='Local directory generally used to save your outputs',
                         type=str,
                         default=base_output_path,
                         widget='DirChooser')

    elabftw_args = elab_arg_parser.add_argument_group("eLabFTW Arguments", gooey_options={'columns': 2})
    elabftw_args.add_argument('exp_no',
                              metavar='eLabFTW experiment ID',
                              help='Integer indicated in the URL of the experiment',
                              default=exp_no,
                              type=int)
    elabftw_args.add_argument('endpoint',
                              metavar="eLabFTW API endpoint URL",
                              help='Ask your eLabFTW admin to provide the endpoint URL for you',
                              default=endpoint,
                              type=str)
    elabftw_args.add_argument('token',
                              metavar='eLabFTW API Token',
                              help='Ask your eLabFTW admin to generate an API token for you',
                              default=token,
                              # Ask your eLabFTW admin to instance to generate one for you
                              type=str)

    # ELABFTW DATABASE PARAMETERS
    # elabftw_args = parser.add_argument_group("eLabFTW Arguments")
    elab_arg_parser = subs.add_parser('parse_database', prog="Parse Container",
                                      help='Parse metadata from an eLabFTW database/container items')

    io_args = elab_arg_parser.add_argument_group("Input/Output Arguments", gooey_options={'columns': 1})
    radio_group = io_args.add_mutually_exclusive_group(required=True, gooey_options={
        'title': "Naming method for the outputs", 'initial_selection': 0})
    radio_group.add_argument("-t", "--title", metavar="Title", action="store_true",
                             help='Name files and folders based on container type + title, including the underlying experiments')
    radio_group.add_argument("-i", "--id", metavar="ID", action="store_true",
                             help='Name files and folders based on container type + ID, including the underlying experiments')
    io_args.add_argument('base_output_dir',
                         metavar='Base output directory',
                         help='Local directory generally used to save your outputs',
                         type=str,
                         default=base_output_path,
                         widget='DirChooser')

    elabftw_args = elab_arg_parser.add_argument_group("eLabFTW Arguments", gooey_options={'columns': 2})
    elabftw_args.add_argument('db_item_no',
                              metavar='eLabFTW Database/Container Item ID',
                              help='Integer indicated in the URL of the database/container item',
                              # default=db_item_no,
                              default=db_item_no,
                              type=int)
    elabftw_args.add_argument('endpoint',
                              metavar="eLabFTW API endpoint URL",
                              help='Ask your eLabFTW admin to provide the endpoint URL for you',
                              default=endpoint,
                              type=str)
    elabftw_args.add_argument('token',
                              metavar='eLabFTW API Token',
                              help='Ask your eLabFTW admin to generate an API token for you',
                              default=token,
                              # Ask your eLabFTW admin to instance to generate one for you
                              type=str)

    args = parser.parse_args()
    return args


def get_db_cat_and_title(endpoint: str, token: str, db_item_no: int) -> Tuple[str, str]:
    manager = create_elab_manager(endpoint, token)
    db_item = manager.get_item(db_item_no)
    if db_item is None:
        raise ValueError("Failed to retrieve database item")
    category = db_item.get("category")
    title = db_item.get("title")
    if category is None or title is None:
        raise ValueError("Invalid database category/title format")
    return category, title


def get_exp_title(endpoint: str, token: str, exp_item_no: int) -> str:
    exp = get_elab_exp(exp_item_no, endpoint, token)
    if exp is None:
        raise ValueError("Failed to retrieve experiment entry")
    exp_title = exp[1]["title"]
    return exp_title


# ------------------------------------------------ MAIN FUNCTION ------------------------------------------------------
ref_counter = 0


def main():
    global output_fname  # , input_file
    global output_path, base_output_path
    global token, exp_no, endpoint
    # global log

    # sys.stdin.reconfigure(encoding='utf-8')
    # sys.stdout.reconfigure(encoding='utf-8')

    log = ""

    args = parse_gooey_args()
    base_output_path = args.base_output_dir
    if args.command == 'parse_database':
        cat, title = get_db_cat_and_title(args.endpoint, args.token, args.db_item_no)
        if args.id:
            output_fname = slugify(cat) + "_" + str(args.db_item_no)
        elif args.title:
            output_fname = slugify(cat) + "_" + slugify(title)
    elif args.command == 'parse_experiment':
        if args.id:
            output_fname = slugify("experiment") + "_" + str(args.exp_no)
        elif args.title:
            title = get_exp_title(args.endpoint, args.token, args.exp_no)
            output_fname = slugify("experiment") + "_" + slugify(title)
    print("The output is written to %s directory" % (output_fname))

    output_path = manage_output_path(args.base_output_dir, output_fname)
    check_and_create_path(output_path)

    print("base_output_dir: ", (base_output_path))
    print("output_fname: ", (output_fname))
    print("output_path: ", (output_path))

    if args.command == 'parse_experiment':
        print("Processing experiment...")
        process_experiment(args.exp_no, args.endpoint, args.token, output_path)
    elif args.command == 'parse_database':
        process_ref_db_item(args.db_item_no, args.endpoint, args.token, args.id, args.title)


if __name__ == "__main__":
    main()
