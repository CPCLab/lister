# DOCX Standard Operating Procedure (SOP) Parser for SFB1208 Experiments

This repository contains a set of files to parse SOP from lab experiments.



# Motivation

As research lab usually has their own set of SOP to conduct experiments, a tool to extract metadata from an editable document (e.g., DOCX) would be handy. The metadata is helpful in documenting the research and hence improves the reproducibility of the conducted research. To enable the metadata extraction, the SOP should follow some annotation rules (described later below).



# Repository structure

- The base directory contains the metadata extraction script.

- *input* directory contains the docx SOPs example for extraction.

- *output* directory contains extracted steps order – key – value in both JSON and XLSX format.

  

# List of supported annotations

The parser extracts: 

| Extracted Items          | Description                                                  | Representation                                               | Example                                     | Extracted order,key,value                                    |
| ------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------- | ------------------------------------------------------------ |
| Section                  | The section name                                             | <*section*\|*section name*>                                  | <*section*\|*Structure Preparation*>        | <ul><li> "-", *section*, *Structure Preparation*</li></ul>   |
| Order                    | The *order* of the steps, based on the order of the paragraph in the docx SOP document | -                                                            | -                                           | -                                                            |
| Key                      | The *key* for the metadata, based on the value represented in the curly bracket after the pipe character {value\|key}. | {value\|*key*}                                               | {sequence alignment\|*stage*}               | <ul><li> \<order\>, *stage*, sequence alignment</li></ul>    |
| Comment                  | *Comments* are allowed within the key, represented within regular brackets after the pipe symbol. **TBD**: How to serialize comments in the metadata parser output. | {value\|(*comment*) key}                                     | {receptor residue\|(*minimization*) target} | <ul><li> \<order\> target, receptor residue</li></ul>        |
| Value                    | The *value* of the metadata is based on the first value represented in the curly bracket before the pipe character {value\|key}. Example:  with ‘sequence alignment’ as the value. | {*value*\|key}                                               | {*sequence alignment*\|stage}               | <ul><li> \<order\>, stage, *sequence alignment*</li></ul>    |
| Control flow: *for each* | Extract multiple key value pairs related to *for each*  iterations | <*flow type*\|iterated value>                                | <*for each*\|*generated pose*>              | <ul><li>\<order\>, step type, *iteration*</li><li>\<order\>, flow type, *for each*</li><li>\<order\>, flow parameter, generated pose</li></ul> |
| Control flow: *while*    | Extract multiple key value pairs related to *while*  iteration | \<flow type\|key\|logical operator\|value\> ... \<iteration operation\|magnitude\> | \<while\|pH\|lte\|7\> ... \<\+\|1\>         | <ul> <li>\<order\>, step type, *iteration*</li> <li>\<order\>, flow type, *while*</li> <li>\<order\>, flow parameter, pH</li> <li>\<order\>, flow logical parameter, lte</li> <li>\<order\>, flow compared value, 7</li> <li>\<order\>, flow operation, +, </li> <li>\<order\>, flow magnitude, 1</li> </ul> |
| Control flow: *if*       | Extract multiple key value pairs related to *if*  iteration  | \<if\|key\|logical operator\|value\>                         | \<if\|pH\|lte\|7\>                          | <ul> <li>\<order\>, step type, *conditional*</li> <li>\<order\>, flow type, *if*</li> <li>\<order\>, flow parameter, pH</li> <li>\<order\>, flow logical parameter, lte</li> <li>\<order\>, flow compared value, 7</li> </ul> |
| Control flow: *else if*  | Extract multiple key value pairs related to *else if*  iteration | \<else if\|key\|logical operator\|value\>                    | \<else if\|pH\|between\|[8-12]\>            | <ul> <li>\<order\>, step type, *conditional*</li> <li>\<order\>, flow type, *else if*</li> <li>\<order\>, flow parameter, pH</li> <li>\<order\>, flow logical parameter, between</li> <li>\<order\>, flow range, [8-12]</li><li>\<order\>,start iteration value,8</li><li>\<order\>,end iteration value,12</li> </ul> |
| Control flow: *else*     | Extract multiple key value pairs related to *else*  iteration | \<else\>                                                     |                                             | <ul> <li>\<order\>, step type, *conditional*</li> <li>\<order\>, flow type, *else*</li> </ul> |
| Control flow: *for*      | Extract multiple key value pairs related to *for*  iteration | \<for\|key\|[range]\|iteration operation\|magnitude\>        | \<for\|pH\|\[1-7]\|\+\|1\>                  | <ul> <li>\<order\>, step type, *iteration*</li> <li>\<order\>, flow type, *for*</li> <li>\<order\>, flow parameter, pH</li> <li>\<order\>, flow logical parameter, lte</li> <li>\<order\>, flow flow range, [1-7]</li> <li>\<order\>,start iteration value,1</li><li>\<order\>,end iteration value,7</li> <li>\<order\>, flow operation, +, </li> <li>\<order\>, flow magnitude, 1</li> </ul> |
|                          |                                                              |                                                              |                                             |                                                              |

The overall example of the SOP document is available in the *input/sop2.docx* file. The color in the *sop2.docx* does not play any role in the order/key/value extraction.

 

# Supported operators



## Logical operator

Logical operator is used to decide whether a particular condition  is met during iteration/conditional block. It is available for `while`, `if` and `else if` control flow. The following logical operators are supported: 

- `e` : equal

- `ne`: not equal

- `lt`: less than

- `lte`: less than equal

- `gt`: greater than

- `gte`: greater than equal

- `between`: between

  

## Iteration operator

Iteration operator is used to change the value of compared variable during a loop.  It is available for `while` and `for`. The following iteration operators are supported:

- `+`: iteration using addition

- `-`: iteration using subtraction

- `%`: iteration using modulo

- `*`: iteration using multiplication

- `/`: iteration using division

  

# Constraints and recommendations

## Constraint

- Only one unique key per step is supported. If there are similar keys within one step, only the last pair of that key will be saved and the previous ones will be overridden (**TODO**: create a warning in the validator if a non-empty KV already existed).
- Subprocess/substep is not currently supported to simplify data storage process (or let me know if this is really necessary, providing suggestion on how to store/serialize it would be great). Any subprocess will be stored simply as a next step from its parent process.
- Some of the keys are not officially on the Amber's output parameter list (e.g., No. of atom in the used PDB molecules), but please feel free to suggest a new key. These suggested keys will be analyzed for further inclusion in metadata standard in the specific domain. 
- Avoid use of reference without explicit KV-pair (avoid e.g., "*Repeat step 1 with similar parameters*"), as this will make the metadata for that particular implicit step unextracted.
- Comments are currently not yet extracted in the parser's output but it is already parsed in the background - still need to find a way how to simplify the data serialization.

## Recommendations

- To minimize confusion regarding units of measurement (e.g., `fs` vs `ps`), please explicitly state the units as a comment within the value portion of the KV-pair, e.g., ` {0.01 (ps)|gamma_ln}`.
- Default  measurement unit should be used (e.g., `ps` instead of `fs` in e.g., AmberMD's `gamma_ln` variable). 
-  Avoid superfluous blank lines (**TODO**: Discard step numbering on an empty line/section - or implement specific step numbering functionality).

# Running the parser

1.   Create SOP according to the above annotation rules.
2.  Change the input directory/file name in the python script (2nd last line).
3. Change the output directory/filename (last line).
4.  Run the script.

 

# Further plans

1. Fixes for while control flow, and logical operators in general control flow.
2. Consult CAi and Biochemistry1 for its implementability on other labs.
3. Align the used keys with terms from an ontology, or if the term does not exist, create a new term by extending an ontology or creating a term within a new ontology.

 