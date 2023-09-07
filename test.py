import re
import unittest
import lister
from bs4 import BeautifulSoup
import elabapi_python
import elabapy
import os
from unittest.mock import MagicMock, patch

class Test_lister(unittest.TestCase):


    def test_get_api_v2endpoint(self):
        v1endpoint = 'http://example.com/v1'
        expected_v2endpoint = 'https://example.com/v2'
        self.assertEqual(lister.get_api_v2endpoint(v1endpoint), expected_v2endpoint)


    def test_create_apiv2_client(self):
        endpoint = 'http://example.com/v1'
        token = 'test_token'
        apiv2_client = lister.create_apiv2_client(endpoint, token)

        self.assertIsInstance(apiv2_client, elabapi_python.ApiClient)
        self.assertEqual(apiv2_client.configuration.host, 'https://example.com/v2')
        self.assertEqual(apiv2_client.configuration.api_key['api_key'], token)
        self.assertEqual(apiv2_client.configuration.api_key_prefix['api_key'], 'Authorization')
        self.assertFalse(apiv2_client.configuration.debug)
        self.assertFalse(apiv2_client.configuration.verify_ssl)


    def test_derive_fname_from_exp(self):
        exp = {"title": "Example Experiment Title"}
        expected_fname = "example-experiment-title"
        self.assertEqual(lister.derive_fname_from_exp(exp), expected_fname)


    def test_create_elab_manager(self):
        current_endpoint = 'http://example.com'
        current_token = 'test_token'
        manager = lister.create_elab_manager(current_endpoint, current_token)
        self.assertIsInstance(manager, elabapy.Manager)


    @patch('os.path.isdir')
    @patch('os.makedirs')
    def test_check_and_create_path(self, mock_makedirs, mock_isdir):
        # Test when the directory exists
        mock_isdir.return_value = True
        path = '/path/to/directory'
        lister.check_and_create_path(path)
        mock_isdir.assert_called_with(path)
        mock_makedirs.assert_not_called()

        # Test when the directory does not exist
        mock_isdir.return_value = False
        lister.check_and_create_path(path)
        mock_isdir.assert_called_with(path)
        mock_makedirs.assert_called_with(path)


    @patch('lister.check_and_create_path')
    @patch('os.path.isdir')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_get_and_save_attachments(self, mock_open, mock_isdir, mock_check_and_create_path):
        manager = MagicMock()
        uploads = [
            {"id": "1", "real_name": "attachment1.txt"},
            {"id": "2", "real_name": "attachment2.txt"}
        ]
        path = '/path/to/directory'

        mock_isdir.return_value = True
        manager.get_upload.side_effect = [b'content1', b'content2']

        lister.get_and_save_attachments(manager, uploads, path)

        mock_check_and_create_path.assert_called_with(path + '/attachments/')
        manager.get_upload.assert_any_call("1")
        manager.get_upload.assert_any_call("2")
        mock_open.assert_any_call(path + '/attachments/attachment1.txt', 'wb')
        mock_open.assert_any_call(path + '/attachments/attachment2.txt', 'wb')
        mock_open().write.assert_any_call(b'content1')
        mock_open().write.assert_any_call(b'content2')


    @patch('lister.check_and_create_path')
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

        lister.get_and_save_attachments_apiv2(path, apiv2_client, exp_id)

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
        self.assertListEqual(lister.split_into_sentences(content), sentences)

    def test_is_valid_comparative_operator(self):
        self.assertTrue(lister.is_valid_comparative_operator("e"))
        self.assertTrue(lister.is_valid_comparative_operator("ne"))
        self.assertTrue(lister.is_valid_comparative_operator("gt"))
        self.assertTrue(lister.is_valid_comparative_operator("between"))
        self.assertTrue(lister.is_valid_comparative_operator("gte"))
        self.assertTrue(lister.is_valid_comparative_operator("lt"))
        self.assertTrue(lister.is_valid_comparative_operator("lte"))
        self.assertFalse(lister.is_valid_comparative_operator("="))
        self.assertFalse(lister.is_valid_comparative_operator("<"))
        self.assertFalse(lister.is_valid_comparative_operator(">"))
        self.assertFalse(lister.is_valid_comparative_operator(">="))
        self.assertFalse(lister.is_valid_comparative_operator("<="))

    def test_is_valid_iteration_operator(self):
        self.assertTrue(lister.is_valid_iteration_operator("+"))
        self.assertTrue(lister.is_valid_iteration_operator("-"))
        self.assertTrue(lister.is_valid_iteration_operator("*"))
        self.assertTrue(lister.is_valid_iteration_operator("/"))
        self.assertTrue(lister.is_valid_iteration_operator("%"))
        self.assertFalse(lister.is_valid_iteration_operator("substract"))
        self.assertFalse(lister.is_valid_iteration_operator("add"))
        self.assertFalse(lister.is_valid_iteration_operator("multiply"))
        self.assertFalse(lister.is_valid_iteration_operator("divide"))
        self.assertFalse(lister.is_valid_iteration_operator("modulo"))

    def test_is_num(self):
        self.assertTrue(lister.is_num("1"))
        self.assertTrue(lister.is_num(1))
        self.assertFalse(lister.is_num('A1'))

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
        self.assertFalse(lister.check_bracket_num(par_no, line)[1])
        self.assertTrue(lister.check_bracket_num(par_no, line2)[1])

    def test_validate_foreach(self):
        pair = ['for each', 'cycles of minimization']
        pair2 = ['for each']
        self.assertFalse(lister.validate_foreach(pair)[1])
        self.assertTrue(lister.validate_foreach(pair2)[1])

    def test_validate_while(self):
        list1 = ['while', 'ph', 'lte', '7']
        list2 = ['while', 'ph', '7']
        self.assertFalse(lister.validate_while(list1)[1])
        self.assertTrue(lister.validate_while(list2)[1])

    def test_validate_if(self):
        list1 = ['if', 'membrane simulation', 'e', 'True']
        list2 = ['if', 'membrane simulation', 'True']
        self.assertFalse(lister.validate_if(list1)[1])
        self.assertTrue(lister.validate_if(list2)[1])

    def test_validate_elseif(self):
        list1 = ['elif', 'membrane simulation', 'e', 'false']
        list2 = ['elif', 'membrane simulation', '=', 'false']
        list3 = ['elif', 'membrane simulation', 'false']
        self.assertFalse(lister.validate_elseif(list1)[1])
        self.assertTrue(lister.validate_elseif(list2)[1])
        self.assertTrue(lister.validate_elseif(list3)[1])

    def test_validate_else(self):
        list1 = ['else']
        list2 = ['else', "1"]
        self.assertFalse(lister.validate_else(list1)[1])
        self.assertTrue(lister.validate_else(list2)[1])

    def test_validate_range(self):
        pass  # waiting for a use case

    def test_validate_for(self):
        list1 = ['for', 'pH', '[1-7]', '+', '1']
        list2 = ['for', 'pH', '[1-7]', '1']
        self.assertFalse(lister.validate_for(list1)[1])
        self.assertTrue(lister.validate_for(list2)[1])

    def test_validate_iterate(self):
        pass  # needs more use case

    def test_validate_section(self):
        list1 = ['Section', 'Preparation and Environment']
        list2 = ['Section']
        self.assertFalse(lister.validate_section(list1)[1])
        self.assertTrue(lister.validate_section(list2)[1])

    def test_process_foreach(self):
        list1 = ['for each', 'cycles of minimization']
        par_no = 8
        processed_list = [[8, 'step type', 'iteration', '', ''],
                          [8, 'flow type', 'for each', '', ''],
                          [8, 'flow parameter', 'cycles of minimization', '', '']]
        self.assertListEqual(lister.process_foreach(par_no, list1)[0], processed_list)

    def test_process_while(self):
        pass # needs more use case

    def test_process_if(self):
        list1 = ['if', 'membrane simulation', 'e', 'true']
        par_no = 2
        processed_list = [[2, 'step type', 'conditional', '', ''],
                          [2, 'flow type', 'if', '', ''],
                          [2, 'flow parameter', 'membrane simulation', '', ''],
                          [2, 'flow logical parameter', 'e', '', ''],
                          [2, 'flow compared value', 'true', '', '']]
        self.assertListEqual(lister.process_if(par_no, list1)[0], processed_list)

    def test_process_elseif(self):
        list1 = ['elif', 'membrane simulation', 'e', 'false']
        par_no = 2
        processed_list = [[2, 'step type', 'conditional', '', ''],
                          [2, 'flow type', 'elif', '', ''],
                          [2, 'flow parameter', 'membrane simulation', '', ''],
                          [2, 'flow logical parameter', 'e', '', ''],
                          [2, 'flow compared value', 'false', '', '']]
        self.assertListEqual(lister.process_elseif(par_no, list1)[0], processed_list)


    def test_process_internal_comment(self):
        str1 = "molecular dynamics (MD)"
        comment = '(MD)'
        remain  = 'molecular dynamics'
        self.assertEqual(lister.process_internal_comment(str1)[0], remain)
        self.assertEqual(lister.process_internal_comment(str1)[1], comment)

    def test_process_section(self):
        list1 = ['Section', 'Preparation and Environment']
        processed_list = [['-', 'section level 0', 'Preparation and Environment', '', '']]
        self.assertListEqual(lister.process_section(list1)[0], processed_list)


    def test_extract_flow_type(self):
        par_no = 2

        # TEST IF STATEMENT PARSING
        if_str1 = '<if|membrane simulation|e|true>'
        processed_if_list = [[2, 'step type', 'conditional', '', ''], [2, 'flow type', 'if', '', ''],
                             [2, 'flow parameter', 'membrane simulation', '', ''],
                             [2, 'flow logical parameter', 'e', '', ''],
                             [2, 'flow compared value', 'true', '', '']]
        self.assertListEqual(lister.extract_flow_type(par_no, if_str1)[0],processed_if_list)

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
                self.assertListEqual(lister.extract_flow_type(par_no, sect_str)[0], processed_sect_list)
            else:
                "Test: no (sub)section found."
            print("SUB COUNT: " + str(subsection_level))

        # TEST FOREACH PARSING
        foreach_str1 = '<for each|cycles of minimization>'
        processed_foreach_list = [[par_no, 'step type', 'iteration', '', ''],
                                  [par_no, 'flow type', 'for each', '', ''],
                                  [par_no, 'flow parameter', 'cycles of minimization', '', '']]
        self.assertListEqual(lister.extract_flow_type(par_no, foreach_str1)[0], processed_foreach_list)

        # TEST WHILE PARSING
        while_str1 = '<while|ph|lte|7>'
        processed_while_list = [[par_no, 'step type', 'iteration', '', ''],
                                [par_no, 'flow type', 'while', '', ''],
                                [par_no, 'flow parameter', 'ph', '', ''],
                                [par_no, 'flow logical parameter', 'lte', '', ''],
                                [par_no, 'flow compared value', '7', '', '']]
        self.assertListEqual(lister.extract_flow_type(par_no, while_str1)[0], processed_while_list)

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
        self.assertListEqual(lister.extract_flow_type(par_no, for_str1)[0], processed_for_list)

        # TEST ELSE-IF PARSING
        elif_str1 = '<else if|pH|between|[8-12]>'
        processed_elif_list = [[par_no, 'step type', 'conditional', '', ''],
                               [par_no, 'flow type', 'else if', '', ''],
                               [par_no, 'flow parameter', 'pH', '', ''],
                               [par_no, 'flow logical parameter', 'between', '', ''],
                               [par_no, 'flow range', '[8-12]', '', ''],
                               [par_no, 'start iteration value', 8.0, '', ''],
                               [par_no, 'end iteration value', 12.0, '', '']]
        self.assertListEqual(lister.extract_flow_type(par_no, elif_str1)[0], processed_elif_list)


        # TEST ELSE PARSING
        else_str1 = '<else>'
        processed_else_list = [[par_no, 'step type', 'conditional', '', ''],
                               [par_no, 'flow type', 'else', '', '']]
        self.assertListEqual(lister.extract_flow_type(par_no, else_str1)[0], processed_else_list)


    def test_strip_unwanted_mvu_colons(self):
        # Test case 1: No surrounding colons
        word = "word_without_colons"
        expected_output = word
        self.assertEqual(lister.strip_unwanted_mvu_colons(word), expected_output)

        # Test case 2: Surrounding colons
        word = ":word_with_colons:"
        expected_output = "word_with_colons"
        self.assertEqual(lister.strip_unwanted_mvu_colons(word), expected_output)

    def test_split(self):
        # Test case 1: Single separator
        text = "word1, word2, word3"
        separators = [","]
        expected_output = ["word1", "word2", "word3"]
        self.assertEqual(lister.split(text, separators), expected_output)

        # Test case 2: Multiple separators
        text = "word1, word2; word3"
        separators = [",", ";"]
        expected_output = ["word1", "word2", "word3"]
        self.assertEqual(lister.split(text, separators), expected_output)

        # Test case 3: No separators
        text = "word1 word2 word3"
        separators = [","]
        expected_output = ["word1 word2 word3"]
        self.assertEqual(lister.split(text, separators), expected_output)

    def test_remove_table_tag(self):
        # Test case 1: HTML with no tables
        html_content = "<p>This is a test paragraph without tables.</p>"
        soup = BeautifulSoup(html_content, "html.parser")
        expected_output = soup
        self.assertEqual(lister.remove_table_tag(soup), expected_output)

        # Test case 2: HTML with one table
        html_content = "<p>This is a test paragraph with a table.</p><table><tr><td>Cell 1</td><td>Cell 2</td></tr></table>"
        soup = BeautifulSoup(html_content, "html.parser")
        expected_output = BeautifulSoup("<p>This is a test paragraph with a table.</p>", "html.parser")
        self.assertEqual(lister.remove_table_tag(soup), expected_output)

        # Test case 3: HTML with multiple tables
        html_content = "<p>Paragraph with multiple tables.</p><table><tr><td>Table 1</td></tr></table><table><tr><td>Table 2</td></tr></table>"
        soup = BeautifulSoup(html_content, "html.parser")
        expected_output = BeautifulSoup("<p>Paragraph with multiple tables.</p>", "html.parser")
        self.assertEqual(lister.remove_table_tag(soup), expected_output)

    def test_conv_html_to_nkvmu(self):

        pass

        # TODO: check the flow again surrounding creating metadata headers for the first paragraph which now creates:
        #  [['', 'metadata section', 'Experiment Context', '', '']] - find alternative options.

        # # Test case 1: HTML with no tables
        # html_content = "<p>This is a test paragraph without tables.</p>"
        # expected_output = ([
        #     ["", "section", "This is a test paragraph without tables.", "", ""]
        # ], "")
        # self.assertEqual(lister.conv_html_to_nkvmu(html_content), expected_output)

        # # Test case 2: HTML with one table
        # html_content = "<p>This is a test paragraph with a table.</p><table><tr><td>Cell 1</td><td>Cell 2</td></tr></table>"
        # expected_output = ([
        #     ["", "section", "This is a test paragraph with a table.", "", ""]
        # ], "")
        # self.assertEqual(lister.conv_html_to_nkvmu(html_content), expected_output)
        #
        # # Test case 3: HTML with multiple tables
        # html_content = "<p>Paragraph with multiple tables.</p><table><tr><td>Table 1</td></tr></table><table><tr><td>Table 2</td></tr></table>"
        # expected_output = ([
        #     ["", "section", "Paragraph with multiple tables.", "", ""]
        # ], "")
        # self.assertEqual(lister.conv_html_to_nkvmu(html_content), expected_output)


    def test_get_elab_exp_lines(self):
        pass #  not applicable

    def test_extract_elab_exp_content(self):
        pass # not applicable

    def test_get_docx_par_list(self):
        pass # not applicable

    def test_process_else(self):
        # list1 = ['else'] # needs more use cases
        pass

    def test_process_range(self):
        pass  # needs more use case

    def test_process_for(self):
        pass  # needs more use case

    def test_process_iterate(self):
        pass  # needs more use case

    def test_extract_docx_content(self):
        pass # not applicable

    def test_get_docx_content(self):
        pass # not applicable

    def test_slugify(self):
        self.assertEqual(lister.slugify('Test String'), 'test-string')
        self.assertEqual(lister.slugify('Another_Test_String'), 'another_test_string')
        self.assertEqual(lister.slugify('More-Test_String'), 'more-test_string')
        self.assertEqual(lister.slugify('Test@String'), 'teststring')

   # def test_manage_output_path(self):
   #     self.assertEqual(lister.manage_output_path('/Users/testuser', 'output'), '/Users/testuser/output/')
   #     self.assertEqual(lister.manage_output_path('/Users/testuser', 'another_output'), '/Users/testuser/another_output/')

    def test_remove_table_tag(self):
        html_content = "<html><body><p>Hello</p><table><tr><td>world!</td></tr></table></body></html>"
        soup = BeautifulSoup(html_content, 'html.parser')
        result = lister.remove_table_tag(soup)

        # Check that the resulting HTML does not contain any '<table>', '<tr>', or '<td>' tags
        self.assertNotIn('<table>', str(result))
        self.assertNotIn('<tr>', str(result))
        self.assertNotIn('<td>', str(result))

        # Also check that the content of the table tag ("world!") has been removed
        self.assertNotIn('world!', str(result))

        # Check that content outside the table tag ("Hello") is still present
        self.assertIn('Hello', str(result))

    # def test_process_nbsp(self):
    #     html_content = "<html><body><p>Hello&nbsp;world!</p><p>How are&nbsp;you?</p></body></html>"
    #     soup = BeautifulSoup(html_content, 'html.parser')
    #     result = lister.process_nbsp(soup)
    #
    #     # Check that the resulting list of lines does not contain any non-breaking spaces
    #     for line in result:
    #         self.assertNotIn('\xa0', line)
    #
    #     # Check that the non-breaking spaces have been replaced with regular spaces
    #     self.assertEqual(result, ["Hello world!", "How are you?"])

    # def test_conv_html_to_nkvmu(self):
    #     html_content = "<html><body><p>metadata section: Experiment Context</p></body></html>"
    #     result, log = lister.conv_html_to_nkvmu(html_content)
    #
    #     # The expected result is based on the assumption of how the dependent functions work
    #     expected_result = [[0, "metadata section", "Experiment Context", "", ""]]
    #
    #     self.assertEqual(result, expected_result)

    def test_strip_unwanted_mvu_colons(self):
        # Test a word with surrounding colons
        word = ":Hello:"
        result = lister.strip_unwanted_mvu_colons(word)
        self.assertEqual(result, "Hello")

        # Test a word without surrounding colons
        word = "World"
        result = lister.strip_unwanted_mvu_colons(word)
        self.assertEqual(result, "World")

        # Test a word with only one surrounding colon
        word = ":Hello"
        result = lister.strip_unwanted_mvu_colons(word)
        self.assertEqual(result, ":Hello")
        word = "Hello:"
        result = lister.strip_unwanted_mvu_colons(word)
        self.assertEqual(result, "Hello:")

    def test_strip_colon(self):
        self.assertEqual(lister.strip_colon("key:value"), "keyvalue")
        self.assertEqual(lister.strip_colon("key::value"), "keyvalue")
        self.assertEqual(lister.strip_colon("key"), "key")
        self.assertEqual(lister.strip_colon(":key:"), "key")
        self.assertEqual(lister.strip_colon(":"), "")


    def test_process_reg_bracket(self):
        # Test case 1: No comments or DOIs
        line = "This is a test line without comments or DOIs."
        expected_output = (line, [])
        self.assertEqual(lister.process_reg_bracket(line), expected_output)

        # Test case 2: Invisible comment
        line = "This is a test line with an (_invisible comment_)."
        expected_output = ("This is a test line with an .", [])
        self.assertEqual(lister.process_reg_bracket(line), expected_output)

        # Test case 3: Visible comment
        line = "This is a test line with a (:(visible comment):)."
        expected_output = ("This is a test line with a (visible comment).", [])
        self.assertEqual(lister.process_reg_bracket(line), expected_output)

        # Test case 4: DOI
        line = "This is a test line with a DOI (10.1234/abcd)."
        # TODO: find more details about those parsing results that yield double spaces. Decide how to handle them.
        expected_output = ("This is a test line with a DOI  [1].", ["10.1234/abcd"])
        self.assertEqual(lister.process_reg_bracket(line), expected_output)



    def test_strip_markup_and_explicit_keys(self):

        # Test case 1: No markup or explicit keys
        line = "This is a test line without markup or explicit keys."
        expected_output = (line, [])
        self.assertEqual(lister.strip_markup_and_explicit_keys(line), expected_output)

        # Test case 2: Explicit keys
        line = "This is a test line with :explicit_key:."
        expected_output = ("This is a test line with  explicit_key.", [])
        self.assertEqual(lister.strip_markup_and_explicit_keys(line), expected_output)

        # Test case 3: Markup and DOI
        line = "This is a test line with {markup} and a DOI (10.1234/abcd)."
        expected_output = ("This is a test line with markup and a DOI  [2].", ["10.1234/abcd"])
        # Note: the DOI index is set to be 2 because process_reg_bracket(), which adds +1 to the globally-declared
        # reference counter if a DOI is encountered, has already been called in test_process_reg_bracket().
        # further tests that call process_reg_bracket() and involves found DOI pattern will increment the reference
        # counter by 1.
        stripped_line, dois = lister.strip_markup_and_explicit_keys(line)
        print("stripped_line: " + str(stripped_line) + "\ndois: " + str(dois))
        self.assertEqual((stripped_line, dois), expected_output)

    def test_conv_bracketedstring_to_kvmu(self):
        # Test a string with key and value
        kvmu = "{value|key}"
        result = lister.conv_bracketedstring_to_kvmu(kvmu)
        self.assertEqual(result, ("key", "value", "", "", ""))

        # Test a string with value, unit, and key
        kvmu = "{value|unit|key}"
        result = lister.conv_bracketedstring_to_kvmu(kvmu)
        self.assertEqual(result, ("key", "value", "", "unit", ""))

        # Test a string with measure, unit, value, and key
        kvmu = "{measure|unit|value|key}"
        result = lister.conv_bracketedstring_to_kvmu(kvmu)
        self.assertEqual(result, ("key", "value", "measure", "unit", ""))

        # Test a string with no separators
        kvmu = "{value}"
        result = lister.conv_bracketedstring_to_kvmu(kvmu)
        expected_log = "WARNING: A Key-Value split with length = 1 is found. This can be caused by a " \
                            "mathematical formula, which is okay and hence no KV pair is written to the metadata. " \
                            "Otherwise please check this pair: {0}."
        self.assertEqual(result, ("", "", "", "", expected_log.format(kvmu)))

        # Test a string with too many separators
        with self.assertRaises(SystemExit):
            kvmu = "{measure|unit|value|key|extra}"
            lister.conv_bracketedstring_to_kvmu(kvmu)


    # def test_parse_lines_to_kv(self):
    #     lines = ["metadata section: Experiment Context"]
    #     result, internal_comments, log = lister.parse_lines_to_kv(lines)
    #
    #     # The expected result is based on the assumption of how the dependent functions work
    #     expected_result = [[0, "metadata section", "Experiment Context", "", ""]]
    #
    #     self.assertEqual(result, expected_result)


# TODO: Continue with lister.process_experiment()
# NOTE: many of the remaining functions are not tested because they are either too complicated for unit test
# or require interactions with GUI components. These functions are tested manually. Try exploring Unit Test Mock:
# https://docs.python.org/3/library/unittest.mock.html

if __name__ == '__main__':
    unittest.main()
