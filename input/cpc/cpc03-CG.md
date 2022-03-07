Procedure :

**<Section|Preparation and Environment>**

The structure { PDB-ID: 5xm9| structure} was downloaded from the PDB. The chains A-D, G, and H were deleted and the DNA substrate was changed to RNA.

The complex was embedded in a {cubic|box type} water box using {TIP3P|water type} with a minimal shell of {15 Å|shell radius} around the solute. {150 mM NaCl| ions} and {20 mM hexahydrated Mg2+| ions} were added.

All atom {molecular dynamics (MD)|simulation} simulations were performed using the {AMBER14|suite} suite.

The {OL3| force field} force field was used for the RNA and the {OL15| force field} force field was used for the DNA.

The monovalent ions were treated with the {Joung-Chetham parameters for monovalent ions| parameters} and the Mg2+ ions were treated with the {Li-Merz parameters for two-fold positively charged metal ions| parameters}.

The time step for all MD simulations was set to {2 (fs)|dt} with a direct space, nonbonded cutoff of {9 Å|cut}. During the {production|period}, the time step for all MD simulations was set to {4 (fs)|dt} as hydrogen mass repartitioning was used with a direct-space, non-bonded cutoff of {8 (Å)|cut}. <elif|membrane simulation|e|false>, the time step for all MD simulations was set to {4 (fs)|dt} as hydrogen mass repartitioning was used with a direct-space, non-bonded cutoff of {8 (Å)|cut}.

To cope with long-range interactions, the Particle Mesh Ewald method was used; the SHAKE algorithm was applied to bonds involving hydrogen atoms.

**<Section|Minimization>**

At the beginning, {17,500|maxcyc} steps of steepest descent and conjugate gradient minimization were performed for each of the 10 replicas.

print {2500|maxcyc}, steps of minimization were performed.

During these steps positional harmonic restraints with a force constant of print {25 kcal mol-1 Å-2|restraint_wt} were applied to solute atoms.

**<Section|Thermalization>**

Thereafter, {50 (ps)|simulation time} of {NVT|MD} simulations were conducted.

The system was then heated up to {100 K|temp0} varying a fraction of a Kelvin for each replica.

The previous step is followed by {300 (ps)|simulation time} simulations to adjust the density of the simulation box to a pressure of {1 (atm)|pres0} and to heat the system to {300 (K)|temp0}. During these steps, a harmonic potential with a force constant of {10 (kcal mol-1 Å-2)|restraint_wt} was applied to the solute atoms.

As the final step in thermalization, {300 (ns)|simulation time} {NVT|MD} MD simulations were performed.

During this process, the restraint forces on solute atoms were gradually reduced to {0 kcal mol-1 Å-2|restraint_wt} within the first {250 (ns)|simulation time}.

**<Section|Production>**

Afterward, {10|overall repetitions} replicas of independent production {NVT|MD} simulations were performed.

For each production run, simulations of {1 µs|simulation time} were performed.