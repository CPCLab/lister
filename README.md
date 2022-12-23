# LISTER: Life Science Experiment Metadata Parser

This repository contains a set of files to parse documentation of experiments in eLabFTW.

## Motivation

As a research group usually has its own set of experiment protocols/Materials and Methods (MM) to conduct experiments, a tool to extract metadata from protocols/MMs-adapted experiment documentation helps support research data publication according to FAIR (Findable, Accessible, Interoperable, and Reusable) principles. Research data published under FAIR principles is expected to improve the reproducibility of research. To enable metadata extraction, the experiment documentation follows annotation rules described below and is in an HTML format stored as an experiment/database entry in eLabFTW.


## Screenshots

### User interface
![lister_experiment_tab.png](docs%2Flister_experiment_tab.png)

Fig. 1: User interface for parsing an experiments.


![lister_container_tab.png](docs%2Flister_container_tab.png)

Fig. 2: User interface for parsing a container (e.g., Publications, Project, etc).


### eLabFTW annotations

![elabftw_exp_annotation.png](docs%2Felabftw_exp_annotation.png)

Fig. 3: How the annotation is done to enable parsing via LISTER. This annotated fragment can be derived from reusable, 
and lab-curated experiment protocols/material and methods. See the Annotation Mechanism section below.

![elabftw_exp_linked_items.png](docs%2Felabftw_exp_linked_items.png)

Fig. 4: Linked items section of an experiment, in which the tabular content will be parsed to gather more context
w.r.t. e.g., Study, Project, and System.

### Outputs
![lister_xlsx_output.png](docs%2Flister_xlsx_output.png)

Fig. 5: Metadata output in the Excel sheet, after parsing with LISTER.

![lister_docx_output.png](docs%2Flister_docx_output.png)

Fig. 6: Clean human-friendly output in Word document format, after parsing with LISTER.


## Installing and running LISTER

LISTER is distributed as an executable file for Windows, Linux, or macOS (with an Intel chipset). The executable file for each platform is available on the release page, along with another, platform-specific file.

- **For Windows and Linux**, place the executable file (`lister.exe `on Windows or `lister` on Linux) within the same folder as the config.json file.

- **For macOS**, create the directory `~/Apps/lister` first and place the executable lister.app and config.json in this directory.

### Adapting the config.json file

Parsing an eLabFTW entry requires

- the general parameters
  
  - eLabFTW API token and API endpoint, which can be obtained from the eLabFTW instance's administrator of the lab or university,
  
  - Default output directory, i.e., a directory path used to store the parser output,
    -experiment-specific parameters
    
    - Metadata/experiment output filename,
  
  - Experiment ID for the entry to be parsed.



## Annotation mechanism

The annotation mechanism allows extracting metadata from experiment documentation as .xlsx and .json files. In the following points, the basic elements of annotating protocol/MM to be parsed by LISTER are described.

- *Key-Value (KV) elements*.
  
  - A KV pair is written as `{value|key}` in an experiment entry.
  
  - If applicable, a KV pair is extendable with measure and unit. Therefore, there are two more variations for writing a KV pair:
    
    - `{measure|unit|key} `the measure and unit will be mapped into value and unit.
    - `{measure|unit|value|key}` the measure and unit will be taken as given.
  
  - For example, “*Two* *{100|mL|LB Kan|expression media}* *cultures in* *{unbaffled Erlenmeyer|flasks}*” consists of two patterns of pair:
    
    - `{measure|unit|value|key}` -> `{100|mL|LB Kan|expression media}`
    - `{value|key}` -> `{unbaffled Erlenmeyer|:flasks:}`
  
  - Keys are hidden by default in the .docx output file to avoid superfluous text.
  
  - To make the keys visible, they can be placed within colons as `{value|:key:}`, such as `{unbaffled Erlenmeyer|:flasks:}`”.

- *Order.*
  
  - As there can be identical keys within an experiment entry, disambiguation is needed.
  - The disambiguation is done through the *paragraph number*, which will be extracted and associated with each KV pair.

- *Comments*. There are three types of comments supported in LISTER.
  
  - Comments parsed as-is.
    - This retains both brackets and content in the word document.
    - Annotation is done using a regular bracket `()`.
    - Annotation example: `(This comment will be parsed as is, retaining both the content and the brackets in the .docx file.)`.
  - Invisible comments.
    - Used to specify additional notes (regarding, e.g., parameter use) that should be hidden from the final experiment documentation output.
    - Annotation is done using a pair of underscores inside a regular comment. `(_ _)`
    - Annotation example: `(\_This comment will be invisible in the .docx output file.\_)`.
  - Comments are retained but without brackets.
    - This is typically used for comments within KV pairs.
    - Annotation is done using brackets and a double colon `(: :)`
    - Annotation example: `(:This comment's bracket will be invisible in the .docx output file, but the text content will be kept.:)`.

- *Conditionals and iterations handling*.
  
  - LISTER supports documenting conditionals and iterations, but this should be used cautiously: As the final experiment documentation is unlikely to have these conditional and iteration clauses, researchers are required to resolve them by adapting the experiment parameter values with the actual values used during the experiment.

- *Reference management*.
  
  - References can be provided if the referred source has a DOI.
  - Annotation is done using regular brackets and providing the DOI (not URI) in the bracket.
  - The DOI will be converted into Arabic numerals in square brackets, which refer to the reference provided at the bottom of the document.
  - References are only retained in the docx output, but not the metadata outputs (.xlsx/.json).
  - Example: `(DOI_CODE)`, such as `(10.1073/pnas.062492699)` will be written as `[1]` in the experiment body, and as a numbered list of DOI codes by the end of the experiment documentation.

- *Sections*.
  
  - The keywords section or subsection are designated to provide a separation between sections or subsections.
  - This is done by using the `<section|section name>` annotation.
  - Multiple subsections are also supported, with e.g., `<subsubsection|section name>`, which will output different sectioning levels in the .xlsx and .json files and different heading levels in the .docx file.

## Examples of annotations vs. extracted metadata

| **Extracted item**                                                             | **Description**                                                                                                                                                           | **Representation**                                                                     | **Example**                                 | **Extracted order,key, value, and optionally measure, unit in the metadata**                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Section                                                                        | The section name                                                                                                                                                          | `<section\|section name>`                                                              | `<section\|Structure Preparation>`          | `"-",section level 0,Structure Preparation, -, -`                                                                                                                                                                                                                                                                                                        |
| Order                                                                          | The *order* of the steps, based on the order of the paragraph in the experiment documentation                                                                             | -                                                                                      | -                                           | -                                                                                                                                                                                                                                                                                                                                                        |
| Key                                                                            | The *key* for the metadata, connected to the value {value\                                                                                                                | `{value\|key}`                                                                         | `{sequence alignment\|stage}`               |     `<order>, stage, sequence alignment, -, -`                                                                                                                                                                                                                                                                                                          |
| Comment, please also see the bullet points about comments above for variations | *Comments* are allowed within the key-value annotation, represented within regular brackets. Comments can be placed both/either before and/or after the key and/or value. | `{value\|(comment) key} or {value (comment)\|key} or {value (comment)\|(comment) key}` | `{receptor residue\|(minimization) target}` | `    <order>, target, receptor residue, -, -`                                                                                                                                                                                                                                                                                                           |
| Value                                                                          | The *value* of the metadata is the first item within the curly brackets {*value*\                                                                                         | `{value\|key}`                                                                         | `{sequence alignment\|stage}`               | <order>, `stage, sequence alignment, -, -`                                                                                                                                                                                                                                                                                                               |
| Measure and Unit                                                               | The measure and unit of corresponding key/value pairs.                                                                                                                    | `{measure\|unit\|value\|key}`                                                          | `{100\|mL\|LB Kan\|expression media}`       | `<order>, expression media, LB Kan, 100, mL`                                                                                                                                                                                                                                                                                                             |
| Value and Unit                                                                 | In some cases, value is attached to a unit directly, without having to provide a measure.                                                                                 | `{value\|unit\|key}`                                                                   | `{250\|rpm\|shaking}`                       | `<order>, shaking,250, -, rpm`                                                                                                                                                                                                                                                                                                                           |
| Control flow: `for each`                                                       | Extract multiple key-value pairs related to `for each` iteration                                                                                                          | `{value\|unit\|key}`                                                                   | `<for each\|generated pose>`                | `<order>, flow type,for each, -,- `       `<order>, flow parameter, generated pose, -,-`                                                                                                                                                                                                                                                                 |
| Control flow: `for`                                                            | Extract multiple key-value pairs related to `for` iteration                                                                                                               | `<for\|key\|[range]\|iteration operation\|magnitude>`                                  | `<for\|pH\|[1-7]\|+\|1>`                    | - `<order>, step type,*iteration, -, - `     `<order>, flow type,for, -, -`               `<order>, flow parameter, pH, -, -`        ` <order>, flow range, [1-7], -, -`    `<order>, start iteration value,1, -, -`            `<order>, end iteration value,7, -,-` .      `<order>, flow operation, +,-, -  `      `<order>, flow magnitude, 1, -, -` |
| Control flow: `while`                                                          | Extract multiple key-value pairs related to `while` iteration                                                                                                             | `<while\|key\|logical operator\|value> ... <iterate\|iteration operation\|magnitude>`  | `<while\|pH\|lte\|7> ... <iterate\|+\|1>`   | `<order>, step type,iteration, -, -`          `<order>, flow type,while, -, - `                `<order>, flow parameter, pH, -, -`               `<order>, flow logical parameter, lte, -, -`           <order>, flow compared value, 7*, -, -<order>, flow type,*iterate*(after while) <order>flow operation, +,*-, -*<order>, flow magnitude, 1, -, -  |
| Control flow: `if`                                                             | Extract multiple key-value pairs related to `if` iteration                                                                                                                | `<if\|key\|logical operator\|value>`                                                   | `<if\|pH\|lte\|7>`                          | `<order>, step type,conditional, -,-`          `<order>, flow type,*if, -, -*`                 `<order>, flow parameter, pH. `         `<order>, flow logical parameter, lte, -, -  `       `<order>, flow compared value, 7`                                                                                                                            |
| Control flow: `else if`                                                        | Extract multiple key-value pairs related to `else if` iteration                                                                                                           | `<else if\|key\|logical operator\|value>`                                              | `<else if\|pH\|between\|[8-12]>`            | `<order>, step type,conditional, -, -`         `<order>, flow type,*else if, -, -`    ` <order>, flow parameter, pH, -, -`              `<order>, flow logical parameter, between, -, -`        `<order>, flow range, [8-12], -, -`       `<order>, start iteration value,8, -, -`     `<order>, end iteration value,12, -, -`                           |
| Control flow: `else`                                                           | Extract multiple key-value pairs related to `else` iteration                                                                                                              | `<else>`                                                                               |                                             | `<order>, step type,conditional, -, -`    `<order>, flow type,else, -, -`                                                                                                                                                                                                                                                                                |

### Supported operators

#### Logical operator

A logical operator is used to decide whether a particular condition is met in an iteration/conditional block. It is available for while, if , and else if control flows. The following logical operators are supported:

- `e`: equal

- `ne`: not equal

- `lt`: less than

- `lte`: less than equal

- `gt`: greater than

- `gte`: greater than equal

- `between`: between

#### Iteration operator

An iteration operator is used to change the value of a variable in a loop. It is available for while and for. The following iteration operators are supported:

- +: iteration using addition

- -: iteration using subtraction

- %: iteration using modulo

- *: iteration using multiplication

- /: iteration using division

## Document validation

LISTER checks and reports the following syntax issues upon parsing:

- Orphaned brackets.

- Mismatched data types for conditionals and iterations.

- Mismatched argument numbers for conditionals and iterations.

- Invalid control flows.

## Image extraction

Images are extracted from the experiment documentation, but there is no metadata or naming scheme for the extracted images.

## Recommendations

- Avoid referring to, e.g., a section without explicitly using a key-value pair (avoid, e.g., "*Repeat step 1 with similar parameters*"), as this will make the metadata extraction for that particular implicit step impossible.

- To minimize confusion regarding units of measurement (e.g., `fs` vs `ps`), please explicitly state the units within the value portion of the key-value pair, e.g., `{0.01|ps|gamma_ln}`.

## GitHub repository structure

- The base directory contains the metadata extraction script.

- The output directory contains the extracted metadata: step order – key – value – measure – unit in JSON and XLSX format.

## Miscellaneous

### Packaging LISTER

- Packaging is done through the PyInstaller library and has to be done on the respective platform. PyInstaller should be installed first.

- A .spec file to build LISTER can be generated using the pyi-makespec command, e.g., `pyi-makespec --onedir lister.py` to create a spec file to package the LISTER app as one directory instead of one file.

- The spec file for each platform is provided in the root folder of the LISTER GitHub repository.

- The resulting packaged app will be available under the dist directory, which is created automatically during the build process.

#### Packaging the app on Windows

- One directory version - on the root folder of the repo, run pyinstaller `.\build-windows-onedir.spec`

- One file version - on the root folder of the repo, run pyinstaller `.\build-windows-onefile.spec`

#### Packaging the app on Linux

- One file version - on the root folder of the repo, run pyinstaller `.\build-linux.spec`

#### Packaging the app on macOS

- One file version - on the root folder of the repo, run pyinstaller `.\build-macos.spec`

## Troubleshooting

### Slow app execution

Decompressing a single-executable lister app into a temporary directory likely caused this problem. The multi-file distribution (aka one-directory version) can be used instead, although it is not as tidy as compared to the single-executable LISTER app.

### Encoding problem on Windows

When the following error 'charmap' codec can't encode characters in position... appears, open cmd.exe as an administrator before running LISTER and type the following:

`setx /m PYTHONUTF8 1`

`setx PATHEXT "%PATHEXT%;.PY"`

### Failed building on Windows

The error `win32ctypes.pywin32.pywintypes.error: (110, 'EndUpdateResourceW', 'The system cannot open the device or file specified.'` happens because of file access problems on Windows. Ensure that  the directory is neither read-only nor auto-synced to cloud storage , exclude the repo folder from antivirus scanning, and/or try removing both the `build` and `dist` directories. Both of these directories are automatically generated upon packaging. Cloud storage synchronization may also be the cause of this issue.
