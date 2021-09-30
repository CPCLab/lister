from docx import Document
import re
import json


latin_alphabets= "([A-Za-z])"
openers = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
abbr = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
pref = "(Mr|St|Mrs|Ms|Dr)[.]"
sites = "[.](com|net|org|io|gov|de|eu)"
suff = "(Inc|Ltd|Jr|Sr|Co)"
def split_into_sentences(content):
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

def list_to_json(list, filename):
    json.dump(list, open(filename, 'w'))

def get_docx_content(filename):
    f = open(filename, 'rb')
    content = Document(f)
    f.close()
    return content

# parse opened document, first draft of sop
def parse_docx1_content(doc_content):
    par_no = 0
    key_val = []
    for para in doc_content.paragraphs:
        sentences = split_into_sentences(para.text)
        for sentence in sentences:
            key = ""
            key = str(re.findall('\[.*?\]', sentence))              # get keys
            key = ''.join(key[3:-3])                                # remove unnecessary brackets/hyphens
            lst_values = re.findall('\{.*?\}', sentence)            # get lst_values
            lst_values = [value[1:-1] for value in lst_values]      # remove the curly brackets
            str_values = str(lst_values)                            # convert list to string
            str_values = re.sub(r'[\'][\"]*', '', str_values)       # remove superfluous apostrophe and quotation marks
            str_values = str_values[1:-1]
            if key != "" and str_values != "" :                     # only add when none of the key or value is empty
                one_key_val = [par_no, key, str_values]
                key_val.append(one_key_val)
        par_no = par_no + 1                                         # count paragraph index, starting from 1 and iterate
    return key_val

def extract_kv(kv):
    kv = kv[1:-1]
    kv_split = re.split("\|", kv)
    key = kv_split[1]
    key = key.strip()
    val = kv_split[0]
    val = val.strip()
    #key = ""
    #val = ""
    return key, val

# parse opened document, first draft of sop
def parse_docx2_content(doc_content):
    par_no = 0
    key_val = []
    for para in doc_content.paragraphs:
        kvs = re.findall(r'\{.+?\}', para.text)             # get values and keys
        if len(kvs)>0:
            for kv in kvs:
                key, val = extract_kv(kv)
                if key != "" and val != "":
                    one_key_val = [par_no, key, val]
                    key_val.append(one_key_val)
        par_no = par_no + 1                                         # count paragraph index, starting from 1 and iterate
    return key_val

# open docx document
document = get_docx_content('input/sop2.docx')
list_to_json(parse_docx2_content(document),"output/key_val2.json")
print('amount of paragraphs: ' + str(len(document.paragraphs)))