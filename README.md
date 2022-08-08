# 

# LISTER: **Li**fe **S**cience Experimen**t** M**e**tadata Parse**r**

This repository contains a set of files to parse SOP from lab experiments.

# 1. Motivation

As a research group usually has its own set of SOP to conduct experiments, a tool to extract metadata from SOP-adapted experiment document can be helpful in supporting  FAIR research data publication. The research data published in FAIR principle can improve research reproducibility. To enable metadata extraction, the experiment should follow some annotation rules (described below) and in a format supported by LISTER (a eLabFTW entry, a Microsoft Word document or a Markdown file).

# 2. Running LISTER

LISTER is packaged into an executable file under Windows, Linux and Mac OS (with Intel chip). The executable file for each platform is available in the release page, along with a  file. 

- **For Windows and Linux**: place the executable file within the same folder as `config.json` file. 

- **For macOS**, place both config file and `lister.app` in your `~/Apps/lister`  directory (please create the directory first). The `config.json` for macOS have to be placed exactly in `~/Apps/lister/config.json` due to a limitation on macOS. 

## Adapting the config.json file

### For eLabFTW

Parsing an eLabFTW entry requires:

- General parameter:
  
  - eLabFTW `API token` and `API endpoint`, which can be obtained from the eLabFTW instance's administrator from your lab or university.
  
  - Default `output` directory , a directory path used to store the output of the parser.

- Experiment-specific parameter:
  
  - Metadata/experiment output filename.
  
  - Experiment ID of the parsed entry.

### For Microsoft Word or Markdown (TODO: Revise)

- Input file name - the filename of the docx or markdown file to parse.

- Base output directory - the output directory for the above files.

- Output file name - the output filename prefix, which will be used for the docx, json, xlsx, and log output.

# 3. Annotation Mechanism

The annotation mechanism below affects both output metadata (xlsx and json) and These are the basics of annotating an experiment/protocol to be parsed by LISTER:

- *Key-Value (KV) elements*.
  
  -  A KV pair is written as *{value|key}* in an experiment entry.
  
  - If applicable, a KV pair is extendable with *measure* and *unit*. Therefore, there are two more variations for writing a KV pair: 
    
    - *{measure|unit|key}* 
    
    - *{measure|unit|value|key}* 

-  *Adjusting Key visibility on DOCX output*. 
  
  - Keys are hidden by default in the docx output file to avoid superflous text.
  
  - To make the keys visible, keys can be placed within colons `{value|:key:}`

- *Order.* 
  
  - There can be similar keys within an experiment entry, hence a disambigation is needed.
  
  - The disambiguation is done through the *paragraph number*, which will be extracted for each KV pair.

- *Comments*. There are three different types of comments supported in LISTER.
  
  - Comments parsed as-is.
    
    - This retains both brackets and content in the word document.
    
    - Annotation is done using a regular bracket `()`.
    
    - Annotation example: `(This comment will be parsed as is, retaining both the content and the bracket itself in the docx file)`.
  
  - Invisible comments. 
    
    - Used when MM writers need to specify additional notes (regarding, for example, parameter usage) but wish to hide that note from the final experiment document output.
    
    - Annotation is done using a pair of underscore inside a regular comment. `(_ _)`
    
    - Annotation example: `(_This comment will be totally invisible in the docx output file_)`.
  
  - Comments without brackets retained, with the content kept. 
    
    - This is used for typically comment within key-value pairs.
    
    - Annotation is done using brackets and double colon `(: :)`
    
    - Annotation example: `(:This comment will be totally invisible in the docx output file:)`.

- *Conditionals and iterations handling*. 
  
  - LISTER supports documenting conditionals and iterations, but it should be used with caution. This is because the final experiment entry  is unlikely to have these conditional and iterations clauses as researchers are encouraged to get rid of conditionals and adapt the experiment parameter values with the actual values that was used during the experiment. 

- *Reference management*. 
  
  - Reference can be provided if the referred source have a DOI.
  
  - Annotation is done using regular brackets, and providing the DOI number (not URI) in the bracket.
  
  - Example: `(DOI_CODE)` 
  
  - The DOI code will be converted into square bracket number, referring to the reference index that will be provided in the bottom of the document, e.g., `[2]`, in which the number `2` is the index referred in the document.

- *Sections*. 
  
  - The keyword sub\*section is designated to provide separation between sections or subsection. 
  
  - This is done by using `<section|section name>` annotation.
  
  - Multiple subsection is also supported, e.g., `<subsubsection|section name>` which will outputs different sectioning level in the metadata, and different heading level in the microsoft word document.

# 4. Some annotations vs extracted metadata example (TODO: incomplete - no DOI/subsection/visibility/measure-unit yet)

The parser extracts: 

| Extracted Items          | Description                                                                                                                                                                                                                                 | Representation                                                                                 | Example                                        | Extracted order,key,value in the metadata                                                                                                                                                                                                                                                                                                                                                     |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Section                  | The section name                                                                                                                                                                                                                            | <*section*\|*section name*>                                                                    | <*section*\|*Structure Preparation*>           | <ul><li> "-", *section*, *Structure Preparation*</li></ul>                                                                                                                                                                                                                                                                                                                                    |
| Order                    | The *order* of the steps, based on the order of the paragraph in the docx SOP document                                                                                                                                                      | -                                                                                              | -                                              | -                                                                                                                                                                                                                                                                                                                                                                                             |
| Key                      | The *key* for the metadata, based on the value represented in the curly bracket after the pipe character {value\|key}.                                                                                                                      | {value\|*key*}                                                                                 | {sequence alignment\|*stage*}                  | <ul><li> \<order\>, *stage*, sequence alignment</li></ul>                                                                                                                                                                                                                                                                                                                                     |
| Comment                  | *Comments* are allowed within the key, represented within regular brackets after the pipe symbol. Comment can be placed both/either before and/or after key and/or value. **TBD**: How to serialize comments in the metadata parser output. | - {value\|(*comment*) key} or {value (*comment*)\|key} or {value (*comment*)\|(*comment*) key} | {receptor residue\|(*minimization*) target}    | <ul><li> \<order\> target, receptor residue</li></ul>                                                                                                                                                                                                                                                                                                                                         |
| Value                    | The *value* of the metadata is based on the first value represented in the curly bracket before the pipe character {value\|key}. Example:  with ‘sequence alignment’ as the value.                                                          | {*value*\|key}                                                                                 | {*sequence alignment*\|stage}                  | <ul><li> \<order\>, stage, *sequence alignment*</li></ul>                                                                                                                                                                                                                                                                                                                                     |
| Control flow: `for each` | Extract multiple key value pairs related to `for each`  iterations                                                                                                                                                                          | <`for each`\|iterated value>                                                                   | <`for each`\|*generated pose*>                 | <ul><li>\<order\>, step type, *iteration*</li><li>\<order\>, flow type, *for each*</li><li>\<order\>, flow parameter, generated pose</li></ul>                                                                                                                                                                                                                                                |
| Control flow:  `while`   | Extract multiple key value pairs related to `while`  iteration                                                                                                                                                                              | \<`while`\|key\|logical operator\|value\> ... \<iteration operation\|magnitude\>               | \<`while`\|pH\|lte\|7\> ... \<iterate\|\+\|1\> | <ul> <li>\<order\>, step type, *iteration*</li> <li>\<order\>, flow type, *while*</li> <li>\<order\>, flow parameter, pH</li> <li>\<order\>, flow logical parameter, lte</li> <li>\<order\>, flow compared value, 7</li> <li>\<order\></li> <li>flow type, iterate  (after while)</li> <li>flow operation, +, </li> <li>\<order\>, flow magnitude, 1</li> </ul>                               |
| Control flow: `if`       | Extract multiple key value pairs related to `if`  iteration                                                                                                                                                                                 | \<´if´\|key\|logical operator\|value\>                                                         | \<`if`\|pH\|lte\|7\>                           | <ul> <li>\<order\>, step type, *conditional*</li> <li>\<order\>, flow type, *if*</li> <li>\<order\>, flow parameter, pH</li> <li>\<order\>, flow logical parameter, lte</li> <li>\<order\>, flow compared value, 7</li> </ul>                                                                                                                                                                 |
| Control flow: `else if`  | Extract multiple key value pairs related to `else if`   iteration                                                                                                                                                                           | \<`else if`\|key\|logical operator\|value\>                                                    | \<`else if`\|pH\|between\|[8-12]\>             | <ul> <li>\<order\>, step type, *conditional*</li> <li>\<order\>, flow type, *else if*</li> <li>\<order\>, flow parameter, pH</li> <li>\<order\>, flow logical parameter, between</li> <li>\<order\>, flow range, [8-12]</li><li>\<order\>,start iteration value,8</li><li>\<order\>,end iteration value,12</li> </ul>                                                                         |
| Control flow: `else`     | Extract multiple key value pairs related to `else`  iteration                                                                                                                                                                               | \<`else`\>                                                                                     |                                                | <ul> <li>\<order\>, step type, *conditional*</li> <li>\<order\>, flow type, *else*</li> </ul>                                                                                                                                                                                                                                                                                                 |
| Control flow: `for`      | Extract multiple key value pairs related to `for`  iteration                                                                                                                                                                                | <`for`\|key\|[range]\|iteration operation\|magnitude\>                                         | \<`for`\|pH\|\[1-7]\|\+\|1\>                   | <ul> <li>\<order\>, step type, *iteration*</li> <li>\<order\>, flow type, *for*</li> <li>\<order\>, flow parameter, pH</li> <li>\<order\>, flow logical parameter, lte</li> <li>\<order\>, flow flow range, [1-7]</li> <li>\<order\>,start iteration value,1</li><li>\<order\>,end iteration value,7</li> <li>\<order\>, flow operation, +, </li> <li>\<order\>, flow magnitude, 1</li> </ul> |
|                          |                                                                                                                                                                                                                                             |                                                                                                |                                                |                                                                                                                                                                                                                                                                                                                                                                                               |

The overall example of the SOP document is available in the /*input* directory.  

Note: subsection, comment visibility, and DOI are not yet in the example.

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

# 5. Document validation

LISTER checks the following problems upon parsing, and report accordingly:

- Orphaned brackets and indicates which line the error is located.
- Mismatched data types for conditionals and iterations.
- Mismatched argument numbers for conditionals and iterations. 
- Invalid control flows.

# 6. Image extraction

Images are extracted from the experiment documents, but as for now there is no metadata or naming scheme from the extracted images.

# 7. Recommendations

- Avoid the use of reference without explicit KV-pair (avoid e.g., "*Repeat step 1 with similar parameters*"), as this will make the metadata for that particular implicit step unextracted.
- To minimize confusion regarding units of measurement (e.g., `fs` vs `ps`), please explicitly state the units  within the value portion of the KV-pair, e.g., ` {0.01| ps|gamma_ln}`.

# 8. Repository structure

- The base directory contains the metadata extraction script.
- `input` directory contains the *.DOCX/*.MD experiment documentation examples for the extraction.
- `output` directory contains extracted steps order – key – value in both JSON and XLSX format.
  
  
# 9. Miscellanous

## Associated conditionals

Writing conditionals can be exhausting when there are many else clauses involved. To simplify the writing of conditionals, the authors can choose to write it in a concise manner as an associated conditionals using the /{number} notations after the key-value pairs, and a comment notated by regular bracket after the intended value.  Here is an example:

### Example

_"The top five templates identified by TopDomain were {3N25_A (a), 4YJ5_A (b), 3GR4_A (c), 1A49_A (d), 6DU6_B (e)|template_pdbs}**/1** with sequence identities of {99% (a), 93% (b), 93% (c), 100% (d), 63% (e)|template_identities}**/1**, coverages of {95% (a), 97% (b), 97% (c), 97% (d), 96%(e)|template_coverages}**/1**, and predicted TM-Score of {0.96 (a), 0.96 (b), 0.96 (c), 0.96 (d), 0.93(e)| template_confidences}**/1**, respectively."_

### Explanation

From the SOP above, associated key-values are marked with the number after the "/" symbol, so keys with a similar number after the "'/" are grouped together. In the example above, _template_pdbs, template_identities, template_coverages,_ and _template_confidences_ belong to the same association. The values on each key are then associated according to the comment in the regular bracket. So, if template_pdbs = 3N25_A, then template_identities = 99%, template_coverages = 95%, and template_confidences = 0.96. On a table, the correlation is grouped as shown below.

<style>
</style>

|                      |        |        |        |        |        |
| -------------------- | ------ | ------ | ------ | ------ | ------ |
| association<br> set  | 1      | 1      | 1      | 1      | 1      |
| mapping              | a      | b      | c      | d      | e      |
| template_pdbs        | 4YJ5_A | 3N25_A | 3GR4_A | 1A49_A | 6DU6_B |
| template_identities  | 0.99   | 0.93   | 0.93   | 1      | 0.63   |
| template_coverages   | 0.95   | 0.97   | 0.97   | 0.97   | 0.96   |
| template_confidences | 0.96   | 0.96   | 0.96   | 0.96   | 0.93   |

*Note: the SOP users need to adapt this themselves by removing irrelevant values and /{number} annotations when adapting for their experiment. SOP is not going to be parsed, only the experiments will.*



# Repository structure

- The base directory contains the metadata extraction script.
- `input` directory contains the *.DOCX/*.MD experiment documentation examples for the extraction.
- `output` directory contains extracted steps order – key – value in both JSON and XLSX format.
