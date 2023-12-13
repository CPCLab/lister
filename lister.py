import json
import re
from enum import Enum
import xlsxwriter
from docx import Document
from bs4 import BeautifulSoup, Tag
# import elabapy
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
from typing import Any, Tuple, List, Dict, Union
from argparse import Namespace
from elabapi_python.rest import ApiException
from pprint import pprint
import urllib3
import warnings
from multiprocessing import freeze_support

# TODO: remove the following line when the issue is fixed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# -------------------------------- CLASSES TO HANDLE ENUMERATED CONCEPTS --------------------------------
# Control Flow Metadata Types
class CFMetadata(Enum):
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


class BracketPairErrorMsg(Enum):
    IMPROPER_COMMENT_BRACKET = "ERROR: Mismatch between '(' and ')'. Check line "
    IMPROPER_RANGE_BRACKET = "ERROR: Mismatch between '[' and ']'.  Check line "
    IMPROPER_KV_BRACKET = "ERROR: Mismatch between '{' and '}'.  Check line "
    IMPROPER_FLOW_BRACKET = "ERROR: Mismatch between '<' and '>'.  Check line "


class MiscAlertMsg(Enum):
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
    ITRTN_OPERATION_NOT_EXIST = "ERROR: The iteration operation is not found, please check the following part: {0}."
    MAGNITUDE_NOT_EXIST = "ERROR: The magnitude of the iteration flow is not found, please check the following part: {0}."
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


class RegexPatterns(Enum):
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


class ArgNum(Enum):
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



# -------------------------------------------- API Access-related Class -----------------------------------------------
class ApiAccess:

    @classmethod
    def get_resource_item(self, apiv2client: elabapi_python.api_client, resource_id: int) -> elabapi_python.Item:
        """
        Get an item from eLabFTW using the resourece  item ID and API v2 client.

        :param apiv2client: The API v2 client.
        :param resource_id: The item ID.
        :return: The item (resource) content.
        """
        api_instance = elabapi_python.ItemsApi(apiv2client)
        try:
            api_item_response = api_instance.get_item(resource_id, format='json')
        except ApiException as e:
            print("Exception when calling ItemsApi->get_item: %s\n" % e)
        return api_item_response

    @classmethod
    def get_attachment_long_name(cls, img_path: str) -> str:
        """
        Get upload long name from the img path.

        :param img_path: The path of the image.
        :type img_path: str
        :return: The long name of the upload.
        :rtype: str

        This method splits the image path by the separators '&' and '='.
        It then returns the second element of the split path, which corresponds
        to the randomly-assigned long name used to access via the URI.
        """
        splitted_path = GeneralHelper.split_by_separators(img_path, ('&', '='))
        return (splitted_path[1])  # strip first 19 chars to get the long_name field in the upload dictionary


    @classmethod
    def get_exp_title(self, apiv2client, exp_item_no: int) -> str:
        """
        Get the title of an experiment from eLabFTW using apiv2client object the experiment item number.

        :param apiv2client: eLabFTW API v2 client object
        :param int exp_item_no: eLabFTW experiment item number
        :return: Experiment title as a string
        """
        exp = self.get_exp(apiv2client, exp_item_no)
        if exp is None:
            raise ValueError("Failed to retrieve experiment entry")
        exp_title = exp.__dict__["_title"]
        return exp_title


    @classmethod
    def get_exp_info(self, exp: dict) -> List[List[str]]:
        """
        Get experiment information and return it as a list of lists.

        :param exp: An eLabFTW API's Experiment object containing experiment information.
        :return: A list of lists containing experiment information in the form of par.no-key-value-measure-units.
        """
        nkvmu_pairs = []
        nkvmu_pairs.append(["", "metadata section", "Experiment Info", "", ""])
        nkvmu_pairs.append(["", "title", exp.__dict__["_title"], "", ""])
        nkvmu_pairs.append(["", "creation date", exp.__dict__["_created_at"], "", ""])
        nkvmu_pairs.append(["", "category", exp.__dict__["_type"], "", ""])
        nkvmu_pairs.append(["", "author", exp.__dict__["_fullname"], "", ""])
        nkvmu_pairs.append(["", "tags", exp.__dict__["_tags"], "", ""])
        return nkvmu_pairs


    @classmethod
    def get_exp(self, apiv2client: elabapi_python.ApiClient, id: int) -> elabapi_python.Experiment:
        """
        Get an eLab experiment using the provided API client and experiment ID.

        :param elabapi_python.ApiClient apiv2client: The eLab API client instance.
        :param int id: The ID of the experiment to retrieve.
        :return: elabapi_python.Experiment exp_response: The retrieved eLab experiment.

        This method uses the provided eLab API client to fetch an experiment with the given ID.
        If an ApiException occurs, it prints the exception message and continues.
        """
        api_instance = elabapi_python.ExperimentsApi(apiv2client)
        try:
            exp_response = api_instance.get_experiment(id, format='json')
        except ApiException as e:
            print("Exception when calling ExperimentsApi->getExperiment: %s\n" % e)
        return exp_response


    @classmethod
    def get_attachment_id(self, exp: Dict, content: Tag) -> Tuple[str, str]:
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
        upl_long_name = self.get_attachment_long_name(img_path)
        uploads = exp.__dict__['_uploads']
        if len(uploads) > 0:
            try:
                matched_upl = next(upload for upload in uploads if upload.__dict__['_long_name'] == upl_long_name)
                upl_id = matched_upl.__dict__['_id']
                real_name = matched_upl.__dict__['_real_name']
            except Exception as e:
                log = MiscAlertMsg.INACCESSIBLE_ATTACHMENT.value.format("NULL", str(e))
                upl_id = ""
                real_name = ""
                print(log)
                print("Attachment download is skipped...")
                pass
        else:
            upl_id = ""
            real_name = ""
        return upl_id, real_name


    @classmethod
    def get_apiv2endpoint(self, apiv1endpoint: str) -> str:
        '''
        Convert a version 1 API endpoint to a version 2 API endpoint.

        :param str apiv1endpoint: version 1 API endpoint.
        :return: str v2endpoint: version 2 API endpoint.
        '''
        v2endpoint = re.sub(r'http://', 'https://', apiv1endpoint)
        v2endpoint = re.sub(r'/v1', '/v2', v2endpoint)
        return v2endpoint


    @classmethod
    def create_apiv2client(self, endpoint: str, token: str) -> elabapi_python.ApiClient:
        """
        Create an API v2 client with the given endpoint and token.

        :param endpoint: The API endpoint.
        :param token: The API token.
        :return: The API v2 client.
        :rtype: elabapi_python.ApiClient.
        """
        endpoint_v2 = self.get_apiv2endpoint(endpoint)
        apiv2config = elabapi_python.Configuration()
        apiv2config.api_key['api_key'] = token
        apiv2config.api_key_prefix['api_key'] = 'Authorization'
        apiv2config.host = endpoint_v2
        apiv2config.debug = False
        apiv2config.verify_ssl = False
        apiv2_client = elabapi_python.ApiClient(apiv2config)
        apiv2_client.set_default_header(header_name='Authorization', header_value=token)
        return apiv2_client


    @classmethod
    def get_save_attachments(self, path: str, apiv2client: elabapi_python.ApiClient, exp_id: int) -> str:
        '''
        Get a list of attachments in the experiment entry and download these attachments, and return the logs as string.

        :param str path: the path for downloading the attached files, typically named based on experiment title or ID.
        :param elabapi_python.ApiClient apiv2client: The API v2 client object.
        :param int exp_id: The experiment ID.

        :return log:  The log as a string.
        '''

        log = ""

        experimentsApi = elabapi_python.ExperimentsApi(apiv2client)
        uploadsApi = elabapi_python.UploadsApi(apiv2client)
        exp = experimentsApi.get_experiment(int(exp_id))

        upload_saving_path = path + '/' + 'attachments'
        sanitized_upload_saving_path = sanitize_filepath(upload_saving_path, platform='auto')
        PathHelper.check_and_create_path(sanitized_upload_saving_path)

        for upload in uploadsApi.read_uploads('experiments', exp.id):
            with open(sanitized_upload_saving_path + "/" + upload.real_name, 'wb') as file:
                print("Attachment found: ID: {0}, with name {1}. Writing to {2}.".format(str(upload.id), upload.real_name,
                                                                                         upload_saving_path + "/" + upload.real_name))
                file.write(
                    uploadsApi.read_upload('experiments', exp.id, upload.id, format='binary', _preload_content=False).data)
                file.flush()
        return log


# ------------------------------------------------ GUI Helper Class ----------------------------------------------------
class GUIHelper:

    @Gooey(optional_cols=0, program_name="LISTER: Life Science Experiment Metadata Parser", default_size=(753, 753),
           navigation="TABBED")
    def parse_gooey_args(self) -> Namespace:
        """
        Get arguments from an existing JSON config to be passed to Gooey's interface.
        Manual debugging (i.e., printout) is necessary when Gooey is used.

        :returns: args WHERE argparse.Namespace args is an object containing several attributes:
        - str command (e.g., eLabFTW),
        - str output_file_name,
        - int exp_no,
        - str endpoint,
        - str base_output_dir,
        - str token,
        - bool uploadToggle.
        """
        token, endpoint, output_file_name, exp_no, resource_item_no = self.parse_cfg()
        settings_msg = 'Please ensure to enter the fields below properly, or ask your eLabFTW admin if you have questions.'
        parser = GooeyParser(description=settings_msg)
        subs = parser.add_subparsers(help='commands', dest='command')
        base_output_path = PathHelper.get_default_output_path(output_file_name)

        # ELABFTW EXPERIMENT PARAMETERS
        elab_arg_parser = subs.add_parser('parse_experiment', prog="Parse Experiment",
                                          help='Parse metadata from an eLabFTW experiment entry')
        io_args = elab_arg_parser.add_argument_group("Input/Output Arguments", gooey_options={'columns': 1})
        radio_group = io_args.add_mutually_exclusive_group(required=True,
                                                           gooey_options={'title': "Naming method for the outputs",
                                                                          'initial_selection': 0})
        radio_group.add_argument("-t", "--title", metavar="Title", action="store_true",
                                 help='Name files and folders based on experiment title')
        radio_group.add_argument("-i", "--id", metavar="ID", action="store_true",
                                 help='Name files and folders based on the experiment ID')

        io_args.add_argument('base_output_dir', metavar='Base output directory',
                             help='Local directory generally used to save your outputs', type=str,
                             default=base_output_path, widget='DirChooser')
        elabftw_args = elab_arg_parser.add_argument_group("eLabFTW Arguments", gooey_options={'columns': 2})
        elabftw_args.add_argument('exp_no', metavar='eLabFTW experiment ID',
                                  help='Integer indicated in the URL of the experiment', default=exp_no, type=int)
        elabftw_args.add_argument('endpoint', metavar="eLabFTW API endpoint URL",
                                  help='Ask your eLabFTW admin to provide the endpoint URL for you', default=endpoint,
                                  type=str)
        elabftw_args.add_argument('token', metavar='eLabFTW API Token',
                                  help='Ask your eLabFTW admin to generate an API token for you', default=token,
                                  type=str)

        # ELABFTW resource PARAMETERS
        elab_arg_parser = subs.add_parser('parse_resource', prog="Parse Container",
                                          help='Parse metadata from an eLabFTW resource/container items')
        io_args = elab_arg_parser.add_argument_group("Input/Output Arguments", gooey_options={'columns': 1})
        radio_group = io_args.add_mutually_exclusive_group(required=True,
                                                           gooey_options={'title': "Naming method for the outputs",
                                                                          'initial_selection': 0})
        radio_group.add_argument("-t", "--title", metavar="Title", action="store_true",
                                 help='Name files and folders based on container type + title, including the underlying experiments')
        radio_group.add_argument("-i", "--id", metavar="ID", action="store_true",
                                 help='Name files and folders based on container type + ID, including the underlying experiments')

        io_args.add_argument('base_output_dir', metavar='Base output directory',
                             help='Local directory generally used to save your outputs', type=str,
                             default=base_output_path, widget='DirChooser')
        elabftw_args = elab_arg_parser.add_argument_group("eLabFTW Arguments", gooey_options={'columns': 2})
        elabftw_args.add_argument('resource_item_no', metavar='eLabFTW Resource/Container Item ID',
                                  help='Integer indicated in the URL of the resource/container item',
                                  default=resource_item_no, type=int)
        elabftw_args.add_argument('endpoint', metavar="eLabFTW API endpoint URL",
                                  help='Ask your eLabFTW admin to provide the endpoint URL for you', default=endpoint,
                                  type=str)
        elabftw_args.add_argument('token', metavar='eLabFTW API Token',
                                  help='Ask your eLabFTW admin to generate an API token for you', default=token,
                                  type=str)

        args = parser.parse_args()
        return args

    @classmethod
    def parse_cfg(self) -> Tuple[str, str, str, int, int]:
        '''
        Parse JSON config file, requires existing config.json file which should be specified on certain directory.

        The directory is OS-dependent. On Windows/Linux, it is in the same folder as the script/executables.
        On macOS, it is in the users' Apps/lister/config.json file.

        :returns: tuple (token, endpoint, output_file_name, exp_no)
            str token: eLabFTW API Token,
            str endpoint: eLabFTW API endpoint URL,
            str output_file_name: filename to be used for all the outputs (xlsx/json metadata, docx documentation, log file),
            int exp_no: the parsed experiment ID (int).
            int resource_item_no: the parsed resource/container item ID (int).
        '''

        input_file = PathHelper.manage_input_path() + "config.json"
        print("CONFIG FILE: %s" % (input_file))
        # using ...with open... allows file to be closed automatically.
        with open(input_file, encoding="utf-8") as json_data_file:
            data = json.load(json_data_file)
        token = data['elabftw']['token']
        endpoint = data['elabftw']['endpoint']
        exp_no = data['elabftw']['exp_no']
        output_file_name = data['elabftw']['output_file_name']
        resource_item_no = data['elabftw']['resource_item_no']
        return token, endpoint, output_file_name, exp_no, resource_item_no


# -------------------------------------------- File serialization Class ------------------------------------------------

class Serializer:

    @classmethod
    def write_to_docx(self, exp: dict, path: str) -> str:
        '''
        fetch an experiment, clean the content from LISTER annotation markup and serialize the result to a docx file.

        :param dict exp: dictionary containing the properties of the experiment, including its HTML body content.
        :param str path: the path for writing the docx file, typically named based on experiment title or ID.

        :return: str log: log of the process.
        '''

        document = Document()
        all_references = []
        tagged_contents = TextCleaner.get_nonempty_body_tags(exp)
        watched_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'strong', 'sub', 'em', 'sup']
        for content in tagged_contents:  # iterate over list of tags
            if isinstance(content, Tag):
                if len(content.select("img")) > 0:
                    upl_id, real_name = ApiAccess.get_attachment_id(exp, content)
                    DocxHelper.add_img_to_doc(document, real_name, path)
                elif any(x in content.name for x in watched_tags):
                    references, log = DocxHelper.write_tag_to_doc(document, content)
                    if len(references) > 0:
                        all_references.extend(references)
                if content.name == "table":
                    print("A table is found, writing to docx...")
                    DocxHelper.add_table_to_doc(document, content)
                if content.name == "img":
                    print("An image is found, serializing to docx...")
                    upl_id, real_name = ApiAccess.get_attachment_id(exp, content)
                    DocxHelper.add_img_to_doc(document, real_name, path)

        if len(all_references) > 0:
            document.add_heading("Reference", level=1)
            for reference in all_references:
                document.add_paragraph(reference, style='List Number')
        document.save(path + '/' + PathHelper.derive_fname_from_exp(exp) + '.docx')


    # Used to serialize extracted metadata to json file.
    @classmethod
    def write_to_json(self, lst: List, exp: dict, path: str) -> None:
        """
        Write a list to a JSON file.
        :param lst: The list to write to the JSON file.
        :param exp: The experiment title or ID.
        :param path: The path for writing the JSON file.
        """
        filename = f"{PathHelper.derive_fname_from_exp(exp)}.json"
        with open(f"{path}/{filename}", "w", encoding="utf-8") as f:
            json.dump(lst, f, ensure_ascii=False)


    # Used to write into the log file.
    # def write_log(log, full_path=output_path_and_fname):
    @classmethod
    def write_log(self, log_text: str, path: str) -> None:
        """
        Write the log to a file.
        :param log_text: The log to be written to the file.
        :param path: The path for writing the log file.
        """
        log_text = log_text.strip()
        PathHelper.check_and_create_path(path)
        with open(f"{path}/lister-report.log", "w", encoding="utf-8") as f:
            f.write(log_text)


    @classmethod
    def write_to_xlsx(self, nkvmu: List, exp: dict, path: str) -> None:
        '''
        Write extracted order/key/value/measure/unit to an Excel file.

        :param list nkvmu: list containing the order (paragraph number)/key/value/measure/unit to be written.
        :param dict exp: experiment object.
        :param str path: the path for writing the xlsx file, typically named based on experiment title or ID.
        '''
        PathHelper.check_and_create_path(path)
        header = ["PARAGRAPH NUMBER", "KEY", "VALUE", "MEASURE", "UNIT"]
        # json.dump(list, open(path + '/' + derive_fname_from_exp(exp) + ".json", 'w', encoding="utf-8"), ensure_ascii=False)
        # with xlsxwriter.Workbook(path + output_fname + ".xlsx") as workbook:
        with xlsxwriter.Workbook(path + '/' + PathHelper.derive_fname_from_exp(exp) + ".xlsx") as workbook:
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
                # if re.match(RegexPatterns.SUBSECTION.value, data[1].lower()):
                if len(key) >= 7 and key[
                                     0:7].casefold() == "section".casefold() or key.casefold() == "metadata section":
                    worksheet.write_row(row_no + 1, 0, data, section_format)
                else:
                    worksheet.write_row(row_no + 1, 0, data, default_format)


# ---------------------------------------------- Metadata Extraction Class --------------------------------------------
class MetadataExtractor:

    @classmethod
    def is_explicit_key(self, key: str) -> bool:
        '''
        Check whether the string is an explicit key.

        :param str key: checked string.
        :return: bool stating whether the key is a LISTER explicit key.

        '''
        if re.match(RegexPatterns.EXPLICIT_KEY.value, key):
            return True
        else:
            return False


    @classmethod
    def extract_flow_type(self, par_no: int, flow_control_pair: str) -> Tuple[List[List], str, bool]:
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
        # print("flow_control_pair: " + str(flow_control_pair))
        is_error = False
        key_val = []
        cf = flow_control_pair[1:-1]
        cf_split = re.split("\|", cf)
        flow_type = cf_split[0]
        flow_type = flow_type.strip()
        flow_type = flow_type.lower()
        if flow_type == "for each":
            key_val, log, is_error = self.process_foreach(par_no, cf_split)
            if log != "":
                flow_log = flow_log + "\n" + log
        elif flow_type == "while":
            key_val, log, is_error = self.process_while(par_no, cf_split)
            if log != "":
                flow_log = flow_log + "\n" + log
        elif flow_type == "if":
            key_val, log, is_error = self.process_if(par_no, cf_split)
            if log != "":
                flow_log = flow_log + "\n" + log
        elif flow_type == "else if" or flow_type == "elif":
            key_val, log, is_error = self.process_elseif(par_no, cf_split)
            if log != "":
                flow_log = flow_log + "\n" + log
        elif flow_type == "else":
            key_val, log, is_error = self.process_else(par_no, cf_split)
            if log != "":
                flow_log = flow_log + "\n" + log
        elif flow_type == "for":
            key_val, log, is_error = self.process_for(par_no, cf_split)
            if log != "":
                flow_log = flow_log + "\n" + log
        # elif flow_type.casefold() == "section".casefold():
        elif re.match(RegexPatterns.SUBSECTION.value, flow_type, flags=re.IGNORECASE):
            key_val, log, is_error = self.process_section(cf_split)
            if log != "":
                flow_log = flow_log + "\n" + log
        elif flow_type == "iterate":
            key_val, log, is_error = self.process_iterate(par_no, cf_split)
            if log != "":
                flow_log = flow_log + "\n" + log
        else:
            is_error = True
            log = MiscAlertMsg.UNRECOGNIZED_FLOW_TYPE.value.format(cf_split[0].upper(), cf_split) + "\n"
            flow_log = flow_log + "\n" + log
            print(flow_log)
        # print("key_val: " + str(key_val) + "\n\n")
        return key_val, flow_log, is_error


    @classmethod
    def process_section(self, cf_split: List[str]) -> Tuple[List[List], str, bool]:
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
        log, is_sect_error = Validator.validate_section(cf_split)
        if is_sect_error:
            is_error = True
            section_log = section_log + "\n" + log
            exit()
        else:
            section_keyword = cf_split[0].lower()
            section_level = section_keyword.count("sub")
            key_val.append(
                ["-", CFMetadata.FLOW_SECTION.value + " level " + str(section_level), cf_split[1], '', ''])
        return key_val, section_log, is_error


    @classmethod
    def process_ref_resource_item(self, apiv2client: elabapi_python.ApiClient, item_api_response) -> None:
        '''
        Process reference resource item, using the initial resource ID for that container item (e.g., publication).

        :param apiv2client: An instance of the API v2 client object, containing eLabFTW API-related information.
        :param item_api_response: The API response of the reference resource item.
        :return: None
        '''

        # TODO: also get the list of related experiments instead of linked experiments only,
        #  status: pending. see https://github.com/elabftw/elabftw/issues/4811
        try:
            experiments = item_api_response.__dict__["_experiments_links"]
            for experiment in experiments:
                exp_path = output_path + PathHelper.slugify(experiment.__dict__["_title"])
                self.process_experiment(apiv2client, experiment.__dict__["_itemid"], exp_path)
        except ApiException as e:
            print("Exception when calling ItemsApi->getItem: %s\n" % e)


    @classmethod
    def process_linked_resource_item_apiv2(self, apiv2client: elabapi_python.ApiClient, id: int) -> (
            Tuple)[Union[List[List[str]], str], str]:
        """
        Process a linked resource item and return its metadata and log.

        :param elabapi_python.ApiClient apiv2client: An instance of the API v2 client object, containing eLabFTW
        API-related information.
        :param id: The ID of the linked resource item.
        :return: A tuple containing the resource item metadata and log.
        """
        api_instance = elabapi_python.ItemsApi(apiv2client)

        try:
            # Read an item
            linked_item = api_instance.get_item(id)
            html_body = getattr(linked_item, 'body')
            # category = getattr(linked_item, 'mainattr_title') # only works for elabapi-python 0.4.1.
            category = getattr(linked_item, 'category_title')

            dfs = pd.read_html(html_body)
            df = pd.concat(dfs)
            df_col_no = df.shape[1]
            log = ""
            if df_col_no != 2:
                log = MiscAlertMsg.NON_TWO_COLS_LINKED_TABLE.value.format(category, df_col_no) + "\n"
                print(log)
                resource_item_nkvmu_metadata = ""
                pass
            else:
                df.columns = ["metadata section", category]
                df.insert(loc=0, column="", value="")
                df = df.reindex(df.columns.tolist() + ['', ''], axis=1)  # add two empty columns
                filtered_df = df.fillna('')  # fill empty cells with empty string
                resource_item_nkvmu_metadata = [filtered_df.columns.values.tolist()] + filtered_df.values.tolist()
        except ApiException as e:
            log = "Exception when calling ItemsApi->getItem: %s\n" % e
            print(log)
        return resource_item_nkvmu_metadata, log


    @classmethod
    def process_experiment(self, apiv2client: elabapi_python.ApiClient, exp_no: int, path: str) -> None:
        """
        Process an experiment and save its information to various formats.

        :param elabapi_python.ApiClient apiv2client: The API v2 client.
        :param int exp_no: The experiment number.
        :param str path: The path for saving the output files.
        """
        overall_log = ""

        exp_instance = elabapi_python.ExperimentsApi(apiv2client)
        exp_response = exp_instance.get_experiment(int(exp_no))

        linked_resources = exp_response.__dict__['_items_links']
        # get the IDs of the linked resources
        linked_resource_ids = [linked_resource.__dict__["_itemid"] for linked_resource in linked_resources]

        # get the respective category of the linked resources
        id_and_category = {}
        excluded_item_types = ["MM", "Publication", "Protocols", "Protocol", "Methods", "Method", "Recipe"]

        # this will only work with elabapi-python 0.4.1.
        # unfortunately the response from the API is not consistent between versions, so it may be a good idea to fix
        # the version of elabapi-python to specific version in the requirements.txt in the future.

        #for linked_resource in linked_resources:
            #id_and_category[linked_resource.__dict__["_itemid"]] = linked_resource.__dict__["_mainattr_title"]

        for linked_resource_id in linked_resource_ids:
            # get the linked resource item by ID
            linked_resource = ApiAccess.get_resource_item(apiv2client, linked_resource_id)
            # pprint(linked_resource)
            id_and_category[linked_resource.__dict__["_id"]] = linked_resource.__dict__["_category_title"]
        # pprint(id_and_category)

        filtered_id_and_category =  {key: value for key, value in id_and_category.items() if value.lower() not in
                                     [item.lower() for item in excluded_item_types]}
        # pprint(filtered_id_and_category)

        overall_nkvmu = []
        # the 'key' here is the ID of the resource item.
        for key in filtered_id_and_category:
            resource_item_nkvmu_metadata, log = MetadataExtractor.process_linked_resource_item_apiv2(apiv2client, key)
            overall_log = overall_log + "\n" + log
            overall_nkvmu.extend(resource_item_nkvmu_metadata)

        exp_nkvmu_info_v2 = ApiAccess.get_exp_info(exp_response)
        overall_nkvmu.extend(exp_nkvmu_info_v2)
        exp_nkvmu, log = MetadataExtractor.conv_html_to_metadata(exp_response.__dict__["_body"])
        overall_log = overall_log + "\n" + log
        overall_nkvmu.extend(exp_nkvmu)

        log = ApiAccess.get_save_attachments(path, apiv2client, int(exp_no))
        overall_log = overall_log + "\n" + log
        docx_log = Serializer.write_to_docx(exp_response, path)
        try:
            overall_log = overall_log + "\n" + docx_log
        except:
            pass

        Serializer.write_to_json(overall_nkvmu, exp_response, path)
        Serializer.write_to_xlsx(overall_nkvmu, exp_response, path)
        Serializer.write_log(overall_log, path)


    # only process the comment that is within (key value measure unit) pairs and remove its content
    # (unless if it is begun with "!")
    @classmethod
    def process_internal_comment(self, str_with_brackets: str) -> Tuple[str, str]:
        '''
        Separates actual part of a lister bracket annotation fragment (key/value/measure/unit) with the trailing comments.

        Internal comment refers to any comment that is available within a fragment of a lister bracket annotation.
        Internal comment will not be bypassed to the metadata output.
        However, internal comment is important to be provided to make the experiment clear-text readable in the docx output.

        :param str str_with_brackets: a lister bracket annotation fragment with a comment.
        :returns: tuple (actual_fragment, internal_comment)
            WHERE
            str actual_fragment:  string containing the actual element of metadata, it can be either key/value/measure/unit,
            str internal_comment: string containing the comment part of the string fragment, with brackets retained.
        '''
        comment = re.search(RegexPatterns.COMMENT.value, str_with_brackets)
        comment = comment.group(0)
        remains = str_with_brackets.replace(comment, '')
        actual_fragment, internal_comment = remains.strip(), comment.strip()
        return actual_fragment, internal_comment


    @classmethod
    def process_foreach(self, par_no: int, cf_split: List[str]) -> Tuple[List[List], str, bool]:
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
        log, is_error = Validator.validate_foreach(cf_split)
        if is_error:
            # write_log(log, output_path+output_fname)
            print(log)
            exit()
        step_type = "iteration"
        key_val.append([par_no, CFMetadata.STEP_TYPE.value, step_type, '', ''])
        flow_type = cf_split[0]
        key_val.append([par_no, CFMetadata.FLOW_TYPE.value, flow_type, '', ''])
        flow_param = cf_split[1]
        key_val.append([par_no, CFMetadata.FLOW_PARAM.value, flow_param, '', ''])
        return key_val, log, is_error


    @classmethod
    def process_while(self, par_no: int, cf_split: List[str]) -> Tuple[List[List], str, bool]:
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
        log, is_error = Validator.validate_while(cf_split)
        if is_error:
            # write_log(log, output_path+output_fname)
            print(log)
            exit()
        step_type = "iteration"
        key_val.append([par_no, CFMetadata.STEP_TYPE.value, step_type, '', ''])
        flow_type = cf_split[0]
        key_val.append([par_no, CFMetadata.FLOW_TYPE.value, flow_type, '', ''])
        flow_param = cf_split[1]
        key_val.append([par_no, CFMetadata.FLOW_PARAM.value, flow_param, '', ''])
        flow_logical_operator = cf_split[2]
        key_val.append([par_no, CFMetadata.FLOW_LGCL_OPRTR.value, flow_logical_operator, '', ''])
        flow_compared_value = cf_split[3]
        key_val.append([par_no, CFMetadata.FLOW_CMPRD_VAL.value, flow_compared_value, '', ''])
        return key_val, log, is_error


    @classmethod
    def process_if(self, par_no: int, cf_split: List[str]) -> Tuple[List[List], str, bool]:
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
        log, is_error = Validator.validate_if(cf_split)
        if is_error:
            # write_log(log, output_path+output_fname)
            print(log)
            exit()
        step_type = "conditional"
        key_val.append([par_no, CFMetadata.STEP_TYPE.value, step_type, '', ''])
        flow_type = cf_split[0]
        key_val.append([par_no, CFMetadata.FLOW_TYPE.value, flow_type, '', ''])
        flow_param = cf_split[1]
        key_val.append([par_no, CFMetadata.FLOW_PARAM.value, flow_param, '', ''])
        flow_logical_operator = cf_split[2]
        key_val.append([par_no, CFMetadata.FLOW_LGCL_OPRTR.value, flow_logical_operator, '', ''])
        flow_compared_value = cf_split[3]
        key_val.append([par_no, CFMetadata.FLOW_CMPRD_VAL.value, flow_compared_value, '', ''])
        return key_val, log, is_error


    @classmethod
    def process_elseif(self, par_no: int, cf_split: List[str]) -> Tuple[List[List], str, bool]:
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
        log, is_error = Validator.validate_elseif(cf_split)
        if is_error:
            # write_log(log, output_path+output_fname)
            print(log)
            exit()
        step_type = "conditional"
        key_val.append([par_no, CFMetadata.STEP_TYPE.value, step_type, '', ''])
        flow_type = cf_split[0]
        key_val.append([par_no, CFMetadata.FLOW_TYPE.value, flow_type, '', ''])
        flow_param = cf_split[1]
        key_val.append([par_no, CFMetadata.FLOW_PARAM.value, flow_param, '', ''])
        flow_logical_operator = cf_split[2]
        key_val.append([par_no, CFMetadata.FLOW_LGCL_OPRTR.value, flow_logical_operator, '', ''])
        flow_compared_value = cf_split[3]
        if re.search("\[.*?\]", flow_compared_value):
            key_val.append([par_no, CFMetadata.FLOW_RANGE.value, flow_compared_value, '', ''])
            start, end, range_log, range_is_error = self.process_range(flow_compared_value)
            key_val.append([par_no, CFMetadata.FLOW_ITRTN_STRT.value, start, '', ''])
            key_val.append([par_no, CFMetadata.FLOW_ITRTN_END.value, end, '', ''])
        else:
            key_val.append([par_no, CFMetadata.FLOW_CMPRD_VAL.value, flow_compared_value, '', ''])
        return key_val, log, is_error


    @classmethod
    def process_else(self, par_no: int, cf_split: List[str]) -> Tuple[List[List], str, bool]:
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
        log, is_error = Validator.validate_else(cf_split)
        if is_error:
            # write_log(log, output_path+output_fname)
            print(log)
            exit()
        step_type = "conditional"
        key_val.append([par_no, CFMetadata.STEP_TYPE.value, step_type, '', ''])
        flow_type = cf_split[0]
        key_val.append([par_no, CFMetadata.FLOW_TYPE.value, flow_type, '', ''])
        return key_val, log, is_error

    @classmethod
    def process_range(self, flow_range: str) -> Tuple[float, float, str, bool]:
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
        log, is_error = Validator.validate_range(flow_range)
        if is_error:
            # write_log(log, output_path+output_fname)
            print(log)
            # exit()
        else:
            range_values = re.split("-", flow_range[1:-1])
        return float(range_values[0]), float(range_values[1]), log, is_error


    @classmethod
    def process_for(self, par_no: int, cf_split: List[str]) -> Tuple[List[List], str, bool]:
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
        for_validation_log, is_for_error = Validator.validate_for(cf_split)
        if is_for_error:
            # write_log(log, output_path+output_fname)
            for_log = for_log + "\n" + for_validation_log
            is_error = True
            print(for_validation_log)
            # exit()
        step_type = "iteration"
        key_val.append([par_no, CFMetadata.STEP_TYPE.value, step_type, '', ''])
        flow_type = cf_split[0]
        key_val.append([par_no, CFMetadata.FLOW_TYPE.value, flow_type, '', ''])
        flow_param = cf_split[1]
        key_val.append([par_no, CFMetadata.FLOW_PARAM.value, flow_param, '', ''])
        flow_range = cf_split[2]
        key_val.append([par_no, CFMetadata.FLOW_RANGE.value, flow_range, '', ''])
        start, end, range_log, is_range_error = self.process_range(flow_range)
        if is_range_error:
            for_log = for_log + "\n" + range_log
            print(range_log)
            is_error = True
        key_val.append([par_no, CFMetadata.FLOW_ITRTN_STRT.value, start, '', ''])
        key_val.append([par_no, CFMetadata.FLOW_ITRTN_END.value, end, '', ''])
        try:
            flow_operation = cf_split[3]
            key_val.append([par_no, CFMetadata.FLOW_OPRTN.value, flow_operation, '', ''])
        except:
            is_error = True
            print(MiscAlertMsg.ITRTN_OPERATION_NOT_EXIST.value.format(cf_split))
            for_log = for_log + "\n" + MiscAlertMsg.ITRTN_OPERATION_NOT_EXIST.value.format(cf_split)
        try:
            flow_magnitude = cf_split[4]
            key_val.append([par_no, CFMetadata.FLOW_MGNTD.value, flow_magnitude, '', ''])
        except:
            is_error = True
            print(MiscAlertMsg.MAGNITUDE_NOT_EXIST.value.format(cf_split))
            for_log = for_log + "\n" + MiscAlertMsg.MAGNITUDE_NOT_EXIST.value.format(cf_split)
        return key_val, for_log, is_error


    # should happen only after having 'while' iterations to provide additional steps on the iterator
    @classmethod
    def process_iterate(self, par_no: int, cf_split: List[str]) -> Tuple[List[List], str, bool]:
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
        log, is_error = Validator.validate_iterate(cf_split)
        if is_error:
            iterate_log = iterate_log + "\n" + log
            # write_log(log, output_path+output_fname)
            print(iterate_log)
            # exit()
        flow_type = cf_split[0]
        key_val.append([par_no, CFMetadata.FLOW_TYPE.value, flow_type + "  (after while)"])
        flow_operation = cf_split[1]
        key_val.append([par_no, CFMetadata.FLOW_OPRTN.value, flow_operation])
        try:
            flow_magnitude = cf_split[2]
            key_val.append([par_no, CFMetadata.FLOW_MGNTD.value, flow_magnitude])
        except:
            is_error = True
            print(MiscAlertMsg.MAGNITUDE_NOT_EXIST.value.format(cf_split))
            iterate_log = iterate_log + "\n" + MiscAlertMsg.MAGNITUDE_NOT_EXIST.value.format(cf_split)
        return key_val, iterate_log, is_error


    @classmethod
    def parse_lines_to_metadata(self, lines: List[str]) -> Tuple[List, List[str], str]:
        '''
        Get a list of metadata pairs [order, key, value, measure, unit] or ['-', sec. level, section name, '', ''] from nbsp-clean lines.
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
            bracketing_log, is_bracket_error = Validator.check_bracket_num(par_no, line)
            log = log + bracketing_log  # + "\n"
            if is_bracket_error:
                # write_log(log, output_path+output_fname)
                break

            # Extract KV and flow metadata
            kv_and_flow_pairs = re.findall(RegexPatterns.KV_OR_FLOW.value, line)
            para_len = len(GeneralHelper.split_into_sentences(line))
            if para_len > 0:
                par_no = par_no + 1  # count paragraph index, starting from 1 only if it consists at least a sentence
            for kv_and_flow_pair in kv_and_flow_pairs:
                if re.match(RegexPatterns.KV.value, kv_and_flow_pair):
                    kvmu_set = self.conv_bracketedstring_to_metadata(kv_and_flow_pair)  # returns tuple with key, value, measure, unit, log
                    # measure, unit, log could be empty
                    if kvmu_set[4] != "":
                        log = log + "\n" + kvmu_set[4]
                    if kvmu_set[0] != "" and kvmu_set[1] != "":
                        if re.search(RegexPatterns.COMMENT.value, kvmu_set[0]):
                            key, comment = self.process_internal_comment(kvmu_set[0])
                            internal_comments.append(comment)
                        else:
                            key = kvmu_set[0]
                        if re.search(RegexPatterns.COMMENT.value, kvmu_set[1]):
                            val, comment = self.process_internal_comment(kvmu_set[1])
                            internal_comments.append(comment)
                        else:
                            val = kvmu_set[1]
                        if re.search(RegexPatterns.COMMENT.value, kvmu_set[2]):
                            measure, comment = self.process_internal_comment(kvmu_set[2])
                            internal_comments.append(comment)
                        else:
                            measure = kvmu_set[2]
                        if re.search(RegexPatterns.COMMENT.value, kvmu_set[3]):
                            unit, comment = self.process_internal_comment(kvmu_set[3])
                            internal_comments.append(comment)
                        else:
                            unit = kvmu_set[3]
                        nk_pair = [par_no, key]
                        if (nk_pair in nk_pairs):
                            log = log + MiscAlertMsg.SIMILAR_PAR_KEY_FOUND.value.format(nk_pair) + "\n"
                        if self.is_explicit_key(key):
                            key = TextCleaner.strip_colon(key)
                        nkvmu_pair = [par_no, key, val, measure, unit]
                        nk_pairs.append(nk_pair)
                        nkvmu_pairs.append(nkvmu_pair)
                if re.match(RegexPatterns.FLOW.value, kv_and_flow_pair):
                    flow_metadata, flow_log, is_flow_error = self.extract_flow_type(par_no, kv_and_flow_pair)
                    log = log + flow_log  # + "\n"
                    if is_flow_error:
                        # write_log(log, output_path+output_fname)
                        break
                    nkvmu_pairs.extend(flow_metadata)
        print(log)
        return nkvmu_pairs, internal_comments, log


    # parse opened document, first draft of sop
    @classmethod
    def conv_bracketedstring_to_metadata(self, bracketed_str: str) -> Tuple[str, str, str, str, str]:
        '''
        Extract lines to a tuple containing key, value, measure, and log.

        :param str bracketed_str: a string fragment with a single lister bracketing annotation.
        :returns: tuple (key, val, measure, unit, log)
            WHERE
            str key: the key portion of the string fragment,
            str val: the val portion of the string fragment,
            str measure: the measure portion of the string fragment,
            str unit: the unit portion of the string fragment,
            str log: log resulted from executing this and underlying functions.
        '''
        log = ""
        bracketed_str_source = bracketed_str
        bracketed_str = bracketed_str[1:-1]
        splitted_metadata = re.split("\|", bracketed_str)
        if len(splitted_metadata) == 2:
            key = splitted_metadata[1]
            val = TextCleaner.strip_unwanted_mvu_colons(splitted_metadata[0]) # mvu: measure, value, unit
            measure = ""
            unit = ""
        elif len(splitted_metadata) == 3:
            val = TextCleaner.strip_unwanted_mvu_colons(splitted_metadata[0])
            unit = TextCleaner.strip_unwanted_mvu_colons(splitted_metadata[1])
            key = splitted_metadata[2]
            measure = ""
        elif len(splitted_metadata) == 4:
            measure = TextCleaner.strip_unwanted_mvu_colons(splitted_metadata[0])
            unit = TextCleaner.strip_unwanted_mvu_colons(splitted_metadata[1])
            key = splitted_metadata[3]
            val = TextCleaner.strip_unwanted_mvu_colons(splitted_metadata[2])
        elif len(splitted_metadata) == 1:
            key = ""
            val = ""
            measure = ""
            unit = ""
            print(MiscAlertMsg.SINGLE_PAIRED_BRACKET.value.format(bracketed_str_source))
            log = MiscAlertMsg.SINGLE_PAIRED_BRACKET.value.format(bracketed_str_source)
        else:
            log = MiscAlertMsg.INVALID_KV_SET_ELEMENT_NO.value.format(len(splitted_metadata), str(bracketed_str_source))
            raise SystemExit(log)
        key = key.strip()
        val = val.strip()
        measure = measure.strip()
        unit = unit.strip()
        return key, val, measure, unit, log


    @classmethod
    def conv_html_to_metadata(self, html_content: str) -> Tuple[List, str]:
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
        soup = BeautifulSoup(html_content.encode("utf-8"), "html.parser", from_encoding="found_encoding")
        soup.encoding = "utf-8"
        soup = TextCleaner.remove_table_tag(soup)

        detected_encoding = soup.encoding
        print("Detected encoding:", detected_encoding)
        clean_lines = TextCleaner.process_nbsp(soup)
        if clean_lines is not None:
            multi_nkvmu_pair, internal_comments, log = MetadataExtractor.parse_lines_to_metadata(clean_lines)
        return multi_nkvmu_pair, log


class Validator:

    @classmethod
    def get_nonempty_body_tags(self, exp: BeautifulSoup) -> List:
        '''
        Clean up the source-html from empty-content html tags.

        :param bs4.soup exp: beautifulSoup4.soup experiment object.
        :return: list tagged_contents: list of non-empty html tags as well as new lines.
        '''
        html_body = exp["body"]
        soup = BeautifulSoup(html_body.encode("utf-8"), "html.parser")
        soup.encoding = "utf-8"

        non_empty_soup = TextCleaner.remove_empty_tags(soup)
        tagged_contents = non_empty_soup.currentTag.tagStack[0].contents
        return tagged_contents


    @classmethod
    def check_bracket_num(self, par_no: int, text: str) -> Tuple[str, bool]:
        '''
        Check if there is any bracketing error over the text line

        :param int par_no: paragraph number for the referred line
        :param str text: string of the line
        :return: tuple (log, is_error)
            WHERE
            str log: error log (if any)
            bool is_error: flag if the checked line contains bracketing error
        '''
        log = ""
        base_error_warning = "BRACKET ERROR: %s %s: %s"
        is_error = False
        if text.count("{") != text.count("}"):
            is_error = True
            log = base_error_warning % (BracketPairErrorMsg.IMPROPER_KV_BRACKET.value, str(par_no), text)
        if text.count("<") != text.count(">"):
            is_error = True
            log = base_error_warning % (BracketPairErrorMsg.IMPROPER_FLOW_BRACKET.value, str(par_no), text)
        if text.count("[") != text.count("]"):
            is_error = True
            log = base_error_warning % (BracketPairErrorMsg.IMPROPER_RANGE_BRACKET.value, str(par_no), text)
        if text.count("(") != text.count(")"):
            is_error = True
            log = base_error_warning % (BracketPairErrorMsg.IMPROPER_COMMENT_BRACKET.value, str(par_no), text)
        # print(log)
        return log, is_error


    # Used in several control flow validation functions.
    @classmethod
    def is_valid_comparative_operator(self, operator: str) -> bool:
        '''
        Check if the given operator is a valid comparative operator.

        :param str operator: The operator to check.
        :return: True if the operator is valid, False otherwise.
        '''
        operators_list = ["e", "ne", "lt", "lte", "gt", "gte", "between"]
        if operator.lower() in operators_list:
            return True
        else:
            return False


    # Used in several control flow validation functions.
    @classmethod
    def is_valid_iteration_operator(self, operator: str) -> bool:
        '''
        Check if the given operator is a valid iteration operator.

        :param str operator: The operator to check.
        :return: True if the operator is valid, False otherwise.
        '''
        operators_list = ["+", "-", "*", "/", "%"]
        if operator.lower() in operators_list:
            return True
        else:
            return False


    @classmethod
    def validate_while(self, cf_split: List[str]) -> Tuple[str, bool]:
        """
        Validate the while command in the given list of strings.
        :param List[str] cf_split: List of strings containing the command and its arguments.
        :return: tuple (log, is_error)
            WHERE
            str log: error log (if any)
            bool is_error: flag if the checked line contains an error
        """
        log = ""
        is_error = False
        elements = len(cf_split)
        if elements == ArgNum.ARG_NUM_WHILE.value:
            if GeneralHelper.is_num(cf_split[1]):
                is_error = True
                log = log + MiscAlertMsg.ARGUMENT_MISMATCH.value.format(cf_split[1], cf_split) + "\n"
            if not self.is_valid_comparative_operator(cf_split[2]):
                is_error = True
                log = log + MiscAlertMsg.UNRECOGNIZED_OPERATOR.value.format(cf_split[2], cf_split) + "\n"
        else:
            log = log + MiscAlertMsg.IMPROPER_ARGNO.value.format(
                cf_split[0].upper(), ArgNum.ARG_NUM_WHILE.value, elements,
                cf_split) + "\n"
            is_error = True
        # note that the last value (comparison point is not yet checked as it can be digit, binary or possibly other things)
        return log, is_error


    # Used in process_foreach()
    @classmethod
    def validate_foreach(self, cf_split: List[str]) -> Tuple[str, bool]:
        '''
        Validate the foreach command in the given list of strings.

        :param List[str] cf_split: List of strings containing the command and its arguments.
        :return: tuple (log, is_error)
            WHERE
            str log: error log (if any)
            bool is_error: flag if the checked line contains an error
        '''
        log = ""
        is_error = False
        elements = len(cf_split)
        if elements == ArgNum.ARG_NUM_FOREACH.value:
            if GeneralHelper.is_num(cf_split[1]):  # or
                # https://stackoverflow.com/questions/36330860/pythonically-check-if-a-variable-name-is-valid
                is_error = True
                log = log + MiscAlertMsg.ARGUMENT_MISMATCH.value.format(cf_split[1], cf_split) + "\n"
        else:
            log = log + MiscAlertMsg.IMPROPER_ARGNO.value.format(
                cf_split[0].upper(), ArgNum.ARG_NUM_FOREACH.value, elements,
                cf_split) + "\n"
            is_error = True
        return log, is_error


    # Used in process_if().
    @classmethod
    def validate_if(self, cf_split):
        """
        Validate the structure of an IF statement.

        This function checks the number of elements, the validity of the comparative operator,
        and the argument types in the provided IF statement.

        :param list cf_split: A list of elements in the IF statement.
        :return: tuple (log, is_error)
            WHERE
            str log: A log message.
            bool is_error: A flag indicating if there's an error.
        """

        log = ""
        is_error = False
        elements = len(cf_split)
        if elements == ArgNum.ARG_NUM_IF.value:
            if GeneralHelper.is_num(cf_split[1]):
                is_error = True
                log = log + MiscAlertMsg.ARGUMENT_MISMATCH.value.format(cf_split[1], cf_split) + "\n"
            if not self.is_valid_comparative_operator(cf_split[2]):
                is_error = True
                log = log + MiscAlertMsg.UNRECOGNIZED_OPERATOR.value.format(cf_split[2], cf_split) + "\n"
        else:
            log = log + MiscAlertMsg.IMPROPER_ARGNO.value.format(
                cf_split[0].upper(), ArgNum.ARG_NUM_IF.value, elements,
                cf_split) + "\n"
            is_error = True
        # note that the last value (comparison point) is not yet checked as it can be digit, binary or possibly other things
        return log, is_error


    # Used in process_elseif().
    # Validation functions for else if, while and if have similar properties. Hence, these functions can be integrated, but
    # if there are changes for each of those, it may be difficult to refactor. For now these validation functions are
    # provided individually.
    @classmethod
    def validate_elseif(self, cf_split):
        """
        Validate the structure of an ELSEIF statement.

        This class method checks the number of elements, the validity of the comparative operator,
        and the argument types in the provided ELSEIF statement.

        :param list cf_split: A list of elements in the ELSEIF statement.
        :return: tuple (log, is_error)
            WHERE
            str log: A log message.
            bool is_error: A flag indicating if there's an error.
        """
        log = ""
        is_error = False
        elements = len(cf_split)
        if elements == ArgNum.ARG_NUM_ELSEIF.value:
            if GeneralHelper.is_num(cf_split[1]):
                is_error = True
                log = log + MiscAlertMsg.ARGUMENT_MISMATCH.value.format(cf_split[1], cf_split) + "\n"
            if not self.is_valid_comparative_operator(cf_split[2]):
                is_error = True
                log = log + MiscAlertMsg.UNRECOGNIZED_OPERATOR.value.format(cf_split[2], cf_split) + "\n"
        else:
            log = log + MiscAlertMsg.IMPROPER_ARGNO.value.format(
                cf_split[0].upper(), ArgNum.ARG_NUM_ELSEIF.value, elements,
                cf_split) + "\n"
            is_error = True
        # note that the last value (comparison point is not yet checked as it can be digit, binary or possibly other things)
        return log, is_error


    # Used in else().
    @classmethod
    def validate_else(self, cf_split: List[str]) -> Tuple[str, bool]:
        '''
        Validate the else command in the given list of strings.

        :param List[str] cf_split: List of strings containing the command and its arguments.
        :return: tuple (log, is_error)
            WHERE
            str log: error log (if any)
            bool is_error: flag if the checked line contains an error
        '''
        log = ""
        is_error = False
        elements = len(cf_split)
        if elements != ArgNum.ARG_NUM_ELSE.value:
            log = log + MiscAlertMsg.IMPROPER_ARGNO.value.format(
                cf_split[0].upper(), ArgNum.ARG_NUM_ELSE.value, elements,
                cf_split) + "\n"
            is_error = True
        return log, is_error


    # Used in process_range().
    @classmethod
    def validate_range(self, flow_range: str) -> Tuple[str, bool]:
        '''
        Validate the range command in the given string.

        :param str flow_range: String containing the range command.
        :return: tuple (log, is_error)
            WHERE
            str log: error log (if any)
            bool is_error: flag if the checked line contains an error
        '''
        is_error = False
        log = ""
        range_values = re.split("-", flow_range[1:-1])
        if len(range_values) == 2:
            if not (GeneralHelper.is_num(range_values[0]) and GeneralHelper.is_num(range_values[0])):
                is_error = True
                log = log + MiscAlertMsg.RANGE_NOT_NUMBERS.value.format(flow_range) + "\n"
        else:
            is_error = True
            log = log + MiscAlertMsg.RANGE_NOT_TWO_ARGS.value.format(flow_range) + "\n"
        return log, is_error


    # Used in process_for().
    @classmethod
    def validate_for(self, cf_split: List[str]) -> Tuple[str, bool]:
        '''
        Validate the for command in the given list of strings.

        :param List[str] cf_split: List of strings containing the command and its arguments.
        :return: tuple (log, is_error)
            WHERE
            str log: error log (if any)
            bool is_error: flag if the checked line contains an error
        '''
        log = ""
        is_error = False
        elements = len(cf_split)
        if elements == ArgNum.ARG_NUM_FOR.value:  # validating number of arguments in FOR
            if GeneralHelper.is_num(cf_split[1]):  # in case 2nd argument is number, throw an error
                is_error = True
                log = log + MiscAlertMsg.ARGUMENT_MISMATCH.value.format(cf_split[1], cf_split) + "\n"
            range_error_log, is_range_error = self.validate_range(cf_split[2])
            if is_range_error == True:  # check whether it is a valid range
                is_error = True
                log = log + range_error_log + "\n"
            if not self.is_valid_iteration_operator(cf_split[3]):  # check whether it is a valid operator
                is_error = True
                log = log + MiscAlertMsg.INVALID_ITERATION_OPERATOR.value.format(cf_split[3],
                                                                                 cf_split) + "\n"
        else:  # if number of argument is invalid
            log = log + MiscAlertMsg.IMPROPER_ARGNO.value.format(
                cf_split[0].upper(), ArgNum.ARG_NUM_FOR.value, elements,
                cf_split) + "\n"
            is_error = True
        return log, is_error


    # Used in process_iterate().
    @classmethod
    def validate_iterate(self, cf_split: List[str]) -> Tuple[str, bool]:
        '''
        Validate the iterate command in the given list of strings.

        :param List[str] cf_split: List of strings containing the command and its arguments.
        :return: tuple (log, is_error)
            WHERE
            str log: error log (if any)
            bool is_error: flag if the checked line contains an error
        '''
        log = ""
        is_error = False
        elements = len(cf_split)
        if elements == ArgNum.ARG_NUM_ITERATE.value:
            if not self.is_valid_iteration_operator(cf_split[1]):
                is_error = True
                log = log + MiscAlertMsg.INVALID_ITERATION_OPERATOR.value.format(cf_split[1],
                                                                                 cf_split) + "\n"
        else:  # if number of argument is invalid
            log = log + MiscAlertMsg.IMPROPER_ARGNO.value.format(
                cf_split[0].upper(), ArgNum.ARG_NUM_ITERATE.value, elements,
                cf_split) + "\n"
            is_error = True
        return log, is_error


    # Used in process_section().
    @classmethod
    def validate_section(self, cf_split: List[str]) -> Tuple[str, bool]:
        '''
        Validate the section command in the given list of strings.

        :param List[str] cf_split: List of strings containing the command and its arguments.
        :return: tuple (log, is_error)
            WHERE
            str log: error log (if any)
            bool is_error: flag if the checked line contains an error
        '''
        log = ""
        is_error = False
        elements = len(cf_split)
        if elements != ArgNum.ARG_NUM_SECTION.value:
            log = log + MiscAlertMsg.IMPROPER_ARGNO.value.format(
                cf_split[0].upper(), ArgNum.ARG_NUM_SECTION.value,
                elements, cf_split) + "\n"
            is_error = True
        return log, is_error


class GeneralHelper:

    @classmethod
    def split_into_sentences(self, content):
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


    # Used in get_attachment_long_name()
    @classmethod
    def split_by_separators(self, text: str, separators: List[str]) -> List[str]:
        """
        Split a given text using multiple separators.

        This function replaces all occurrences of the separators in the input
        string with the first separator in the list. Then, it splits the input
        string into a list of substrings based on the first separator. Finally,
        it returns the list of substrings after removing any leading or trailing
        whitespaces from each substring.

        :param str text: The input string to be split.
        :param list separators: A list of separators to be used for splitting the input string.
        :return: A list of substrings obtained by splitting the input string using the specified separators.
        :rtype: list
        """
        default_sep = separators[0]
        for sep in separators[1:]:
            text = text.replace(sep, default_sep)
        return [i.strip() for i in text.split(default_sep)]


    # Used in several control flow validation functions.
    def is_num(s: str) -> bool:
        '''
        Check if the given string represents a number (integer or float).

        :param str s: The string to check.
        :return: True if the string represents a number, False otherwise.
        '''
        if isinstance(s, int) or isinstance(s, float):
            return True
        else:
            s = s.replace(',', '', 1)
            if s[0] in ('-', '+'):
                return s[1:].isdigit()
            else:
                return s.isdigit()


    # helper function to print dataframe, used for development and debugging
    def print_whole_df(df: pd.DataFrame) -> None:
        '''
        Print the entire DataFrame without truncation.
        '''
        with pd.option_context('display.max_rows', None, 'display.max_columns',
                               None):  # more options can be specified also
            print(df)


class DocxHelper:

    # Used in write_tag_to_doc()
    @classmethod
    def get_span_attr_val(self, c: Tag) -> Tuple[str, str]:
        """
        Get the attribute and value from the "style" attribute of a given Tag.

        This class method uses a regular expression to find the attribute and value
        in the "style" attribute of the provided Tag. It returns a tuple containing
        the attribute and value.

        :param bs4.element.Tag c: The Tag to extract the attribute and value from.
        :return: tuple (attr, val)
        WHERE
            str attr: The attribute.
            str val: The value.
        """
        found = re.findall(RegexPatterns.SPAN_ATTR_VAL.value, c.get("style"))
        attr, val = found[0]
        return attr, val


    # Used in write_tag_to_doc()
    @classmethod
    def get_section_title(self, line: str) -> str:
        """
        Get the section title from a given line.

        This class method splits the given line into words and returns a string
        composed of all words except the first one. If the line contains only one word,
        an empty string is returned.

        :param str line: The line to extract the section title from.
        :return: The section title or an empty string.
        :rtype: str
        """
        words = line.split()
        if len(words) > 1:
            return ' '.join(words[1:])
        else:
            return ""


    @classmethod
    def process_reg_bracket(self, line: str) -> Tuple[str, List[str]]:
        '''
        Process strings with regular brackets (), which can be (_invisible comment_), (regular comment), or (DOI).
        This class method also maintains and updates numerical index of DOIs found in the text entries.

        The string is returned to prepare for further docx content processing, in which the invisible comment will not be
        included, visible regular comment is still there but without brackets, and the DOI is provided with numerical
        index reference.

        :param str line: the comment string (with bracket) to be processed.
        :return: tuple (processed_line, references)
            WHERE
            str processed_line: processed_line is the processed string to be written as a part of docx content,
            list references: the list of available DOI references.
        '''
        global ref_counter
        references = []
        # split based on the existence of brackets - including the captured bracket block in the result
        line_elements = re.split(RegexPatterns.COMMENT_W_CAPTURE_GROUP.value, line)
        processed_line = ""
        for element in line_elements:
            found_dois = re.findall(RegexPatterns.DOI.value, element)
            found_doi_length = len(found_dois)
            if re.search(RegexPatterns.COMMENT.value, element):
                # _invisible_ comment - strip all content (brackets, underscores, content
                if re.search(RegexPatterns.COMMENT_INVISIBLE.value, element):
                    processed_element = ""
                # visible comment - strip brackets and colons, keep the content
                elif re.search(RegexPatterns.COMMENT_VISIBLE.value, element):
                    element = re.sub(RegexPatterns.SEPARATOR_MARKUP.value, '', element)
                    visible_comments = re.split(RegexPatterns.COMMENT_VISIBLE.value, element)
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


    # TODO: check why some invisible key elements passed the invisibility checks.
    @classmethod
    def write_tag_to_doc(self, document: Document, tag_item: Tag) -> List[str]:
        '''
        writes and format html tag content to docx document.
        :param Document document: python-docx document instance.
        :param  bs4.element.Tag tag_item: tag to be processed and written to document.
        :return: list all_references
            WHERE
            list all_references: all references of DOIs contained in the document.
        '''
        all_references = []
        p = document.add_paragraph()
        log = ""
        if isinstance(tag_item, Tag):
            section_toggle = False
            subsection_level = 0
            for subcontent in tag_item.contents:
                # strip_markup_and_explicit_keys()
                if isinstance(subcontent, Tag):
                    # print("ORIGINAL CONTENT OF SUBCONTENT.GETTEXT() WITHIN A TAG INSTACE : " + subcontent.get_text())
                    line, references = TextCleaner.strip_markup_and_explicit_keys(subcontent.get_text())
                    # print("LINE FROM TAG INSTANCE: " + line)
                else:
                    if re.match(RegexPatterns.FORMULA.value, subcontent):
                        references = []
                        line = ""
                        formulas = re.findall(RegexPatterns.FORMULA.value, subcontent)
                        processed_subcontent = str(subcontent)
                        for formula in formulas:
                            stripped_formula = formula[1:-1]
                            processed_subcontent = processed_subcontent.replace(formula, '')
                            docx_formula, docx_formula_log = self.latex_formula_to_docx(stripped_formula)
                            log = log + docx_formula_log
                            if docx_formula != None:
                                p._element.append(docx_formula)
                                p.add_run(TextCleaner.remove_extra_spaces(processed_subcontent))
                    else:
                        line, references = TextCleaner.strip_markup_and_explicit_keys(subcontent.string)
                        # print("LINE FROM NON-TAG INSTANCE: " + line)

                if len(references) > 0:
                    all_references.extend(references)

                # check if the line is either goal, procedure, or result - but only limit that to one word
                if re.match(r'Goal:*|Procedure:*|Result:*', line, re.IGNORECASE) and len(line.split()) == 1:
                    document.add_heading(line, level=1)
                # check if the line is a section with following characters
                elif re.match(RegexPatterns.SUBSECTION_W_EXTRAS.value, line, re.IGNORECASE):
                    section_title = self.get_section_title(line)
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
                    sub_text = p.add_run(TextCleaner.remove_extra_spaces(line))
                    sub_text.font.subscript = True
                # check if it is an italic-formatted text
                elif subcontent.name == "em":
                    # print("EM : " + line)
                    italic_text = p.add_run(TextCleaner.remove_extra_spaces(line))
                    # italic_text = p.add_run(" " + line + " ")
                    italic_text.font.italic = True
                # # check if it is a span tag
                elif subcontent.name == "span":
                    attr, val = self.get_span_attr_val(subcontent)
                    # check if the line is a section without being followed by other characters, hence it needs the following
                    # chars from the next line as its section title. This case tends to happen when a section in a line is
                    # not covered within the same span tag hierarchy as its label.
                    if re.match(RegexPatterns.SUBSECTION.value, line, re.IGNORECASE):
                        section_toggle = True
                        subsection_level = line.count("sub")
                    elif (section_toggle):
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
                        color_text = p.add_run(TextCleaner.remove_extra_spaces(line))
                        color_text.font.color.rgb = RGBColor.from_string(val[1:])
                    elif attr == "font-style" and attr == "italic":
                        # print("FONT STYLE AND ITALIC : " + line)
                        styled_text = p.add_run(TextCleaner.remove_extra_spaces(line))
                        styled_text.italic = True
                    else:
                        # print("NON SUBSECT/HEADING/COLOR/FSTYLE : " + line)
                        p.add_run(TextCleaner.remove_extra_spaces(line))
                # check if it is bold format
                elif subcontent.name == "strong":
                    # print("STRONG : " + line)
                    bold_text = p.add_run(TextCleaner.remove_extra_spaces(line))
                    bold_text.bold = True
                # check if it is superscript format
                elif subcontent.name == "sup":
                    # print("SUP : " + line)
                    # super_text = p.add_run(line + " ")
                    super_text = p.add_run(TextCleaner.remove_extra_spaces(line))
                    super_text.font.superscript = True
                else:
                    # print("NON SUP/STRONG/SPAN/EM/SUB/SECT/SUBSECT : " + line)
                    p.add_run(TextCleaner.remove_extra_spaces(line))

        else:
            line, references = TextCleaner.strip_markup_and_explicit_keys(tag_item.string)
            if len(references) > 0:
                all_references.extend(references)
            # print("NON-TAG INSTANCE : " + line)
            p.add_run(TextCleaner.remove_extra_spaces(line))
            # print("*"*50)
        return all_references, log


    # Used in add_img_to_doc()
    @classmethod
    def get_text_width(self, document: Document) -> float:
        """
        Return the text width in mm of the first section of a given document.

        This class method calculates the text width by subtracting the left and right margins
        from the page width of the first section of the document. The result is then divided by 36000
        to convert the measurement to millimeters.

        :param docx.Document document: The document to calculate the text width for.
        :return: A floating point value representing the text width in millimeters.
        """
        section = document.sections[0]
        return (section.page_width - section.left_margin - section.right_margin) / 36000


    @classmethod
    def latex_formula_to_docx(self, latex_formula: str) -> Tuple[str, str]:
        '''
        Convert latex formula to docx formula.

        This function requires MML2OMML.XSL style sheet, which normally shipped with Microsoft Office suite.
        The style sheet file should be placed in the same directory as config.json file. Please check LISTER's readme.

        :param str latex_formula: latex string to be converted to docx formula representation.
        :return: tuple (docx_formula, log)
            WHERE
            str docx_formula: formula represented in docx-string compatible that is going to be written to the docx file.
            str log: error log (if any)
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
            log = log + MiscAlertMsg.MISSING_MML2OMML.value
            print(log)
            pass
        return docx_formula, log


    @classmethod
    def add_table_to_doc(self, doc: Document, content: Tag) -> None:
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


    @classmethod
    def add_img_to_doc(self, document: Document, real_name: str, path: str) -> None:
        '''
        Add image to the document file, based on upload id and image name when it was uploaded.

        :param Document document: the document object that is being modified.
        :param str real_name: real name of the image when it was uploaded to eLabFTW.
        :param str path: path to the image/attachment.
        '''
        log = ""
        if real_name:
            img_saving_path = path + '/attachments/'
            sanitized_img_saving_path = sanitize_filepath(img_saving_path, platform="auto")
            try:
                document.add_picture(sanitized_img_saving_path + "/" + real_name, width=Mm(self.get_text_width(document)))
            except Exception as e:
                log = log + MiscAlertMsg.INACCESSIBLE_ATTACHMENT.value.format(real_name, str(e))
                pass
            print(log)

# ---------------------------------------------- Text Cleaning Class ---------------------------------------------------
class TextCleaner:

    @classmethod
    def get_nonempty_body_tags(self, exp: BeautifulSoup) -> List:
        '''
        Clean up the source-html from empty-content html tags.

        :param bs4.soup exp: beautifulSoup4.soup experiment object.
        :return: list tagged_contents: list of non-empty html tags as well as new lines.
        '''
        html_body = exp.__dict__["_body"]
        soup = BeautifulSoup(html_body.encode("utf-8"), "html.parser")
        soup.encoding = "utf-8"
        non_empty_soup = self.remove_empty_tags(soup)
        tagged_contents = non_empty_soup.currentTag.tagStack[0].contents
        return tagged_contents


    @classmethod
    def process_nbsp(self, soup: BeautifulSoup) -> List[str]: # should probably be refactored to remove_nbsp for clarity
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


    @classmethod
    def strip_unwanted_mvu_colons(self, word: str) -> str:
        '''
        Remove surrounding colon on word(s) within annotation bracket, if it belongs value/measure/unit category.

        :param str word: string with or without colons.
        :return: str word without colons.
        '''
        if re.search(RegexPatterns.SORROUNDED_W_COLONS.value, word):
            # TODO: make the unicode character below properly printed as relevant symbol of utf-8 in console
            print("Surrounding colons in the value/measure/unit {} is removed".format(word).encode("utf-8"))
            word = word[1:-1]  # if there are colons surrounding the word remains, remove it
        return word


    @classmethod
    def strip_markup_and_explicit_keys(self, line: str) -> Tuple[str, List[str]]:
        '''
        Strip keys that are marked as in visible (i.e., keys that are enclosed with colon) and extract any occuring
        pattern of DOI as reference, strip curly and angle brackets, reformat any annotation with regular bracket and
        fetch the DOI references, and strip unnecessary white spaces.

        :param bs4.element.NavigableString/str line: string to be inspected.
        :return: list of string containing DOI number.
        '''
        stripped_from_explicit_keys = re.sub(RegexPatterns.SEPARATOR_AND_KEY.value, '', line)
        # print(stripped_from_explicit_keys)
        # strip curly and angle brackets
        stripped_from_markup = re.sub(RegexPatterns.BRACKET_MARKUPS.value, '', stripped_from_explicit_keys)
        # process based on the types within regular comment
        comments_based_strip, references = DocxHelper.process_reg_bracket(stripped_from_markup)
        # strip separator (pipe symbol)
        stripped_from_markup = re.sub(RegexPatterns.SEPARATOR_COLON_MARKUP.value, ' ', comments_based_strip)
        # strip unnecessary whitespaces
        stripped_from_trailing_spaces = re.sub(RegexPatterns.PRE_PERIOD_SPACES.value, '.', stripped_from_markup)
        stripped_from_trailing_spaces = re.sub(RegexPatterns.PRE_COMMA_SPACES.value, ',',
                                               stripped_from_trailing_spaces)
        # stripped_from_trailing_spaces = " ".join(stripped_from_trailing_spaces.split())  # strip from trailing whitespaces
        return stripped_from_trailing_spaces, references


    # Used in parse_lines_to_metadata().
    @classmethod
    def strip_colon(self, key: str) -> str:
        """
        Strip colon found on key string.

        This class method uses a regular expression to remove all colons from the provided string.

        :param str key: The string to remove colons from.
        :return: str stripped_key: The string with all colons removed.
        """
        stripped_key = re.sub('\:', '', key)
        return stripped_key


    @classmethod
    def remove_empty_tags(self, soup: BeautifulSoup) -> BeautifulSoup:
        '''
        Remove empty tags from a BeautifulSoup object.

        :param BeautifulSoup soup: The BeautifulSoup object to be processed.
        :return: BeautifulSoup soup: BeautifulSoup object with empty tags removed.
        '''
        for x in soup.find_all():
            # if the text within a tag is empty, and tag name is not img/br/etc.. and it is not img within p tag:
            if len(x.get_text(strip=True)) == 0 and x.name not in ['img', 'br', 'td', 'tr', 'table', 'h1', 'h2', 'h3',
                                                                   'h5', 'h6'] and len(x.select("p img")) == 0:
                x.extract()
        return soup


    @classmethod
    def remove_extra_spaces(self, line: str) -> str:
        """
        Remove extra spaces from a given line.

        This class method uses a regular expression to replace all occurrences of multiple spaces
        in the provided string with a single space.

        :param str line: The string to remove extra spaces from.
        :return: (str) The string with all extra spaces removed.
        """
        return re.sub(' +', ' ', line)


    @classmethod
    def remove_table_tag(self, soup: BeautifulSoup) -> BeautifulSoup:
        '''
        Remove table tags and its content from the soup object.

        :param bs4.BeautifulSoup soup: bs4 soup object.
        :return: bs4.BeautifulSoup soup: BeautifulSoup object without table tag, and it's content.
        '''
        for table in soup("table"):
            table.decompose()
        return soup


# ------------------------------------------------ Path Helper Class --------------------------------------------------
class PathHelper:
    @classmethod
    def derive_fname_from_exp(self, exp: Union[elabapi_python.Experiment, Dict]) -> str:
        """
        Derive a file name from the experiment dictionary.

        This class method checks if the provided experiment is a dictionary.
        If it is, it retrieves the title from the dictionary.
        If it's not a dictionary, it retrieves the title from the experiment's attributes.
        The title is then slugified to create a file name.

        :param Union[elabapi_python.Experiment, Dict] exp: The experiment to derive the file name from.
                                                           Can be a dictionary or an object with a "_title" attribute.
        :return: str fname_from_exp: The derived file name.
        """
        if isinstance(exp, dict):
            exp_title = exp["title"]
        else:
            exp_title = exp.__dict__["_title"]
        fname_from_exp = PathHelper.slugify(exp_title)
        return fname_from_exp


    @classmethod
    def get_default_output_path(self, file_name: str) -> str:
        '''
        Create an output path based on the home path (OS-dependent) and output file name.
        The home path is OS-dependent. On Windows/Linux, it is in the output directory as the script/executables.
        On macOS, it is in the users' Apps/lister/output/ directory.

        :param str file_name: file name for the output.
        :return: str output_path: the output path created from appending lister's output home directory and
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


    @classmethod
    def manage_output_path(path, dir_name: str, file_name: str) -> str:
        '''
        Get the output path according to respective platform.

        If it is on macOS, just return the dir_name (which have already been appended with output filename),
        on Windows/Linux, return the dir_name + output file_name.

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


    @classmethod
    def check_and_create_path(self, path: str) -> None:
        '''
        Check if the given path exists, and create the directory if it doesn't.

        :param path: The path to check and create if necessary.
        '''
        if not os.path.isdir(path):
            print("Output path %s is not available, creating the path directory..." % (path))
            os.makedirs(path)


    @classmethod
    def manage_input_path(self) -> str:
        '''
        Enforce reading input from a specific directory on macOS (on macOS, LISTER cannot get the input directly
        from the executable file's directory).

        :return: str input_path is the input directory for macOS.
        '''
        input_path = ""
        if platform.system() == "Darwin":  # enforce input path to be specific to ~/Apps/lister/
            home = str(Path.home())
            input_path = home + "/Apps/lister/"
        return input_path


    #    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    #    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    #    dashes to single dashes. Remove characters that aren't alphanumerics,
    #    underscores, or hyphens. Convert to lowercase. Also strip leading and
    #   trailing whitespace, dashes, and underscores.
    def slugify(value: Union[str, Any], allow_unicode: bool = False) -> str:
        """
        Convert a string into a URL-friendly slug.

        :param value: The input string to be converted.
        :param allow_unicode: Whether to allow Unicode characters in the slug.
        :return: The URL-friendly slug.
        """
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize('NFKC', value)
        else:
            value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'[-\s]+', '-', value).strip('-_')


# ------------------------------------------------ MAIN FUNCTION ------------------------------------------------------
ref_counter = 0

def main():
    global output_fname  # , input_file
    global output_path, base_output_path
    global token, exp_no, endpoint
    log = ""

    # suppress the redundant window pop up on macOS as a workaround, see
    # https://stackoverflow.com/questions/72636873/app-package-built-by-pyinstaller-fails-after-it-uses-tqdm
    if platform.system() == "Darwin":
        warnings.filterwarnings("ignore")
        freeze_support()

    guiHelper = GUIHelper()

    args = guiHelper.parse_gooey_args()
    base_output_path = args.base_output_dir
    apiv2endpoint = ApiAccess.get_apiv2endpoint(args.endpoint)
    apiv2client = ApiAccess.create_apiv2client(apiv2endpoint, args.token)

    if args.command == 'parse_resource':
        item_api_response = ApiAccess.get_resource_item(apiv2client, args.resource_item_no)
        cat = item_api_response.__dict__["_category_title"]
        title = item_api_response.__dict__["_title"]
        if args.id:
            output_fname = PathHelper.slugify(cat) + "_" + str(args.resource_item_no)
        elif args.title:
            output_fname = PathHelper.slugify(cat) + "_" + PathHelper.slugify(title)
    elif args.command == 'parse_experiment':
        if args.id:
            output_fname = PathHelper.slugify("experiment") + "_" + str(args.exp_no)
        elif args.title:
            title = ApiAccess.get_exp_title(apiv2client, args.exp_no)
            output_fname = PathHelper.slugify("experiment") + "_" + PathHelper.slugify(title)
    print("The output is written to %s directory" % (output_fname))

    output_path = PathHelper.manage_output_path(args.base_output_dir, output_fname)
    PathHelper.check_and_create_path(output_path)

    print("base_output_dir: ", (base_output_path))
    print("output_fname: ", (output_fname))
    print("output_path: ", (output_path))

    if args.command == 'parse_experiment':
        print("Processing an experiment...")
        MetadataExtractor.process_experiment(apiv2client, args.exp_no, output_path)
    elif args.command == 'parse_resource':
        print("Processing a resource...")
        MetadataExtractor.process_ref_resource_item(apiv2client, item_api_response)


if __name__ == "__main__":
    main()
