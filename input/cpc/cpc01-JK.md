**Examplary SOP: MD Simulations**

Membrane simulation: yes/no

Cycles of minimization: XX

\<Section\|Preparation and Environment\>

The variants were protonated with {PROPKA\| protonation method}
according to {7.4\| pH}, neutralized by adding counterions.

\<if\|membrane simulation\|e\|true\>, The variants were embedded in a
membrane consisting of {POPC\|Lipid type} lipids and solvated in a
{rectangular\|box type} water box using {TIP3P\|water type} with a
minimal shell of {12 Å\|shell radius} around the solute.
\<elif\|membrane simulation\|e\|false\>, the variants were solvated in
an {octahedral\|box type} water box using {TIP3P\|water type} with a
minimal shell of {12 Å\|shell radius} around the solute.

All atom {molecular dynamics (MD)\|simulation} were performed using the
{AMBER14\|suite} suite.

\<if\|water type\|e\|TIP3P\>, The {ff14SB\|force field} was used.
\<elif\|water type\|e\|OPC\>, The {ff19SB\|force field} was used.

\<if\|membrane simulation\|e\|true\>, the force field is used in
combination with a {LIPID14\|force field}.

\<if\|membrane simulation\|e\|true\> During the
{thermalization\|period}, the time step for all MD simulations was set
to {2 fs\|dt} with a direct space, nonbonded cutoff of {9 Å\|cut}.
During the {production\|period}, the time step for all MD simulations
was set to {4 fs\|dt} as hydrogen mass repartitioning was used with a
direct-space, non-bonded cutoff of {8 Å\|cut}. \<elif\|membrane
simulation\|e\|false\>, the time step for all MD simulations was set to
{4 fs\|dt} as hydrogen mass repartitioning was used with a direct-space,
non-bonded cutoff of {8 Å\|cut}.

To cope with long-range interactions, the Particle Mesh Ewald method was
used; the SHAKE algorithm was applied to bonds involving hydrogen atoms.

\<Section\|Minimization\>

At the beginning, {17,500\|maxcyc} steps of steepest descent and
conjugate gradient minimization were performed.

\<for each\|cycles of minimization\> print {2500\|maxcyc}, steps of
minimization were performed.

During these steps positional harmonic restraints with a force constant
of \<for each\|cycles of minimization\> print {25 kcal mol-1
Å^-2^\|restraint_wt} were applied to solute atoms.

\<Section\|Thermalization\>

Thereafter, {50 ps\|simulation time} of {NVT\|MD} simulations were
conducted.

The system was then heated up to {100 K\|temp0}.

The previous step is followed by {300 ps\|simulation time} simulations
to adjust the density of the simulation box to a pressure of {1
atm\|pres0} and to heat the system to {300 K\|temp0}. During these
steps, a harmonic potential with a force constant of {10 kcal mol^-1^
Å^-2^\|restraint_wt} was applied to the solute atoms.

As the final step in thermalization, {300 ps\|simulation time} {NVT\|MD}
simulations were performed.

During this process, the restraint forces on solute atoms were gradually
reduced to {0 kcal mol^-1^ Å^-2^\|restraint_wt} within the first {100
ps\|simulation time}.

\<Section\|Production\>

Afterward, {5\|overall repetitions} replicas of independent production
{NVT\|MD} simulations were performed.

For each production run, simulations of {2 ns\|simulation time} were
performed.
