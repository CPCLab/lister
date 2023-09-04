import unittest
import lister
from bs4 import BeautifulSoup


class Test_lister(unittest.TestCase):

    # def test_parse_list(self):
    #     lines = ['Examplary SOP: MD Simulations', 'Membrane simulation: yes/no', 'Cycles of minimization: XX',
    #              '<Section|Preparation and Environment>',
    #              'The variants were protonated with {PROPKA| protonation method} according to {7.4| pH}, neutralized by adding counterions.',
    #              '<if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of {POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute. <elif|membrane simulation|e|false>, the variants were solvated in an {octahedral|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.',
    #              'All atom {molecular dynamics (MD)|simulation} simulations were performed using the {AMBER14|suite} suite.',
    #              '<if|water type|e|TIP3P>, The {ff14SB|force field} force field was used. <elif|water type|e|OPC>, The {ff19SB|force field} force field was used.',
    #              '<if|membrane simulation|e|true>, the force field is used in combination with a {LIPID14|force field} force field',
    #              '<if|membrane simulation|e|true> During the {thermalization|period}, the time step for all MD simulations was set to {2 fs|dt} with a direct space, nonbonded cutoff of {9 Å|cut}. During the {production|period}, the time step for all MD simulations was set to {4 fs|dt} as hydrogen mass repartitioning was used with a direct-space, non-bonded cutoff of {8 Å|cut}. <elif|membrane simulation|e|false>, the time step for all MD simulations was set to {4 fs|dt} as hydrogen mass repartitioning was used with a direct-space, non-bonded cutoff of {8 Å|cut}.',
    #              'To cope with long-range interactions, the Particle Mesh Ewald method was used; the SHAKE algorithm was applied to bonds involving hydrogen atoms.',
    #              '<Section|Minimization>',
    #              'At the beginning, {17,500|maxcyc} steps of steepest descent and conjugate gradient minimization were performed. ',
    #              '<for each|cycles of minimization> print {2500|maxcyc}, steps of minimization were performed.',
    #              'During these steps positional harmonic restraints with a force constant of <for each|cycles of minimization> print {25 kcal mol-1 Å-2|restraint_wt} were applied to solute atoms.',
    #              '<Section|Thermalization>',
    #              'Thereafter, {50 ps|simulation time} of {NVT|MD} simulations were conducted.',
    #              'The system was then heated up to {100 K|temp0}.',
    #              'The previous step is followed by {300 ps|simulation time} simulations to adjust the density of the simulation box to a pressure of {1 atm|pres0} and to heat the system to {300 K|temp0}. During these steps, a harmonic potential with a force constant of {10 kcal mol-1 Å-2|restraint_wt} was applied to the solute atoms. ',
    #              'As the final step in thermalization, {300 ps|simulation time} {NVT|MD} MD simulations were performed.',
    #              'During this process, the restraint forces on solute atoms were gradually reduced to {0 kcal mol-1 Å-2|restraint_wt} within the first {100 ps|simulation time}. ',
    #              '<Section|Production>',
    #              'Afterward, {5|overall repetitions} replicas of independent production {NVT|MD} simulations were performed.',
    #              'For each production run, simulations of {2 ns|simulation time} were performed.']
    #     par_key_val = [['-', 'section', 'Preparation and Environment'], [1, 'protonation method', 'PROPKA'],
    #                    [1, 'pH', '7.4'], [2, 'step type', 'conditional'], [2, 'flow type', 'if'],
    #                    [2, 'flow parameter', 'membrane simulation'], [2, 'flow logical parameter', 'e'],
    #                    [2, 'flow compared value', 'true'], [2, 'Lipid type', 'POPC'], [2, 'box type', 'rectangular'],
    #                    [2, 'water type', 'TIP3P'], [2, 'shell radius', '12 Å'], [2, 'step type', 'conditional'],
    #                    [2, 'flow type', 'elif'], [2, 'flow parameter', 'membrane simulation'],
    #                    [2, 'flow logical parameter', 'e'], [2, 'flow compared value', 'false'],
    #                    [2, 'box type', 'octahedral'], [2, 'water type', 'TIP3P'], [2, 'shell radius', '12 Å'],
    #                    [3, 'simulation', 'molecular dynamics'], [3, 'suite', 'AMBER14'],
    #                    [4, 'step type', 'conditional'], [4, 'flow type', 'if'], [4, 'flow parameter', 'water type'],
    #                    [4, 'flow logical parameter', 'e'], [4, 'flow compared value', 'TIP3P'],
    #                    [4, 'force field', 'ff14SB'], [4, 'step type', 'conditional'], [4, 'flow type', 'elif'],
    #                    [4, 'flow parameter', 'water type'], [4, 'flow logical parameter', 'e'],
    #                    [4, 'flow compared value', 'OPC'], [4, 'force field', 'ff19SB'], [4, 'step type', 'conditional'],
    #                    [4, 'flow type', 'if'], [4, 'flow parameter', 'membrane simulation'],
    #                    [4, 'flow logical parameter', 'e'], [4, 'flow compared value', 'true'],
    #                    [4, 'force field', 'LIPID14'], [5, 'step type', 'conditional'], [5, 'flow type', 'if'],
    #                    [5, 'flow parameter', 'membrane simulation'], [5, 'flow logical parameter', 'e'],
    #                    [5, 'flow compared value', 'true'], [5, 'period', 'thermalization'], [5, 'dt', '2 fs'],
    #                    [5, 'cut', '9 Å'], [5, 'period', 'production'], [5, 'dt', '4 fs'], [5, 'cut', '8 Å'],
    #                    [5, 'step type', 'conditional'], [5, 'flow type', 'elif'],
    #                    [5, 'flow parameter', 'membrane simulation'], [5, 'flow logical parameter', 'e'],
    #                    [5, 'flow compared value', 'false'], [5, 'dt', '4 fs'], [5, 'cut', '8 Å'],
    #                    ['-', 'section', 'Minimization'], [7, 'maxcyc', '17,500'], [8, 'step type', 'iteration'],
    #                    [8, 'flow type', 'for each'], [8, 'flow parameter', 'cycles of minimization'],
    #                    [8, 'maxcyc', '2500'], [9, 'step type', 'iteration'], [9, 'flow type', 'for each'],
    #                    [9, 'flow parameter', 'cycles of minimization'], [9, 'restraint_wt', '25 kcal mol-1 Å-2'],
    #                    ['-', 'section', 'Thermalization'], [10, 'simulation time', '50 ps'], [10, 'MD', 'NVT'],
    #                    [11, 'temp0', '100 K'], [12, 'simulation time', '300 ps'], [12, 'pres0', '1 atm'],
    #                    [12, 'temp0', '300 K'], [12, 'restraint_wt', '10 kcal mol-1 Å-2'],
    #                    [13, 'simulation time', '300 ps'], [13, 'MD', 'NVT'], [14, 'restraint_wt', '0 kcal mol-1 Å-2'],
    #                    [14, 'simulation time', '100 ps'], ['-', 'section', 'Production'],
    #                    [15, 'overall repetitions', '5'], [15, 'MD', 'NVT'], [16, 'simulation time', '2 ns']]
    #     self.assertListEqual(lister.parse_list(lines), par_key_val)

    def test_split_into_sentences(self):
        content = ' <if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of {POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute. <elif|membrane simulation|e|false>, the variants were solvated in an {octahedral|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.'
        sentences = [
            '<if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of {POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.',
            '<elif|membrane simulation|e|false>, the variants were solvated in an {octahedral|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.']
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
        line = '<if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of {POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute. <elif|membrane simulation|e|false>, the variants were solvated in an {octahedral|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.'
        line2 = 'if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of {POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute. <elif|membrane simulation|e|false>, the variants were solvated in an {octahedral|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.'
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
        processed_list = [[8, 'step type', 'iteration'], [8, 'flow type', 'for each'], [8, 'flow parameter', 'cycles of minimization']]
        self.assertListEqual(lister.process_foreach(par_no, list1)[0], processed_list)

    def test_process_while(self):
        pass # needs more use case

    def test_process_if(self):
        list1 = ['if', 'membrane simulation', 'e', 'true']
        par_no = 2
        processed_list = [[2, 'step type', 'conditional'], [2, 'flow type', 'if'], [2, 'flow parameter', 'membrane simulation'], [2, 'flow logical parameter', 'e'], [2, 'flow compared value', 'true']]
        self.assertListEqual(lister.process_if(par_no, list1)[0], processed_list)

    def test_process_elseif(self):
        list1 = ['elif', 'membrane simulation', 'e', 'false']
        par_no = 2
        processed_list = [[2, 'step type', 'conditional'], [2, 'flow type', 'elif'], [2, 'flow parameter', 'membrane simulation'], [2, 'flow logical parameter', 'e'], [2, 'flow compared value', 'false']]
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

    def test_conv_bracketedstring_to_kvmu(self):
        str1 = '{8 Å|cut}'
        key = 'cut'
        val = '8 Å'
        self.assertEqual(lister.conv_bracketedstring_to_kvmu(str1)[0], key)
        self.assertEqual(lister.conv_bracketedstring_to_kvmu(str1)[1], val)

 #   def test_parse_list(self):
 #       lines = ['Examplary SOP: MD Simulations', 'Membrane simulation: yes/no', 'Cycles of minimization: XX', '<Section|Preparation and Environment>', 'The variants were protonated with {PROPKA| protonation method} according to {7.4| pH}, neutralized by adding counterions.', '<if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of {POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute. <elif|membrane simulation|e|false>, the variants were solvated in an {octahedral|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.', 'All atom {molecular dynamics (MD)|simulation} simulations were performed using the {AMBER14|suite} suite.', '<if|water type|e|TIP3P>, The {ff14SB|force field} force field was used. <elif|water type|e|OPC>, The {ff19SB|force field} force field was used.', '<if|membrane simulation|e|true>, the force field is used in combination with a {LIPID14|force field} force field', '<if|membrane simulation|e|true> During the {thermalization|period}, the time step for all MD simulations was set to {2 fs|dt} with a direct space, nonbonded cutoff of {9 Å|cut}. During the {production|period}, the time step for all MD simulations was set to {4 fs|dt} as hydrogen mass repartitioning was used with a direct-space, non-bonded cutoff of {8 Å|cut}. <elif|membrane simulation|e|false>, the time step for all MD simulations was set to {4 fs|dt} as hydrogen mass repartitioning was used with a direct-space, non-bonded cutoff of {8 Å|cut}.', 'To cope with long-range interactions, the Particle Mesh Ewald method was used; the SHAKE algorithm was applied to bonds involving hydrogen atoms.', '<Section|Minimization>', 'At the beginning, {17,500|maxcyc} steps of steepest descent and conjugate gradient minimization were performed. ', '<for each|cycles of minimization> print {2500|maxcyc}, steps of minimization were performed.', 'During these steps positional harmonic restraints with a force constant of <for each|cycles of minimization> print {25 kcal mol-1 Å-2|restraint_wt} were applied to solute atoms.', '<Section|Thermalization>', 'Thereafter, {50 ps|simulation time} of {NVT|MD} simulations were conducted.', 'The system was then heated up to {100 K|temp0}.', 'The previous step is followed by {300 ps|simulation time} simulations to adjust the density of the simulation box to a pressure of {1 atm|pres0} and to heat the system to {300 K|temp0}. During these steps, a harmonic potential with a force constant of {10 kcal mol-1 Å-2|restraint_wt} was applied to the solute atoms. ', 'As the final step in thermalization, {300 ps|simulation time} {NVT|MD} MD simulations were performed.', 'During this process, the restraint forces on solute atoms were gradually reduced to {0 kcal mol-1 Å-2|restraint_wt} within the first {100 ps|simulation time}. ', '<Section|Production>', 'Afterward, {5|overall repetitions} replicas of independent production {NVT|MD} simulations were performed.', 'For each production run, simulations of {2 ns|simulation time} were performed.']
 #       processed_lines = [['-', 'section', 'Preparation and Environment'], [1, 'protonation method', 'PROPKA'], [1, 'pH', '7.4'], [2, 'step type', 'conditional'], [2, 'flow type', 'if'], [2, 'flow parameter', 'membrane simulation'], [2, 'flow logical parameter', 'e'], [2, 'flow compared value', 'true'], [2, 'Lipid type', 'POPC'], [2, 'box type', 'rectangular'], [2, 'water type', 'TIP3P'], [2, 'shell radius', '12 Å'], [2, 'step type', 'conditional'], [2, 'flow type', 'elif'], [2, 'flow parameter', 'membrane simulation'], [2, 'flow logical parameter', 'e'], [2, 'flow compared value', 'false'], [2, 'box type', 'octahedral'], [2, 'water type', 'TIP3P'], [2, 'shell radius', '12 Å'], [3, 'simulation', 'molecular dynamics'], [3, 'suite', 'AMBER14'], [4, 'step type', 'conditional'], [4, 'flow type', 'if'], [4, 'flow parameter', 'water type'], [4, 'flow logical parameter', 'e'], [4, 'flow compared value', 'TIP3P'], [4, 'force field', 'ff14SB'], [4, 'step type', 'conditional'], [4, 'flow type', 'elif'], [4, 'flow parameter', 'water type'], [4, 'flow logical parameter', 'e'], [4, 'flow compared value', 'OPC'], [4, 'force field', 'ff19SB'], [4, 'step type', 'conditional'], [4, 'flow type', 'if'], [4, 'flow parameter', 'membrane simulation'], [4, 'flow logical parameter', 'e'], [4, 'flow compared value', 'true'], [4, 'force field', 'LIPID14'], [5, 'step type', 'conditional'], [5, 'flow type', 'if'], [5, 'flow parameter', 'membrane simulation'], [5, 'flow logical parameter', 'e'], [5, 'flow compared value', 'true'], [5, 'period', 'thermalization'], [5, 'dt', '2 fs'], [5, 'cut', '9 Å'], [5, 'period', 'production'], [5, 'dt', '4 fs'], [5, 'cut', '8 Å'], [5, 'step type', 'conditional'], [5, 'flow type', 'elif'], [5, 'flow parameter', 'membrane simulation'], [5, 'flow logical parameter', 'e'], [5, 'flow compared value', 'false'], [5, 'dt', '4 fs'], [5, 'cut', '8 Å'], ['-', 'section', 'Minimization'], [7, 'maxcyc', '17,500'], [8, 'step type', 'iteration'], [8, 'flow type', 'for each'], [8, 'flow parameter', 'cycles of minimization'], [8, 'maxcyc', '2500'], [9, 'step type', 'iteration'], [9, 'flow type', 'for each'], [9, 'flow parameter', 'cycles of minimization'], [9, 'restraint_wt', '25 kcal mol-1 Å-2'], ['-', 'section', 'Thermalization'], [10, 'simulation time', '50 ps'], [10, 'MD', 'NVT'], [11, 'temp0', '100 K'], [12, 'simulation time', '300 ps'], [12, 'pres0', '1 atm'], [12, 'temp0', '300 K'], [12, 'restraint_wt', '10 kcal mol-1 Å-2'], [13, 'simulation time', '300 ps'], [13, 'MD', 'NVT'], [14, 'restraint_wt', '0 kcal mol-1 Å-2'], [14, 'simulation time', '100 ps'], ['-', 'section', 'Production'], [15, 'overall repetitions', '5'], [15, 'MD', 'NVT'], [16, 'simulation time', '2 ns']]
 #       self.assertListEqual(lister.parse_list(lines)[0], processed_lines)

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
        # SECTION TEST HERE COULD USE REGEX INSTEAD OF MANUALLY INPUTTING THE SECTION LEVEL AS DONE HERE
        sect_str0 = '<Section|Preparation and Environment>'
        processed_sect0_list = [['-', 'section level 0', 'Preparation and Environment', '', '']]
        self.assertListEqual(lister.extract_flow_type(par_no, sect_str0)[0], processed_sect0_list)

        sect_str1 = '<Subsection|Preparation and Environment>'
        processed_sect0_list = [['-', 'section level 1', 'Preparation and Environment', '', '']]
        self.assertListEqual(lister.extract_flow_type(par_no, sect_str1)[0], processed_sect0_list)

        sect_str2 = '<Subsubsection|Preparation and Environment>'
        processed_sect0_list = [['-', 'section level 2', 'Preparation and Environment', '', '']]
        self.assertListEqual(lister.extract_flow_type(par_no, sect_str2)[0], processed_sect0_list)

        sect_str3 = '<Subsubsubsection|Preparation and Environment>'
        processed_sect0_list = [['-', 'section level 3', 'Preparation and Environment', '', '']]
        self.assertListEqual(lister.extract_flow_type(par_no, sect_str3)[0], processed_sect0_list)

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

        # Check that content outside of the table tag ("Hello") is still present
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

    # def test_conv_bracketedstring_to_kvmu(self):
    #     # Test a string with key and value
    #     kvmu = "{value|key}"
    #     result = lister.conv_bracketedstring_to_kvmu(kvmu)
    #     self.assertEqual(result, ("key", "value", "", "", ""))
    #
    #     # Test a string with value, unit, and key
    #     kvmu = "{value|unit|key}"
    #     result = lister.conv_bracketedstring_to_kvmu(kvmu)
    #     self.assertEqual(result, ("key", "value", "", "unit", ""))
    #
    #     # Test a string with measure, unit, value, and key
    #     kvmu = "{measure|unit|value|key}"
    #     result = lister.conv_bracketedstring_to_kvmu(kvmu)
    #     self.assertEqual(result, ("key", "value", "measure", "unit", ""))
    #
    #     # Test a string with no separators
    #     kvmu = "{value}"
    #     result = lister.conv_bracketedstring_to_kvmu(kvmu)
    #     expected_log = "SINGLE-PAIRED BRACKET: only contains 'value'"
    #     self.assertEqual(result, ("", "", "", "", expected_log))
    #
    #     # Test a string with too many separators
    #     with self.assertRaises(SystemExit):
    #         kvmu = "{measure|unit|value|key|extra}"
    #         lister.conv_bracketedstring_to_kvmu(kvmu)


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
