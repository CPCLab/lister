from docx import Document
import re
import json
from collections import defaultdict



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


def list_to_json(list):
    json.dump(list, open("output/key_val.json", 'w'))


# parse opened document
def parse_docx_content(doc_content):
    par_no = 0
    key_val = []
    for para in document.paragraphs:
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
        par_no = par_no + 1  # count paragraph index, starting from 1 and iterate
    return key_val


# open docx document
f = open('input/sop.docx', 'rb')
document = Document(f)
f.close()
list_to_json(parse_docx_content(document))
print('amount of paragraphs: ' + str(len(document.paragraphs)))

