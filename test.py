import re
import lister
from bs4 import BeautifulSoup
import elabapi_python
import os
from unittest.mock import MagicMock, Mock, patch
from pathlib import Path
import unittest
import platform
from argparse import Namespace
from bs4 import BeautifulSoup, Tag
import shutil
import pandas as pd
from lxml import etree


#  from lxml import etree
# import latex2mathml.converter
# from lister import latex_formula_to_docx, MiscAlertMsg

class ApiException:
    pass


class Test_lister(unittest.TestCase):


    def test_get_api_v2endpoint(self):
        v1endpoint = 'http://example.com/v1'
        expected_v2endpoint = 'https://example.com/v2'
        self.assertEqual(lister.ApiAccess.get_api_v2endpoint(v1endpoint), expected_v2endpoint)


    def test_create_apiv2_client(self):
        endpoint = 'http://example.com/v1'
        token = 'test_token'
        apiv2_client = lister.ApiAccess.create_apiv2_client(endpoint, token)

        self.assertIsInstance(apiv2_client, elabapi_python.ApiClient)
        self.assertEqual(apiv2_client.configuration.host, 'https://example.com/v2')
        self.assertEqual(apiv2_client.configuration.api_key['api_key'], token)
        self.assertEqual(apiv2_client.configuration.api_key_prefix['api_key'], 'Authorization')
        self.assertFalse(apiv2_client.configuration.debug)
        self.assertFalse(apiv2_client.configuration.verify_ssl)


    # def test_derive_fname_from_exp(self):
    #     exp = {"title": "Example Experiment Title"}
    #     expected_fname = "example-experiment-title"
    #     self.assertEqual(lister.PathHelper.derive_fname_from_exp(exp), expected_fname)

    def test_derive_fname_from_exp_v2(self):

        # Test with a dictionary
        exp_dict = {"title": "My Experiment"}
        result = lister.PathHelper.derive_fname_from_exp_v2(exp_dict)
        self.assertEqual(result, "my-experiment")  # assuming slugify converts "My Experiment" to "my-experiment"

        # Test with an Experiment object
        exp_obj = elabapi_python.Experiment()
        exp_obj.__dict__["_title"] = "Another Experiment"
        result = lister.PathHelper.derive_fname_from_exp_v2(exp_obj)
        self.assertEqual(result, "another-experiment")  # assuming slugify converts "Another Experiment" to "another-experiment"


    @patch('os.path.isdir')
    @patch('os.makedirs')
    def test_check_and_create_path(self, mock_makedirs, mock_isdir):
        # Test when the directory exists
        mock_isdir.return_value = True
        path = '/path/to/directory'
        lister.PathHelper.check_and_create_path(path)
        mock_isdir.assert_called_with(path)
        mock_makedirs.assert_not_called()

        # Test when the directory does not exist
        mock_isdir.return_value = False
        lister.PathHelper.check_and_create_path(path)
        mock_isdir.assert_called_with(path)
        mock_makedirs.assert_called_with(path)


    # @patch('lister.PathHelper.check_and_create_path')
    # @patch('os.path.isdir')
    # @patch('builtins.open', new_callable=unittest.mock.mock_open)
    # def test_get_and_save_attachments(self, mock_open, mock_isdir, mock_check_and_create_path):
    #     manager = MagicMock()
    #     uploads = [
    #         {"id": "1", "real_name": "attachment1.txt"},
    #         {"id": "2", "real_name": "attachment2.txt"}
    #     ]
    #     path = '/path/to/directory'
    #
    #     mock_isdir.return_value = True
    #     manager.get_upload.side_effect = [b'content1', b'content2']
    #
    #     lister.ApiAccess.get_and_save_attachments(manager, uploads, path)
    #
    #     mock_check_and_create_path.assert_called_with(path + '/attachments/')
    #     manager.get_upload.assert_any_call("1")
    #     manager.get_upload.assert_any_call("2")
    #     mock_open.assert_any_call(path + '/attachments/attachment1.txt', 'wb')
    #     mock_open.assert_any_call(path + '/attachments/attachment2.txt', 'wb')
    #     mock_open().write.assert_any_call(b'content1')
    #     mock_open().write.assert_any_call(b'content2')


    @patch("lister.PathHelper.check_and_create_path")
    @patch("elabapi_python.UploadsApi")
    @patch("elabapi_python.ExperimentsApi")
    def test_get_and_save_attachments_apiv2(self, mock_experiments_api, mock_uploads_api, mock_check_and_create_path):
        # Create an instance of the class

        # Mock the experiment object
        mock_experiment = MagicMock()
        mock_experiment.id = 1
        mock_experiments_api.return_value.get_experiment.return_value = mock_experiment

        # Mock the upload object
        mock_upload = MagicMock()
        mock_upload.id = 1
        mock_upload.real_name = "attachment.txt"
        mock_uploads_api.return_value.read_uploads.return_value = [mock_upload]
        mock_uploads_api.return_value.read_upload.return_value.data = b"attachment content"

        # Call the method
        path = "test_path"
        apiv2_client = MagicMock()
        exp_id = 1
        log = lister.get_and_save_attachments_apiv2(path, apiv2_client, exp_id)

        # Check if the method calls are correct
        mock_experiments_api.return_value.get_experiment.assert_called_once_with(exp_id)
        mock_uploads_api.return_value.read_uploads.assert_called_once_with("experiments", mock_experiment.id)
        mock_uploads_api.return_value.read_upload.assert_called_once_with("experiments", mock_experiment.id, mock_upload.id, format="binary", _preload_content=False)
        mock_check_and_create_path.assert_called_once_with(path + "/attachments")

        # Check if the log is empty
        self.assertEqual(log, "")


    @patch('lister.PathHelper.check_and_create_path')
    @patch('lister.sanitize_filepath')
    @patch('elabapi_python.ExperimentsApi')
    @patch('elabapi_python.UploadsApi')
    def test_get_and_save_attachments_apiv2(self, mock_uploads_api, mock_experiments_api, mock_sanitize_filepath, mock_check_and_create_path):
        path = '/path/to/directory'
        apiv2_client = MagicMock()
        exp_id = 1

        mock_sanitize_filepath.return_value = path + '/' + 'attachments'
        mock_check_and_create_path.return_value = None
        mock_experiments_api.get_experiment.return_value = MagicMock(id=exp_id)
        mock_uploads_api.read_uploads.return_value = [
            MagicMock(id="1", real_name="attachment1.txt"),
            MagicMock(id="2", real_name="attachment2.txt")
        ]
        mock_uploads_api.read_upload.return_value = MagicMock(data=b"file_content")

        lister.ApiAccess.get_and_save_attachments_apiv2(path, apiv2_client, exp_id)

        mock_check_and_create_path.assert_called_once_with(mock_sanitize_filepath.return_value)
        # TODO: check the necesssity of the following assertions.
        # mock_uploads_api.read_uploads.assert_called_once_with('experiments', exp_id)
        # mock_uploads_api.read_upload.assert_any_call('experiments', exp_id, "1", format='binary', _preload_content=False)
        # mock_uploads_api.read_upload.assert_any_call('experiments', exp_id, "2", format='binary', _preload_content=False)


    def test_split_into_sentences(self):
        content = (' <if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of '
                   '{POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using '
                   '{TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute. '
                   '<elif|membrane simulation|e|false>, the variants were solvated in an {octahedral|box type} '
                   'water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.')
        sentences = [
            '<if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of '
            '{POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using '
            '{TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.',
            '<elif|membrane simulation|e|false>, the variants were solvated in an '
            '{octahedral|box type} water box using {TIP3P|water type} with a '
            'minimal shell of {12 Å|shell radius} around the solute.']
        self.assertListEqual(lister.GeneralHelper.split_into_sentences(content), sentences)

    def test_is_valid_comparative_operator(self):
        self.assertTrue(lister.Validator.is_valid_comparative_operator("e"))
        self.assertTrue(lister.Validator.is_valid_comparative_operator("ne"))
        self.assertTrue(lister.Validator.is_valid_comparative_operator("gt"))
        self.assertTrue(lister.Validator.is_valid_comparative_operator("between"))
        self.assertTrue(lister.Validator.is_valid_comparative_operator("gte"))
        self.assertTrue(lister.Validator.is_valid_comparative_operator("lt"))
        self.assertTrue(lister.Validator.is_valid_comparative_operator("lte"))
        self.assertFalse(lister.Validator.is_valid_comparative_operator("="))
        self.assertFalse(lister.Validator.is_valid_comparative_operator("<"))
        self.assertFalse(lister.Validator.is_valid_comparative_operator(">"))
        self.assertFalse(lister.Validator.is_valid_comparative_operator(">="))
        self.assertFalse(lister.Validator.is_valid_comparative_operator("<="))

    def test_is_valid_iteration_operator(self):
        self.assertTrue(lister.Validator.is_valid_iteration_operator("+"))
        self.assertTrue(lister.Validator.is_valid_iteration_operator("-"))
        self.assertTrue(lister.Validator.is_valid_iteration_operator("*"))
        self.assertTrue(lister.Validator.is_valid_iteration_operator("/"))
        self.assertTrue(lister.Validator.is_valid_iteration_operator("%"))
        self.assertFalse(lister.Validator.is_valid_iteration_operator("substract"))
        self.assertFalse(lister.Validator.is_valid_iteration_operator("add"))
        self.assertFalse(lister.Validator.is_valid_iteration_operator("multiply"))
        self.assertFalse(lister.Validator.is_valid_iteration_operator("divide"))
        self.assertFalse(lister.Validator.is_valid_iteration_operator("modulo"))

    def test_is_num(self):
        self.assertTrue(lister.GeneralHelper.is_num("1"))
        self.assertTrue(lister.GeneralHelper.is_num(1))
        self.assertFalse(lister.GeneralHelper.is_num('A1'))

    def test_check_bracket_num(self):
        line = ('<if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of '
                '{POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using '
                '{TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute. '
                '<elif|membrane simulation|e|false>, the variants were solvated in an {octahedral|box type} '
                'water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.')
        line2 = ('if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of '
                 '{POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using '
                 '{TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute. '
                 '<elif|membrane simulation|e|false>, the variants were solvated in an {octahedral|box type} '
                 'water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.')
        par_no = 2
        self.assertFalse(lister.Validator.check_bracket_num(par_no, line)[1])
        self.assertTrue(lister.Validator.check_bracket_num(par_no, line2)[1])

    def test_validate_foreach(self):
        pair = ['for each', 'cycles of minimization']
        pair2 = ['for each']
        self.assertFalse(lister.Validator.validate_foreach(pair)[1])
        self.assertTrue(lister.Validator.validate_foreach(pair2)[1])

    def test_validate_while(self):
        list1 = ['while', 'ph', 'lte', '7']
        list2 = ['while', 'ph', '7']
        self.assertFalse(lister.Validator.validate_while(list1)[1])
        self.assertTrue(lister.Validator.validate_while(list2)[1])

    def test_validate_if(self):
        list1 = ['if', 'membrane simulation', 'e', 'True']
        list2 = ['if', 'membrane simulation', 'True']
        self.assertFalse(lister.Validator.validate_if(list1)[1])
        self.assertTrue(lister.Validator.validate_if(list2)[1])

    def test_validate_elseif(self):
        list1 = ['elif', 'membrane simulation', 'e', 'false']
        list2 = ['elif', 'membrane simulation', '=', 'false']
        list3 = ['elif', 'membrane simulation', 'false']
        self.assertFalse(lister.Validator.validate_elseif(list1)[1])
        self.assertTrue(lister.Validator.validate_elseif(list2)[1])
        self.assertTrue(lister.Validator.validate_elseif(list3)[1])


    def test_validate_for(self):
        list1 = ['for', 'pH', '[1-7]', '+', '1']
        list2 = ['for', 'pH', '[1-7]', '1']
        self.assertFalse(lister.Validator.validate_for(list1)[1])
        self.assertTrue(lister.Validator.validate_for(list2)[1])


    def test_validate_section(self):
        list1 = ['Section', 'Preparation and Environment']
        list2 = ['Section']
        self.assertFalse(lister.Validator.validate_section(list1)[1])
        self.assertTrue(lister.Validator.validate_section(list2)[1])


    def test_process_foreach(self):
        list1 = ['for each', 'cycles of minimization']
        par_no = 8
        processed_list = [[8, 'step type', 'iteration', '', ''],
                          [8, 'flow type', 'for each', '', ''],
                          [8, 'flow parameter', 'cycles of minimization', '', '']]
        self.assertListEqual(lister.MetadataExtractor.process_foreach(par_no, list1)[0], processed_list)


    def test_process_for(self):
        # Test case 1: Valid input
        par_no = 1
        cf_split = ["for", "param", "[1-7]", "+", "1"]
        key_val, for_log, is_error = lister.MetadataExtractor.process_for(par_no, cf_split)
        self.assertEqual(len(key_val), 8)
        self.assertEqual(for_log, "")
        self.assertFalse(is_error)

        # Test case 2: Invalid input
        par_no = 1
        cf_split = ["for", "param", "[1-10]", "+"]
        key_val, for_log, is_error = lister.MetadataExtractor.process_for(par_no, cf_split)
        # self.assertNotEqual(for_log, "")
        self.assertTrue(is_error)


    def test_process_if(self):
        list1 = ['if', 'membrane simulation', 'e', 'true']
        par_no = 2
        processed_list = [[2, 'step type', 'conditional', '', ''],
                          [2, 'flow type', 'if', '', ''],
                          [2, 'flow parameter', 'membrane simulation', '', ''],
                          [2, 'flow logical parameter', 'e', '', ''],
                          [2, 'flow compared value', 'true', '', '']]
        self.assertListEqual(lister.MetadataExtractor.process_if(par_no, list1)[0], processed_list)

    def test_process_elseif(self):
        list1 = ['elif', 'membrane simulation', 'e', 'false']
        par_no = 2
        processed_list = [[2, 'step type', 'conditional', '', ''],
                          [2, 'flow type', 'elif', '', ''],
                          [2, 'flow parameter', 'membrane simulation', '', ''],
                          [2, 'flow logical parameter', 'e', '', ''],
                          [2, 'flow compared value', 'false', '', '']]
        self.assertListEqual(lister.MetadataExtractor.process_elseif(par_no, list1)[0], processed_list)


    def test_process_internal_comment(self):
        str1 = "molecular dynamics (MD)"
        comment = '(MD)'
        remain  = 'molecular dynamics'
        self.assertEqual(lister.MetadataExtractor.process_internal_comment(str1)[0], remain)
        self.assertEqual(lister.MetadataExtractor.process_internal_comment(str1)[1], comment)

    def test_process_section(self):
        list1 = ['Section', 'Preparation and Environment']
        processed_list = [['-', 'section level 0', 'Preparation and Environment', '', '']]
        self.assertListEqual(lister.MetadataExtractor.process_section(list1)[0], processed_list)


    def test_extract_flow_type(self):
        par_no = 2

        # TEST IF STATEMENT PARSING
        if_str1 = '<if|membrane simulation|e|true>'
        processed_if_list = [[2, 'step type', 'conditional', '', ''], [2, 'flow type', 'if', '', ''],
                             [2, 'flow parameter', 'membrane simulation', '', ''],
                             [2, 'flow logical parameter', 'e', '', ''],
                             [2, 'flow compared value', 'true', '', '']]
        self.assertListEqual(lister.MetadataExtractor.extract_flow_type(par_no, if_str1)[0],processed_if_list)

        # TEST SECTION PARSING
        sect_str0 = '<Section|Preparation and Environment>'
        sect_str1 = '<Subsection|Preparation and Environment>'
        sect_str2 = '<Subsubsection|Preparation and Environment>'
        sect_str3 = '<Subsubsubsection|Preparation and Environment>'
        sect_list = [sect_str0, sect_str1, sect_str2, sect_str3]
        pattern = r'<(.*?)\|'

        for sect_str in sect_list:
            match = re.findall(pattern, sect_str)
            if match:
                subsection_level = match[0].lower().count("sub")
                processed_sect_list = \
                    [['-', 'section level '+str(subsection_level), 'Preparation and Environment', '', '']]
                self.assertListEqual(lister.MetadataExtractor.extract_flow_type(par_no, sect_str)[0], processed_sect_list)
            else:
                "Test: no (sub)section found."
            print("SUB COUNT: " + str(subsection_level))

        # TEST FOREACH PARSING
        foreach_str1 = '<for each|cycles of minimization>'
        processed_foreach_list = [[par_no, 'step type', 'iteration', '', ''],
                                  [par_no, 'flow type', 'for each', '', ''],
                                  [par_no, 'flow parameter', 'cycles of minimization', '', '']]
        self.assertListEqual(lister.MetadataExtractor.extract_flow_type(par_no, foreach_str1)[0], processed_foreach_list)

        # TEST WHILE PARSING
        while_str1 = '<while|ph|lte|7>'
        processed_while_list = [[par_no, 'step type', 'iteration', '', ''],
                                [par_no, 'flow type', 'while', '', ''],
                                [par_no, 'flow parameter', 'ph', '', ''],
                                [par_no, 'flow logical parameter', 'lte', '', ''],
                                [par_no, 'flow compared value', '7', '', '']]
        self.assertListEqual(lister.MetadataExtractor.extract_flow_type(par_no, while_str1)[0], processed_while_list)

        # TEST FOR PARSING
        for_str1 = '<for|pH|[1-7]|+|1>'
        processed_for_list = [[par_no, 'step type', 'iteration', '', ''],
                              [par_no, 'flow type', 'for', '', ''],
                              [par_no, 'flow parameter', 'pH', '', ''],
                              [par_no, 'flow range', '[1-7]', '', ''],
                              [par_no, 'start iteration value', 1.0, '', ''],
                              [par_no, 'end iteration value', 7.0, '', ''],
                              [par_no, 'flow operation', '+', '', ''],
                              [par_no, 'flow magnitude', '1', '', '']]
        self.assertListEqual(lister.MetadataExtractor.extract_flow_type(par_no, for_str1)[0], processed_for_list)

        # TEST ELSE-IF PARSING
        elif_str1 = '<else if|pH|between|[8-12]>'
        processed_elif_list = [[par_no, 'step type', 'conditional', '', ''],
                               [par_no, 'flow type', 'else if', '', ''],
                               [par_no, 'flow parameter', 'pH', '', ''],
                               [par_no, 'flow logical parameter', 'between', '', ''],
                               [par_no, 'flow range', '[8-12]', '', ''],
                               [par_no, 'start iteration value', 8.0, '', ''],
                               [par_no, 'end iteration value', 12.0, '', '']]
        self.assertListEqual(lister.MetadataExtractor.extract_flow_type(par_no, elif_str1)[0], processed_elif_list)


        # TEST ELSE PARSING
        else_str1 = '<else>'
        processed_else_list = [[par_no, 'step type', 'conditional', '', ''],
                               [par_no, 'flow type', 'else', '', '']]
        self.assertListEqual(lister.MetadataExtractor.extract_flow_type(par_no, else_str1)[0], processed_else_list)


    def test_strip_unwanted_mvu_colons(self):
        # Test case 1: No surrounding colons
        word = "word_without_colons"
        expected_output = word
        self.assertEqual(lister.TextCleaner.strip_unwanted_mvu_colons(word), expected_output)

        # Test case 2: Surrounding colons
        word = ":word_with_colons:"
        expected_output = "word_with_colons"
        self.assertEqual(lister.TextCleaner.strip_unwanted_mvu_colons(word), expected_output)

    def test_split_by_separators(self):
        # Test case 1: Single separator
        text = "word1, word2, word3"
        separators = [","]
        expected_output = ["word1", "word2", "word3"]
        self.assertEqual(lister.GeneralHelper.split_by_separators(text, separators), expected_output)

        # Test case 2: Multiple separators
        text = "word1, word2; word3"
        separators = [",", ";"]
        expected_output = ["word1", "word2", "word3"]
        self.assertEqual(lister.GeneralHelper.split_by_separators(text, separators), expected_output)

        # Test case 3: No separators
        text = "word1 word2 word3"
        separators = [","]
        expected_output = ["word1 word2 word3"]
        self.assertEqual(lister.GeneralHelper.split_by_separators(text, separators), expected_output)

    def test_remove_table_tag(self):
        # Test case 1: HTML with no tables
        html_content = "<p>This is a test paragraph without tables.</p>"
        soup = BeautifulSoup(html_content, "html.parser")
        expected_output = soup
        self.assertEqual(lister.TextCleaner.remove_table_tag(soup), expected_output)

        # Test case 2: HTML with one table
        html_content = "<p>This is a test paragraph with a table.</p><table><tr><td>Cell 1</td><td>Cell 2</td></tr></table>"
        soup = BeautifulSoup(html_content, "html.parser")
        expected_output = BeautifulSoup("<p>This is a test paragraph with a table.</p>", "html.parser")
        self.assertEqual(lister.TextCleaner.remove_table_tag(soup), expected_output)

        # Test case 3: HTML with multiple tables
        html_content = "<p>Paragraph with multiple tables.</p><table><tr><td>Table 1</td></tr></table><table><tr><td>Table 2</td></tr></table>"
        soup = BeautifulSoup(html_content, "html.parser")
        expected_output = BeautifulSoup("<p>Paragraph with multiple tables.</p>", "html.parser")
        self.assertEqual(lister.TextCleaner.remove_table_tag(soup), expected_output)


    def test_get_attachment_long_name(self):
        img_path = "some_url?file=long_name_value"
        expected_long_name = "long_name_value"
        self.assertEqual(lister.ApiAccess.get_attachment_long_name_v2(img_path), expected_long_name)


    # def test_get_attachment_id(self):
    #     exp = {
    #         "uploads": [
    #             {"id": "1", "real_name": "attachment1.txt", "long_name": "long_name_1"},
    #             {"id": "2", "real_name": "attachment2.txt", "long_name": "long_name_2"}
    #         ]
    #     }
    #     content = MagicMock()
    #     content.img = {"src": "some_url?file=long_name_1"}
    #
    #     expected_upl_id = "1"
    #     expected_real_name = "attachment1.txt"
    #
    #     upl_id, real_name = lister.ApiAccess.get_attachment_id_v2(exp, content)
    #
    #     self.assertEqual(upl_id, expected_upl_id)
    #     self.assertEqual(real_name, expected_real_name)


    # @patch('lister.ApiAccess.get_attachment_long_name_v2')
    # def test_get_attachment_id_v2_correct_output(self, mock_get_attachment_long_name):
    #     # Mock the get_attachment_long_name response
    #     mock_get_attachment_long_name.return_value = "long_name"
    #
    #     # Create a mock experiment with a mock upload
    #     mock_exp = {"_uploads": [MagicMock(_long_name="long_name", _id="id", _real_name="real_name")]}
    #
    #     # Create a mock Tag with a mock img
    #     mock_tag = MagicMock()
    #     mock_img = MagicMock()
    #     mock_img.__dict__["src"] = "src"
    #     # mock_img["src"] = "src"
    #     mock_tag.img = mock_img
    #
    #     print("mock_exp")
    #     print([MagicMock(_long_name="long_name", _id="id", _real_name="real_name")].__str__())
    #
    #     # Call the method under test
    #     upl_id, real_name = lister.ApiAccess.get_attachment_id_v2(mock_exp, mock_tag)
    #
    #     # Assert that the method returns the correct upload ID and real name
    #     self.assertEqual(upl_id, "id")
    #     self.assertEqual(real_name, "real_name")


    # @patch('lister.ApiAccess.get_attachment_long_name_v2')
    # def test_get_attachment_id_v2_empty_strings_when_no_uploads(self, mock_get_attachment_long_name):
    #     # Mock the get_attachment_long_name response
    #     mock_get_attachment_long_name.return_value = "long_name"
    #
    #     # Create a mock experiment with no uploads
    #     mock_exp = {"_uploads": []}
    #
    #     # Create a mock Tag with a mock img
    #     mock_tag = MagicMock()
    #     mock_img = MagicMock()
    #     mock_img.__dict__["src"] = "src"
    #     mock_tag.img = mock_img
    #
    #     # Call the method under test
    #     upl_id, real_name = lister.ApiAccess.get_attachment_id_v2(mock_exp, mock_tag)
    #
    #     # Assert that the method returns empty strings for the upload ID and real name
    #     self.assertEqual(upl_id, "")
    #     self.assertEqual(real_name, "")


    # def test_create_elab_manager(self):
    #     current_endpoint = 'http://example.com'
    #     current_token = 'test_token'
    #     manager = lister.ApiAccess.create_elab_manager(current_endpoint, current_token)
    #
    #     self.assertIsInstance(manager, elabapy.Manager)
    #     self.assertEqual(manager.endpoint, current_endpoint)
    #     self.assertEqual(manager.token, current_token)
    #     self.assertFalse(manager.verify)



    # def test_get_resource_cat_and_title(self):
    #     endpoint = 'http://example.com'
    #     token = 'test_token'
    #     resource_item_no = 1
    #     expected_category = 'Sample Category'
    #     expected_title = 'Sample Title'
    #
    #     manager = MagicMock()
    #     manager.get_item.return_value = {'category': expected_category, 'title': expected_title}
    #
    #     with unittest.mock.patch('lister.ApiAccess.create_elab_manager', return_value=manager):
    #         category, title = lister.ApiAccess.get_resource_cat_and_title_v1(endpoint, token, resource_item_no)
    #
    #     self.assertEqual(category, expected_category)
    #     self.assertEqual(title, expected_title)


    def test_output_path_darwin(self):
        with unittest.mock.patch('platform.system', return_value='Darwin'):
            file_name = 'test_file.txt'
            expected_output_path = str(Path.home()) + "/Apps/lister/output/" + file_name
            output_path = lister.PathHelper.get_default_output_path(file_name)
            self.assertEqual(output_path, expected_output_path)

    def test_output_path_windows_linux(self):
        with unittest.mock.patch('platform.system', return_value='Windows'):
            file_name = 'test_file.txt'
            current_path = Path().resolve()
            expected_output_path = str(current_path) + "\\output"
            output_path = lister.PathHelper.get_default_output_path(file_name)
            self.assertEqual(output_path, expected_output_path)

        with unittest.mock.patch('platform.system', return_value='Linux'):
            file_name = 'test_file.txt'
            current_path = Path().resolve()
            expected_output_path = str(current_path) + "/output/"
            output_path = lister.PathHelper.get_default_output_path(file_name)
            self.assertEqual(output_path, expected_output_path)


    # def test_get_elab_exp(self):
    #     exp_number = 1
    #     current_endpoint = 'http://example.com'
    #     current_token = 'test_token'
    #
    #     manager = MagicMock()
    #     expected_exp = {'id': exp_number, 'title': 'Sample Experiment'}
    #
    #     manager.get_experiment.return_value = expected_exp
    #
    #     with patch('lister.ApiAccess.create_elab_manager', return_value=manager):
    #         result_manager, result_exp = lister.ApiAccess.get_elab_exp(exp_number, current_endpoint, current_token)
    #
    #     self.assertEqual(result_manager, manager)
    #     self.assertEqual(result_exp, expected_exp)


    @patch.object(elabapi_python.ExperimentsApi, 'get_experiment')
    def test_get_elab_exp_v2(self, mock_get_experiment):

        # Mock the API client
        mock_client = MagicMock(spec=elabapi_python.ApiClient)

        # Mock the experiment ID
        mock_id = 123

        # Mock the API response
        mock_response = MagicMock()
        mock_get_experiment.return_value = mock_response

        # Call the method
        result = lister.ApiAccess.get_elab_exp_v2(mock_client, mock_id)

        # Check if the method was called with the correct arguments
        mock_get_experiment.assert_called_once_with(mock_id, format='json')

        # Check if the returned value is correct
        self.assertEqual(result, mock_response)


    # def test_get_exp_info(self):
    #     exp = {
    #         'title': 'Sample Experiment',
    #         'date': '2021-01-01',
    #         'category': 'Sample Category',
    #         'fullname': 'John Doe',
    #         'tags': 'tag1, tag2'
    #     }
    #
    #     expected_nkvmu_pairs = [
    #         ["", "metadata section", "Experiment Info", "", ""],
    #         ["", "title", exp['title'], "", ""],
    #         ["", "creation date", exp['date'], "", ""],
    #         ["", "category", exp['category'], "", ""],
    #         ["", "author", exp['fullname'], "", ""],
    #         ["", "tags", exp['tags'], "", ""]
    #     ]
    #
    #     # print("expected_nkvmu_pairs: " + str(expected_nkvmu_pairs))
    #     result_nkvmu_pairs = lister.ApiAccess.get_exp_info(exp)
    #     #m print("result_nkvmu_pairs: " + str(result_nkvmu_pairs))
    #     self.assertEqual(result_nkvmu_pairs, expected_nkvmu_pairs)


    def test_get_exp_info_v2(self):

        # Mock the experiment
        mock_exp = MagicMock()
        mock_exp.__dict__ = {
            "_title": "Test Title",
            "_created_at": "2023-12-06",
            "_type": "Test Type",
            "_fullname": "Test Fullname",
            "_tags": "Test Tags"
        }

        # Call the method
        result = lister.ApiAccess.get_exp_info_v2(mock_exp)

        # Expected result
        expected_result = [
            ["", "metadata section", "Experiment Info", "", ""],
            ["", "title", "Test Title", "", ""],
            ["", "creation date", "2023-12-06", "", ""],
            ["", "category", "Test Type", "", ""],
            ["", "author", "Test Fullname", "", ""],
            ["", "tags", "Test Tags", "", ""]
        ]

        # Check if the returned value is correct
        self.assertEqual(result, expected_result)


    @patch('elabapi_python.ExperimentsApi.get_experiment')
    def test_get_exp_title_v2_returns_correct_title(self, mock_get_experiment):
        # Mock the API response
        mock_experiment = Mock()
        mock_experiment.__dict__["_title"] = "Test Experiment"
        mock_get_experiment.return_value = mock_experiment

        # Create a mock API client
        mock_apiv2client = Mock()

        # Call the method under test
        result = lister.ApiAccess.get_exp_title_v2(mock_apiv2client, 1)

        # Assert that the method returns the correct title
        self.assertEqual(result, "Test Experiment")

    @patch('elabapi_python.ExperimentsApi.get_experiment')
    def test_get_exp_title_v2_raises_error_when_experiment_not_found(self, mock_get_experiment):
        # Mock the API response to return None
        mock_get_experiment.return_value = None

        # Create a mock API client
        mock_apiv2client = Mock()

        # Call the method under test and assert that it raises an error
        with self.assertRaises(ValueError):
            lister.ApiAccess.get_exp_title_v2(mock_apiv2client, 1)


    # def test_get_exp_title(self):
    #     endpoint = 'http://example.com'
    #     token = 'test_token'
    #     exp_item_no = 1
    #     exp_title = 'Sample Experiment'
    #
    #     mock_exp = (None, {'title': exp_title})
    #
    #     with patch('lister.ApiAccess.get_elab_exp', return_value=mock_exp):
    #         result_title = lister.ApiAccess.get_exp_title(endpoint, token, exp_item_no)
    #
    #     self.assertEqual(result_title, exp_title)


    @patch.object(elabapi_python.ExperimentsApi, 'get_experiment')
    def test_get_exp_title_v2_success(self, mock_get_experiment):
        # Mock the get_experiment response
        mock_experiment = MagicMock()
        mock_experiment.__dict__["_title"] = "Test Experiment"
        mock_get_experiment.return_value = mock_experiment

        # Create a mock API client
        mock_apiv2client = MagicMock()

        # Call the method under test
        result = lister.ApiAccess.get_exp_title_v2(mock_apiv2client, 1)

        # Assert that the method returns the correct experiment title
        self.assertEqual(result, "Test Experiment")


    @patch.object(elabapi_python.ExperimentsApi, 'get_experiment')
    def test_get_exp_title_v2_error_experiment_not_found(self, mock_get_experiment):
        # Mock the get_experiment response to return None
        mock_get_experiment.return_value = None

        # Create a mock API client
        mock_apiv2client = MagicMock()

        # Call the method under test and assert that it raises an error
        with self.assertRaises(ValueError):
            lister.ApiAccess.get_exp_title_v2(mock_apiv2client, 1)



    @patch('bs4.BeautifulSoup')
    @patch('lister.TextCleaner.remove_empty_tags')
    def test_get_nonempty_body_tags_correct_output(self, mock_remove_empty_tags, mock_BeautifulSoup):
        # Mock the BeautifulSoup response
        mock_soup = MagicMock()
        mock_BeautifulSoup.return_value = mock_soup

        # Mock the remove_empty_tags response
        mock_remove_empty_tags.return_value = mock_soup

        # Create a mock experiment
        mock_exp = MagicMock()
        mock_exp.__dict__["_body"] = "<html></html>"

        # Call the method under test
        result = lister.TextCleaner.get_nonempty_body_tags_v2(mock_exp)
        print("RESULT: ")
        print(result)

        # Assert that the method returns the correct output
        expected_result = mock_soup.currentTag.tagStack[0].contents
        self.assertEqual(result, expected_result)


    @patch('bs4.BeautifulSoup')
    def test_get_nonempty_body_tags_error_when_body_is_none(self, mock_BeautifulSoup):
        # Mock the BeautifulSoup response to return None
        mock_BeautifulSoup.return_value = None

        # Create a mock experiment with a None body
        mock_exp = Mock()
        mock_exp.__dict__["_body"] = None

        # Call the method under test and assert that it raises an error
        with self.assertRaises(AttributeError):
            lister.TextCleaner.get_nonempty_body_tags_v2(mock_exp)


    def test_get_section_title(self):
        line = "1. Introduction"
        expected_title = "Introduction"
        result_title = lister.DocxHelper.get_section_title(line)
        self.assertEqual(result_title, expected_title)


    # def test_get_span_attr_val(self):
    #     c = MagicMock()
    #     c.get.return_value = "color: red;"
    #     expected_attr, expected_val = "color", "red"
    #     print(c.call_args)
    #     attr, val = lister.get_span_attr_val(c)
    #     print("attr, val")
    #     print(attr, val)
    #     self.assertEqual(attr, expected_attr)
    #     self.assertEqual(val, expected_val)

    @patch('re.findall')
    def test_get_span_attr_val(self, mock_findall):
        # Mock the re.findall response
        mock_findall.return_value = [("color", "#ffffff")]

        # Create a mock Tag
        mock_tag = Mock()
        mock_tag.get.return_value = "color:#ffffff;"

        # Call the method under test
        attr, val = lister.DocxHelper.get_span_attr_val(mock_tag)

        # Assert that the method returns the correct attribute and value
        self.assertEqual(attr, "color")
        self.assertEqual(val, "#ffffff")


    # def test_get_span_attr_val_no_match(self):
    #     c = MagicMock()
    #     c.get.return_value = "font-size: 12px;"
    #     with self.assertRaises(IndexError):
    #         lister.get_span_attr_val(c)


    def test_is_explicit_key_true(self):
        key = ":example_key:"
        self.assertTrue(lister.MetadataExtractor.is_explicit_key(key))


    def test_is_explicit_key_false(self):
        key = "not_explicit_key"
        self.assertFalse(lister.MetadataExtractor.is_explicit_key(key))


    # def test_latex_formula_to_docx(self):
    #     latex_formula = r'\frac{1}{2}'
    #
    #     with patch('latex2mathml.converter.convert') as mock_convert, \
    #          patch('etree.parse') as mock_etree_parse, \
    #          patch('etree.XSLT') as mock_etree_xslt:
    #
    #         mock_convert.return_value = '<mathml></mathml>'
    #         mock_etree_parse.return_value = MagicMock()
    #         mock_etree_xslt.return_value = MagicMock()
    #
    #         docx_formula, log = latex_formula_to_docx(latex_formula)
    #
    #         mock_convert.assert_called_once_with(latex_formula)
    #         mock_etree_parse.assert_called_once_with('MML2OMML.XSL')
    #         mock_etree_xslt.assert_called_once_with(mock_etree_parse.return_value)
    #
    #         self.assertIsNotNone(docx_formula)
    #         self.assertEqual(log, "")


    # def test_latex_formula_to_docx_missing_mml2omml(self):
    #     latex_formula = r'\frac{1}{2}'
    #
    #     with patch('latex2mathml.converter.convert') as mock_convert, \
    #          patch('etree.parse', side_effect=Exception()):
    #
    #         mock_convert.return_value = '<mathml></mathml>'
    #
    #         docx_formula, log = latex_formula_to_docx(latex_formula)
    #
    #         mock_convert.assert_called_once_with(latex_formula)
    #         self.assertIsNone(docx_formula)
    #         self.assertEqual(log, MiscAlertMsg.MISSING_MML2OMML.value)


    # @patch('latex2mathml.converter.convert')
    # @patch('lxml.etree.fromstring')
    # @patch('lxml.etree.parse')
    # @patch('lxml.etree.XSLT')
    # def test_latex_formula_to_docx(self, mock_XSLT, mock_parse, mock_fromstring, mock_convert):
    #     # Mock the convert function to return a specific MathML string
    #     mock_convert.return_value = "<mathml></mathml>"
    #
    #     # Mock the fromstring function to return a specific etree Element
    #     mock_fromstring.return_value = etree.Element("mathml")
    #
    #     # Mock the parse function to return a specific etree ElementTree
    #     mock_parse.return_value = etree.ElementTree(etree.Element("xslt"))
    #
    #     # Mock the XSLT function to return a specific XSLT object
    #     mock_XSLT.return_value = etree.XSLT(etree.ElementTree(etree.Element("xslt")))
    #
    #     # Call the method under test
    #     docx_formula, log = lister.DocxHelper.latex_formula_to_docx("x^2")
    #
    #     # Assert that the method returns the correct docx formula and an empty log
    #     self.assertEqual(docx_formula, etree.Element("mathml"))
    #     self.assertEqual(log, "")

    @patch('latex2mathml.converter.convert')
    @patch('lxml.etree.fromstring')
    @patch('lxml.etree.parse')
    def test_latex_formula_to_docx_missing_mml2omml(self, mock_parse, mock_fromstring, mock_convert):
        # Mock the convert function to return a specific MathML string
        mock_convert.return_value = "<mathml></mathml>"

        # Mock the fromstring function to return a specific etree Element
        mock_fromstring.return_value = etree.Element("mathml")

        # Mock the parse function to raise an exception
        mock_parse.side_effect = Exception("Missing stylesheet")

        # Call the method under test
        docx_formula, log = lister.DocxHelper.latex_formula_to_docx("x^2")

        # Assert that the method returns None for the docx formula and a log message indicating the error
        self.assertIsNone(docx_formula)
        self.assertEqual(log,
                         "WARNING: Formula is found on the experiment entry. Parsing this formula to docx file requires MML2OMML.XSL file from Microsoft Office to be put on the same directory as config.json file. It is currently downloadable from https://www.exefiles.com/en/xsl/mml2omml-xsl/, Otherwise, formula parsing is disabled.")


    def test_get_section_title_empty(self):
        line = "1."
        expected_title = ""
        result_title = lister.DocxHelper.get_section_title(line)
        self.assertEqual(result_title, expected_title)


    @patch('platform.system')
    def test_manage_input_path_darwin(self, mock_system):
        mock_system.return_value = 'Darwin'
        input_path = lister.PathHelper.manage_input_path()
        home = str(Path.home())
        expected_input_path = home + "/Apps/lister/"
        self.assertEqual(input_path, expected_input_path)


    @patch('platform.system')
    def test_manage_input_path_non_darwin(self, mock_system):
        mock_system.return_value = 'Windows'  # or any other non-Darwin platform
        input_path = lister.PathHelper.manage_input_path()
        self.assertEqual(input_path, "")


    @patch('platform.system')
    def test_manage_output_path_darwin(self, mock_system):
        mock_system.return_value = 'Darwin'
        dir_name = 'dir/'
        file_name = 'file'
        output_path = lister.PathHelper.manage_output_path(dir_name, file_name)
        expected_output_path = dir_name + file_name + "/"
        self.assertEqual(output_path, expected_output_path)


    @patch('platform.system')
    def test_manage_output_path_non_darwin(self, mock_system):
        mock_system.return_value = 'Windows'  # or any other non-Darwin platform
        dir_name = 'dir/'
        file_name = 'file'
        output_path = lister.PathHelper.manage_output_path(dir_name, file_name)
        expected_output_path = dir_name + "/" + file_name + "/"
        self.assertEqual(output_path, expected_output_path)


    @patch('builtins.open', new_callable=unittest.mock.mock_open,
           read_data='{"elabftw": {"token": "test_token", "endpoint": "test_endpoint", "exp_no": 1, '
                     '"output_file_name": "test_output", "resource_item_no": 2}}')
    def test_parse_cfg(self, mock_open):
        token, endpoint, output_file_name, exp_no, resource_item_no = lister.GUIHelper.parse_cfg()
        self.assertEqual(token, 'test_token')
        self.assertEqual(endpoint, 'test_endpoint')
        self.assertEqual(output_file_name, 'test_output')
        self.assertEqual(exp_no, 1)
        self.assertEqual(resource_item_no, 2)


    @patch('builtins.open', new_callable=unittest.mock.mock_open,
           read_data='{"elabftw": {"token": "test_token", "endpoint": "test_endpoint", "exp_no": 1, '
                     '"output_file_name": "test_output", "resource_item_no": 2}}')
    @patch('lister.GUIHelper.parse_gooey_args')
    def test_parse_gooey_args(self, mock_parse_gooey_args, mock_open):
        mock_parse_gooey_args.return_value = Namespace(command='parse_experiment', title=True, id=False,
                                                       base_output_dir='output/', exp_no=1,
                                                       endpoint='test_endpoint', token='test_token')
        args = lister.GUIHelper.parse_gooey_args()
        self.assertEqual(args.command, 'parse_experiment')
        self.assertTrue(args.title)
        self.assertFalse(args.id)
        self.assertEqual(args.base_output_dir, 'output/')
        self.assertEqual(args.exp_no, 1)
        self.assertEqual(args.endpoint, 'test_endpoint')
        self.assertEqual(args.token, 'test_token')


    def test_slugify(self):
        self.assertEqual(lister.PathHelper.slugify('Test String'), 'test-string')
        self.assertEqual(lister.PathHelper.slugify('Another_Test_String'), 'another_test_string')
        self.assertEqual(lister.PathHelper.slugify('More-Test_String'), 'more-test_string')
        self.assertEqual(lister.PathHelper.slugify('Test@String'), 'teststring')

   # def test_manage_output_path(self):
   #     self.assertEqual(lister.manage_output_path('/Users/testuser', 'output'), '/Users/testuser/output/')
   #     self.assertEqual(lister.manage_output_path('/Users/testuser', 'another_output'), '/Users/testuser/another_output/')


    def test_remove_table_tag(self):
        html_content = "<html><body><p>Hello</p><table><tr><td>world!</td></tr></table></body></html>"
        soup = BeautifulSoup(html_content, 'html.parser')
        result = lister.TextCleaner.remove_table_tag(soup)

        # Check that the resulting HTML does not contain any '<table>', '<tr>', or '<td>' tags
        self.assertNotIn('<table>', str(result))
        self.assertNotIn('<tr>', str(result))
        self.assertNotIn('<td>', str(result))

        # Also check that the content of the table tag ("world!") has been removed
        self.assertNotIn('world!', str(result))

        # Check that content outside the table tag ("Hello") is still present
        self.assertIn('Hello', str(result))


    def test_process_nbsp(self):
        html_content = "<html><body><p>Hello&nbsp;world!</p><p>How are&nbsp;you?</p></body></html>"
        soup = BeautifulSoup(html_content, 'html.parser')
        result = lister.TextCleaner.process_nbsp(soup)

        # Check that the resulting list of lines does not contain any non-breaking spaces
        for line in result:
            self.assertNotIn('\xa0', line)
        # TODO: put a space to replace <p> tags (or whether those additional spaces are needed at all)
        self.assertEqual(result, ["Hello world!How are you?"])


    # def test_conv_html_to_nkvmu(self):
    #     html_content = "<html><body><p>metadata section: Experiment Context</p></body></html>"
    #     result, log = lister.conv_html_to_nkvmu(html_content)
    #
    #     # The expected result is based on the assumption of how the dependent functions work
    #     expected_result = [[0, "metadata section", "Experiment Context", "", ""]]
    #
    #     self.assertEqual(result, expected_result)


    @patch('bs4.BeautifulSoup')
    @patch('lister.TextCleaner.remove_table_tag')
    @patch('lister.TextCleaner.process_nbsp')
    @patch('lister.MetadataExtractor.parse_lines_to_kv')
    def test_conv_html_to_nkvmu_returns_correct_output(self, mock_parse_lines_to_kv, mock_process_nbsp,
                                                  mock_remove_table_tag, mock_BeautifulSoup):
        # Mock the BeautifulSoup response
        mock_soup = Mock()
        mock_BeautifulSoup.return_value = mock_soup

        # Mock the remove_table_tag response
        mock_remove_table_tag.return_value = mock_soup

        # Mock the process_nbsp response
        mock_process_nbsp.return_value = ["line1", "line2"]

        # Mock the parse_lines_to_kv response
        mock_parse_lines_to_kv.return_value = (
        [["-", "section level 0", "Experiment Context", "", ""]], ["comment", "comment"], "")

        # Call the method under test
        result = lister.MetadataExtractor.conv_html_to_nkvmu("<html></html>")

        # Assert that the method returns the correct output
        expected_result = ([["-", "section level 0", "Experiment Context", "", ""]], "")
        self.assertEqual(result, expected_result)


    # @patch('bs4.BeautifulSoup')
    # @patch('lister.TextCleaner.remove_table_tag')
    # @patch('lister.TextCleaner.process_nbsp')
    # @patch('lister.MetadataExtractor.parse_lines_to_kv')
    # def test_conv_html_to_nkvmu_returns_empty_output_when_no_clean_lines(self, mock_parse_lines_to_kv, mock_process_nbsp,
    #                                                                 mock_remove_table_tag, mock_BeautifulSoup):
    #     # Mock the BeautifulSoup response
    #     mock_soup = Mock()
    #     mock_BeautifulSoup.return_value = mock_soup
    #
    #     # Mock the remove_table_tag response
    #     mock_remove_table_tag.return_value = mock_soup
    #
    #     # Mock the process_nbsp response to return None
    #     mock_process_nbsp.return_value = None
    #
    #     # Call the method under test
    #     result = lister.MetadataExtractor.conv_html_to_nkvmu("<html></html>")
    #
    #     # Assert that the method returns an empty output
    #     expected_result = ([], "")
    #     self.assertEqual(result, expected_result)


    def test_strip_unwanted_mvu_colons(self):
        # Test a word with surrounding colons
        word = ":Hello:"
        result = lister.TextCleaner.strip_unwanted_mvu_colons(word)
        self.assertEqual(result, "Hello")

        # Test a word without surrounding colons
        word = "World"
        result = lister.TextCleaner.strip_unwanted_mvu_colons(word)
        self.assertEqual(result, "World")

        # Test a word with only one surrounding colon
        word = ":Hello"
        result = lister.TextCleaner.strip_unwanted_mvu_colons(word)
        self.assertEqual(result, ":Hello")
        word = "Hello:"
        result = lister.TextCleaner.strip_unwanted_mvu_colons(word)
        self.assertEqual(result, "Hello:")

    def test_strip_colon(self):
        self.assertEqual(lister.TextCleaner.strip_colon("key:value"), "keyvalue")
        self.assertEqual(lister.TextCleaner.strip_colon("key::value"), "keyvalue")
        self.assertEqual(lister.TextCleaner.strip_colon("key"), "key")
        self.assertEqual(lister.TextCleaner.strip_colon(":key:"), "key")
        self.assertEqual(lister.TextCleaner.strip_colon(":"), "")


    def test_process_reg_bracket(self):
        # Test case 1: No comments or DOIs
        line = "This is a test line without comments or DOIs."
        expected_output = (line, [])
        self.assertEqual(lister.DocxHelper.process_reg_bracket(line), expected_output)

        # Test case 2: Invisible comment
        line = "This is a test line with an (_invisible comment_)."
        expected_output = ("This is a test line with an .", [])
        self.assertEqual(lister.DocxHelper.process_reg_bracket(line), expected_output)

        # Test case 3: Visible comment
        line = "This is a test line with a (:(visible comment):)."
        expected_output = ("This is a test line with a (visible comment).", [])
        self.assertEqual(lister.DocxHelper.process_reg_bracket(line), expected_output)

        # Test case 4: DOI
        line = "This is a test line with a DOI (10.1234/abcd)."
        # TODO: find more details about those parsing results that yield double spaces. Decide how to handle them.
        expected_output = ("This is a test line with a DOI  [1].", ["10.1234/abcd"])
        self.assertEqual(lister.DocxHelper.process_reg_bracket(line), expected_output)



    def test_strip_markup_and_explicit_keys(self):

        # Test case 1: No markup or explicit keys
        line = "This is a test line without markup or explicit keys."
        expected_output = (line, [])
        self.assertEqual(lister.TextCleaner.strip_markup_and_explicit_keys(line), expected_output)

        # Test case 2: Explicit keys
        line = "This is a test line with :explicit_key:."
        expected_output = ("This is a test line with  explicit_key.", [])
        self.assertEqual(lister.TextCleaner.strip_markup_and_explicit_keys(line), expected_output)

        # Test case 3: Markup and DOI
        line = "This is a test line with {markup} and a DOI (10.1234/abcd)."
        expected_output = ("This is a test line with markup and a DOI  [2].", ["10.1234/abcd"])
        # Note: the DOI index is set to be 2 because process_reg_bracket(), which adds +1 to the globally-declared
        # reference counter if a DOI is encountered, has already been called in test_process_reg_bracket().
        # further tests that call process_reg_bracket() and involves found DOI pattern will increment the reference
        # counter by 1.
        stripped_line, dois = lister.TextCleaner.strip_markup_and_explicit_keys(line)
        print("stripped_line: " + str(stripped_line) + "\ndois: " + str(dois))
        self.assertEqual((stripped_line, dois), expected_output)

    def test_conv_bracketedstring_to_kvmu(self):
        # Test a string with key and value
        kvmu = "{value|key}"
        result = lister.MetadataExtractor.conv_bracketedstring_to_kvmu(kvmu)
        self.assertEqual(result, ("key", "value", "", "", ""))

        # Test a string with value, unit, and key
        kvmu = "{value|unit|key}"
        result = lister.MetadataExtractor.conv_bracketedstring_to_kvmu(kvmu)
        self.assertEqual(result, ("key", "value", "", "unit", ""))

        # Test a string with measure, unit, value, and key
        kvmu = "{measure|unit|value|key}"
        result = lister.MetadataExtractor.conv_bracketedstring_to_kvmu(kvmu)
        self.assertEqual(result, ("key", "value", "measure", "unit", ""))

        # Test a string with no separators
        kvmu = "{value}"
        result = lister.MetadataExtractor.conv_bracketedstring_to_kvmu(kvmu)
        expected_log = "WARNING: A Key-Value split with length = 1 is found. This can be caused by a " \
                            "mathematical formula, which is okay and hence no KV pair is written to the metadata. " \
                            "Otherwise please check this pair: {0}."
        self.assertEqual(result, ("", "", "", "", expected_log.format(kvmu)))

        # Test a string with too many separators
        with self.assertRaises(SystemExit):
            kvmu = "{measure|unit|value|key|extra}"
            lister.MetadataExtractor.conv_bracketedstring_to_kvmu(kvmu)


    def test_validate_else(self):
        # Test valid input
        cf_split = ["else"]
        log, is_error = lister.Validator.validate_else(cf_split)
        self.assertEqual(log, "")
        self.assertFalse(is_error)

        # Test invalid input
        cf_split = ["else", "extra_arg"]
        log, is_error = lister.Validator.validate_else(cf_split)
        expected_log = lister.MiscAlertMsg.IMPROPER_ARGNO.value.format(
            cf_split[0].upper(), lister.ArgNum.ARG_NUM_ELSE.value, len(cf_split), cf_split)
        self.assertEqual(log, expected_log + "\n")
        self.assertTrue(is_error)


    def test_process_else(self):
        par_no = 1
        cf_split = ["else"]

        key_val, log, is_error = lister.MetadataExtractor.process_else(par_no, cf_split)
        self.assertEqual(log, "")
        self.assertFalse(is_error)
        self.assertEqual(key_val, [
            [par_no, "step type", "conditional", '', ''],
            [par_no, "flow type", "else", '', '']
        ])


    # def test_process_linked_resource_item_two_columns(self):
    #     manager = MagicMock()
    #     manager.get_item.return_value = {
    #         "body": "<table><tr><td>Key</td><td>Value</td></tr></table>",
    #         "category": "TestCategory"
    #     }
    #     id = 1
    #
    #     resource_item_nkvmu_metadata, log = lister.MetadataExtractor.process_linked_resource_item(manager, id)
    #
    #     self.assertEqual(log, "")
    #     self.assertEqual(resource_item_nkvmu_metadata, [
    #         ['', 'metadata section', 'TestCategory', '', ''],
    #         ['', 'Key', 'Value', '', '']
    #     ])


    # def test_process_linked_resource_item_not_two_columns(self):
    #     manager = MagicMock()
    #     manager.get_item.return_value = {
    #         "body": "<table><tr><td>Key</td><td>Value</td><td>Extra</td></tr></table>",
    #         "category": "TestCategory"
    #     }
    #     id = 1
    #
    #     resource_item_nkvmu_metadata, log = lister.MetadataExtractor.process_linked_resource_item(manager, id)
    #
    #     expected_log = lister.MiscAlertMsg.NON_TWO_COLS_LINKED_TABLE.value.format("TestCategory", 3) + "\n"
    #     self.assertEqual(log, expected_log)
    #     self.assertEqual(resource_item_nkvmu_metadata, "")


    # @patch('elabapi_python.ItemsApi.get_item')
    # @patch('pandas.read_html')
    # def test_linked_resource_item_returns_correct_metadata(self, mock_read_html, mock_get_item):
    #     # Mock the API response
    #     mock_item = Mock()
    #     mock_item.__dict__["_body"] = "<html></html>"
    #     mock_item.__dict__["_mainattr_title"] = "Test Category"
    #     mock_get_item.return_value = mock_item
    #
    #     # Mock the pandas read_html response
    #     mock_df = pd.DataFrame({'metadata section': ['key1', 'key2'], 'Test Category': ['value1', 'value2']})
    #     mock_read_html.return_value = [mock_df]
    #
    #     # Create a mock API client
    #     mock_apiv2client = Mock()
    #
    #     # Call the method under test
    #     result, _ = lister.MetadataExtractor.process_linked_resource_item_apiv2(mock_apiv2client, 1)
    #
    #     # Assert that the method returns the correct metadata
    #     expected_result = [['', 'metadata section', 'Test Category', '', ''], ['', 'key1', 'value1', '', ''],
    #                        ['', 'key2', 'value2', '', '']]
    #     self.assertEqual(result, expected_result)


    # @patch('elabapi_python.ItemsApi.get_item')
    # def test_linked_resource_item_raises_error_when_item_not_found(self, mock_get_item):
    #     # Mock the API response to return None
    #     mock_get_item.return_value = None
    #
    #     # Create a mock API client
    #     mock_apiv2client = Mock()
    #
    #     # Call the method under test and assert that it raises an error
    #     with self.assertRaises(ApiException):
    #         lister.MetadataExtractor.process_linked_resource_item_apiv2(mock_apiv2client, 1)


    def test_validate_range_valid(self):
        flow_range = "[1-10]"
        log, is_error = lister.Validator.validate_range(flow_range)
        self.assertEqual(log, "")
        self.assertFalse(is_error)


    def test_validate_range_invalid_not_two_args(self):
        flow_range = "[1-5-10]"
        log, is_error = lister.Validator.validate_range(flow_range)
        expected_log = lister.MiscAlertMsg.RANGE_NOT_TWO_ARGS.value.format(flow_range) + "\n"
        self.assertEqual(log, expected_log)
        self.assertTrue(is_error)


    def test_validate_range_invalid_not_numbers(self):
        flow_range = "[1a-10]"
        log, is_error = lister.Validator.validate_range(flow_range)
        expected_log = lister.MiscAlertMsg.RANGE_NOT_NUMBERS.value.format(flow_range) + "\n"
        self.assertEqual(log, expected_log)
        self.assertTrue(is_error)


    def test_process_range(self):
        flow_range = "[1-10]"
        range_start, range_end, log, is_error = lister.MetadataExtractor.process_range(flow_range)
        self.assertEqual(range_start, 1)
        self.assertEqual(range_end, 10)
        self.assertEqual(log, "")
        self.assertFalse(is_error)


    # def test_parse_lines_to_kv(self):
    #     lines = ["metadata section: Experiment Context"]
    #     result, internal_comments, log = lister.parse_lines_to_kv(lines)
    #
    #     # The expected result is based on the assumption of how the dependent functions work
    #     expected_result = [[0, "metadata section", "Experiment Context", "", ""]]
    #
    #     self.assertEqual(result, expected_result)


    # @patch('lister.MetadataExtractor.process_internal_comment')
    # @patch('lister.MetadataExtractor.conv_bracketedstring_to_kvmu')
    # @patch('lister.MetadataExtractor.extract_flow_type')
    # @patch('lister.GeneralHelper.split_into_sentences')
    # @patch('lister.Validator.check_bracket_num')
    # def test_parse_lines_to_kv_happy_path(self, mock_check_bracket_num, mock_split_into_sentences, mock_extract_flow_type, mock_conv_bracketedstring_to_kvmu, mock_process_internal_comment):
    #     # Arrange
    #     mock_check_bracket_num.return_value = ("", False)
    #     mock_split_into_sentences.return_value = ["sentence1", "sentence2"]
    #     mock_extract_flow_type.return_value = ([["-", "section level 0", "Experiment Context", "", ""]], "", False)
    #     mock_conv_bracketedstring_to_kvmu.return_value = ("key", "value", "measure", "unit", "")
    #     mock_process_internal_comment.return_value = ("key", "comment")
    #     lines = ["line1", "line2"]
    #
    #     # Act
    #     result = lister.MetadataExtractor.parse_lines_to_kv(lines)
    #
    #     # Assert
    #     self.assertEqual(result, ([["-", "section level 0", "Experiment Context", "", ""], ["1", "key", "value", "measure", "unit"]], ["comment", "comment"], ""))


    # @patch('lister.MetadataExtractor.process_internal_comment')
    # @patch('lister.MetadataExtractor.conv_bracketedstring_to_kvmu')
    # @patch('lister.MetadataExtractor.extract_flow_type')
    # @patch('lister.GeneralHelper.split_into_sentences')
    # @patch('lister.Validator.check_bracket_num')
    # def test_parse_lines_to_kv_bracket_error(self, mock_check_bracket_num, mock_split_into_sentences, mock_extract_flow_type, mock_conv_bracketedstring_to_kvmu, mock_process_internal_comment):
    #     # Arrange
    #     mock_check_bracket_num.return_value = ("Bracket error", True)
    #     mock_split_into_sentences.return_value = ["sentence1", "sentence2"]
    #     mock_extract_flow_type.return_value = ([["-", "section level 0", "Experiment Context", "", ""]], "", False)
    #     mock_conv_bracketedstring_to_kvmu.return_value = ("key", "value", "measure", "unit", "")
    #     mock_process_internal_comment.return_value = ("key", "comment")
    #     lines = ["line1", "line2"]
    #
    #     # Act
    #     result = lister.MetadataExtractor.parse_lines_to_kv(lines)
    #
    #     # Assert
    #     self.assertEqual(result, ([], [], "Bracket error"))


    def test_remove_empty_tags(self):
        # Test case 1: HTML with no empty tags
        html_content = "<p>This is a test paragraph without empty tags.</p>"
        soup = BeautifulSoup(html_content, "html.parser")
        expected_output = soup
        # typecasting due to the fact that BeautifulSoup objects are not comparable
        self.assertEqual(str(lister.TextCleaner.remove_empty_tags(soup)), str(expected_output))

        # Test case 2: HTML with empty tags
        html_content = "<p>This is a test paragraph with <span></span> empty tags.</p>"
        soup = BeautifulSoup(html_content, "html.parser")
        expected_output = BeautifulSoup("<p>This is a test paragraph with  empty tags.</p>", "html.parser")
        # typecasting due to the fact that BeautifulSoup objects are not comparable
        self.assertEqual(str(lister.TextCleaner.remove_empty_tags(soup)), str(expected_output))

        # Test case 3: HTML with nested empty tags
        html_content = "<p>This is a test paragraph with <span><i></i></span> nested empty tags.</p>"
        soup = BeautifulSoup(html_content, "html.parser")
        expected_output = BeautifulSoup("<p>This is a test paragraph with  nested empty tags.</p>", "html.parser")
        # typecasting due to the fact that BeautifulSoup objects are not comparable
        self.assertEqual(str(lister.TextCleaner.remove_empty_tags(soup)), str(expected_output))


    def test_remove_extra_spaces(self):
        # Test case 1: String with no extra spaces
        input_string = "This is a test string without extra spaces."
        expected_output = "This is a test string without extra spaces."
        self.assertEqual(lister.TextCleaner.remove_extra_spaces(input_string), expected_output)

        # Test case 2: String with extra spaces
        input_string = "This  is  a  test  string  with  extra  spaces."
        expected_output = "This is a test string with extra spaces."
        self.assertEqual(lister.TextCleaner.remove_extra_spaces(input_string), expected_output)

        # Test case 3: String with leading and trailing spaces
        input_string = "  This is a test string with leading and trailing spaces.  "
        expected_output = " This is a test string with leading and trailing spaces. "
        self.assertEqual(lister.TextCleaner.remove_extra_spaces(input_string), expected_output)


    def setUp(self):
        self.test_path = "test_path"
        self.log_text = "This is a test log."

    def tearDown(self):
        if os.path.exists(self.test_path):
            shutil.rmtree(self.test_path)

    def test_write_log(self):
        lister.Serializer.write_log(self.log_text, self.test_path)
        self.assertTrue(os.path.isfile(f"{self.test_path}/lister-report.log"))

        with open(f"{self.test_path}/lister-report.log", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, self.log_text)


    def test_process_while(self):
        # Test case 1: valid input
        par_no = 1
        cf_split = ["while", "param", "lt", "10"]
        key_val, log, is_error = lister.MetadataExtractor.process_while(par_no, cf_split)
        self.assertFalse(is_error, "Error flag should be False for valid input")
        self.assertEqual(log, "", "Log should be empty for valid input")
        self.assertEqual(len(key_val), 5, "There should be 5 key-value pairs for valid input")

        # Test case 2: invalid input (wrong number of elements)
        cf_split = ["while", "param", "lt"]
        with self.assertRaises(SystemExit):
            lister.MetadataExtractor.process_while(par_no, cf_split)


    def test_process_iterate(self):
        # Test case 1: Valid input
        par_no = 1
        cf_split = ["iterate", "+", "1"]
        key_val, iterate_log, is_error = lister.MetadataExtractor.process_iterate(par_no, cf_split)
        self.assertEqual(len(key_val), 3)
        self.assertEqual(iterate_log, "")
        self.assertFalse(is_error)

        # Test case 2: Invalid input (missing elements)
        par_no = 1
        cf_split = ["iterate", "+"]
        key_val, iterate_log, is_error = lister.MetadataExtractor.process_iterate(par_no, cf_split)
        self.assertEqual(len(key_val), 2)
        self.assertTrue(is_error)


# NOTE: many of the remaining functions are not tested because they are either too complicated for unit test
# or require interactions with GUI components. Some of these functions are: write_to_docx(), write_to_json(),
# write_to_xlsx(), parse_lines_to_kv(), get_text_width(), add_table_to_doc(), add_img_to_doc()
# TODO: process_ref_resource_item_v2(), process_iterate(), process_foreach(), process_for(), process_experiment()


if __name__ == '__main__':
    unittest.main()
