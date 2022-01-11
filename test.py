import unittest
import lister

class Test_lister(unittest.TestCase):

    def test_parse_list(self):
        lines = ['Examplary SOP: MD Simulations', 'Membrane simulation: yes/no', 'Cycles of minimization: XX', '<Section|Preparation and Environment>', 'The variants were protonated with {PROPKA| protonation method} according to {7.4| pH}, neutralized by adding counterions.', '<if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of {POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute. <elif|membrane simulation|e|false>, the variants were solvated in an {octahedral|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.', 'All atom {molecular dynamics (MD)|simulation} simulations were performed using the {AMBER14|suite} suite.', '<if|water type|e|TIP3P>, The {ff14SB|force field} force field was used. <elif|water type|e|OPC>, The {ff19SB|force field} force field was used.', '<if|membrane simulation|e|true>, the force field is used in combination with a {LIPID14|force field} force field', '<if|membrane simulation|e|true> During the {thermalization|period}, the time step for all MD simulations was set to {2 fs|dt} with a direct space, nonbonded cutoff of {9 Å|cut}. During the {production|period}, the time step for all MD simulations was set to {4 fs|dt} as hydrogen mass repartitioning was used with a direct-space, non-bonded cutoff of {8 Å|cut}. <elif|membrane simulation|e|false>, the time step for all MD simulations was set to {4 fs|dt} as hydrogen mass repartitioning was used with a direct-space, non-bonded cutoff of {8 Å|cut}.', 'To cope with long-range interactions, the Particle Mesh Ewald method was used; the SHAKE algorithm was applied to bonds involving hydrogen atoms.', '<Section|Minimization>', 'At the beginning, {17,500|maxcyc} steps of steepest descent and conjugate gradient minimization were performed. ', '<for each|cycles of minimization> print {2500|maxcyc}, steps of minimization were performed.', 'During these steps positional harmonic restraints with a force constant of <for each|cycles of minimization> print {25 kcal mol-1 Å-2|restraint_wt} were applied to solute atoms.', '<Section|Thermalization>', 'Thereafter, {50 ps|simulation time} of {NVT|MD} simulations were conducted.', 'The system was then heated up to {100 K|temp0}.', 'The previous step is followed by {300 ps|simulation time} simulations to adjust the density of the simulation box to a pressure of {1 atm|pres0} and to heat the system to {300 K|temp0}. During these steps, a harmonic potential with a force constant of {10 kcal mol-1 Å-2|restraint_wt} was applied to the solute atoms. ', 'As the final step in thermalization, {300 ps|simulation time} {NVT|MD} MD simulations were performed.', 'During this process, the restraint forces on solute atoms were gradually reduced to {0 kcal mol-1 Å-2|restraint_wt} within the first {100 ps|simulation time}. ', '<Section|Production>', 'Afterward, {5|overall repetitions} replicas of independent production {NVT|MD} simulations were performed.', 'For each production run, simulations of {2 ns|simulation time} were performed.']
        par_key_val = [['-', 'section', 'Preparation and Environment'], [1, 'protonation method', 'PROPKA'], [1, 'pH', '7.4'], [2, 'step type', 'conditional'], [2, 'flow type', 'if'], [2, 'flow parameter', 'membrane simulation'], [2, 'flow logical parameter', 'e'], [2, 'flow compared value', 'true'], [2, 'Lipid type', 'POPC'], [2, 'box type', 'rectangular'], [2, 'water type', 'TIP3P'], [2, 'shell radius', '12 Å'], [2, 'step type', 'conditional'], [2, 'flow type', 'elif'], [2, 'flow parameter', 'membrane simulation'], [2, 'flow logical parameter', 'e'], [2, 'flow compared value', 'false'], [2, 'box type', 'octahedral'], [2, 'water type', 'TIP3P'], [2, 'shell radius', '12 Å'], [3, 'simulation', 'molecular dynamics'], [3, 'suite', 'AMBER14'], [4, 'step type', 'conditional'], [4, 'flow type', 'if'], [4, 'flow parameter', 'water type'], [4, 'flow logical parameter', 'e'], [4, 'flow compared value', 'TIP3P'], [4, 'force field', 'ff14SB'], [4, 'step type', 'conditional'], [4, 'flow type', 'elif'], [4, 'flow parameter', 'water type'], [4, 'flow logical parameter', 'e'], [4, 'flow compared value', 'OPC'], [4, 'force field', 'ff19SB'], [4, 'step type', 'conditional'], [4, 'flow type', 'if'], [4, 'flow parameter', 'membrane simulation'], [4, 'flow logical parameter', 'e'], [4, 'flow compared value', 'true'], [4, 'force field', 'LIPID14'], [5, 'step type', 'conditional'], [5, 'flow type', 'if'], [5, 'flow parameter', 'membrane simulation'], [5, 'flow logical parameter', 'e'], [5, 'flow compared value', 'true'], [5, 'period', 'thermalization'], [5, 'dt', '2 fs'], [5, 'cut', '9 Å'], [5, 'period', 'production'], [5, 'dt', '4 fs'], [5, 'cut', '8 Å'], [5, 'step type', 'conditional'], [5, 'flow type', 'elif'], [5, 'flow parameter', 'membrane simulation'], [5, 'flow logical parameter', 'e'], [5, 'flow compared value', 'false'], [5, 'dt', '4 fs'], [5, 'cut', '8 Å'], ['-', 'section', 'Minimization'], [7, 'maxcyc', '17,500'], [8, 'step type', 'iteration'], [8, 'flow type', 'for each'], [8, 'flow parameter', 'cycles of minimization'], [8, 'maxcyc', '2500'], [9, 'step type', 'iteration'], [9, 'flow type', 'for each'], [9, 'flow parameter', 'cycles of minimization'], [9, 'restraint_wt', '25 kcal mol-1 Å-2'], ['-', 'section', 'Thermalization'], [10, 'simulation time', '50 ps'], [10, 'MD', 'NVT'], [11, 'temp0', '100 K'], [12, 'simulation time', '300 ps'], [12, 'pres0', '1 atm'], [12, 'temp0', '300 K'], [12, 'restraint_wt', '10 kcal mol-1 Å-2'], [13, 'simulation time', '300 ps'], [13, 'MD', 'NVT'], [14, 'restraint_wt', '0 kcal mol-1 Å-2'], [14, 'simulation time', '100 ps'], ['-', 'section', 'Production'], [15, 'overall repetitions', '5'], [15, 'MD', 'NVT'], [16, 'simulation time', '2 ns']]
        self.assertListEqual(lister.parse_list(lines), par_key_val)

    def test_split_into_sentences(self):
        content = ' <if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of {POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute. <elif|membrane simulation|e|false>, the variants were solvated in an {octahedral|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.'
        sentences = ['<if|membrane simulation|e|true>, The variants were embedded in a membrane consisting of {POPC|Lipid type} lipids and solvated in a {rectangular|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.', '<elif|membrane simulation|e|false>, the variants were solvated in an {octahedral|box type} water box using {TIP3P|water type} with a minimal shell of {12 Å|shell radius} around the solute.']
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
        self.assertFalse(lister.validate_while(list1)[0])
        self.assertTrue(lister.validate_while(list2)[0])

    def test_validate_if(self):
        list1 = ['if', 'membrane simulation', 'e', 'True']
        list2 = ['if', 'membrane simulation', 'True']
        self.assertFalse(lister.validate_if(list1)[0])
        self.assertTrue(lister.validate_if(list2)[0])

    def test_validate_elseif(self):
        list1 = ['elif', 'membrane simulation', 'e', 'false']
        list2 = ['elif', 'membrane simulation', '=', 'false']
        list3 = ['elif', 'membrane simulation', 'false']
        self.assertFalse(lister.validate_elseif(list1)[0])
        self.assertTrue(lister.validate_elseif(list2)[0])
        self.assertTrue(lister.validate_elseif(list3)[0])

    def test_validate_else(self):
        list1 = ['else']
        list2 = ['else', "1"]
        self.assertFalse(lister.validate_else(list1)[0])
        self.assertTrue(lister.validate_else(list2)[0])

    def test_validate_range(self):
        pass # waiting for a use case

    def test_validate_for(self):
        list1 = ['for', 'pH', '[1-7]', '+', '1']
        list2 = ['for', 'pH', '[1-7]', '1']
        self.assertFalse(lister.validate_for(list1)[0])
        self.assertTrue(lister.validate_for(list2)[0])

    def test_validate_iterate(self):
        pass # need more use case

    def test_validate_section(self):
        list1 = ['Section', 'Preparation and Environment']
        list2 = ['Section']
        self.assertFalse(lister.validate_section(list1)[0])
        self.assertTrue(lister.validate_section(list2)[0])

    def test_process_foreach(self):
        pass

    def test_process_while(self):
        pass

    def test_process_if(self):
        pass

    def test_process_elseif(self):
        pass

    def test_process_else(self):
        pass

    def test_process_range(self):
        pass

    def test_process_for(self):
        pass

    def test_process_iterate(self):
        pass

    def test_process_comment(self):
        pass

    def test_process_section(self):
        pass

    def test_extract_kv(self):
        pass

    def test_extract_flow_type(self):
        pass

    def test_get_docx_par_list(self):
        pass

    def test_parse_list(self):
        pass

    def test_extract_docx_content(self):
        pass

    def test_get_docx_content(self):
        pass

    def test_get_elab_exp_lines(self):
        pass

    def test_extract_elab_exp_content(self):
        pass

if __name__ == '__main__':
    unittest.main()
