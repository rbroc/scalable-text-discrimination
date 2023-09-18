import ndjson
import json
from pathlib import Path
import re

def clean_stories_data(stories): 
    for col in ["source", "human_completions"]:
        for s in stories: 
            # lowercase the text 
            s[col] = s[col].lower()

            # remove tokens that have brackets [ wp ] [ ip ]
            s[col] = re.sub(r'\[[^\]]+\]', '', s[col])

            # remove the specific string "# # # # # # ( # dropcap )"
            s[col] = re.sub(r'#\s*#\s*#\s*#\s*#\s*#\s*\(\s*#\s*dropcap\s*\)', '', s[col])

            # remove weird newlines
            s[col] = re.sub(r'\n|<newline>', ' ', s[col])

            # replace multiple spaces with a single space
            s[col] = re.sub(r'\s+', ' ', s[col])

            # define punctuation marks
            punctuation_marks = r'.,!?;:'
        
            # adjust spaces around punctuation marks, considering contractions
            for mark in punctuation_marks:
                if mark == "'":
                    continue  # skip apostrophe to handle contractions separately
                s[col] = re.sub(r'\s*(' + re.escape(mark) + r')\s*', r'\1 ', s[col])
            
            # handle spaces around contractions (apostrophes)
            s[col] = re.sub(r'\s*’\s*', r'’', s[col])
            
            # remove extra space before last quotation mark
            s[col] = s[col].strip()

    return stories 

def cleanup():
    ''' Standardizes datasets by lowercasing and removing irregular format '''

    # Cleanup mrsp
    msrpath = Path('..') / 'datasets' / 'mrpc' 
    msrfile = msrpath / 'raw.ndjson'
    with open(msrfile) as f:
        msrp = ndjson.load(f)
    for m in msrp:
        m['human_completions'] = m['human_completions'][0][0].lower()
        m['source'] = m['source'].lower()
        m['id'] = 'mrpc' + m['id'][4:]
    with open(msrpath / 'data.ndjson', 'w') as f:
        ndjson.dump(msrp, f, ensure_ascii=False)
    
    # Cleanup stories
    storiespath = Path('..') / 'datasets' / 'stories' 
    storiesfile = storiespath / 'stories_5bins_1000tokens_al.json'
    with open(storiesfile) as f:
        stories = json.load(f)
   
    # clean data 
    cleaned_stories = clean_stories_data(stories)

    with open(storiespath / 'data.ndjson', 'w') as f:
        ndjson.dump(cleaned_stories, f, ensure_ascii=False)

    # Cleanup dailymail
    dmpath = Path('..') / 'datasets' / 'dailymail_cnn' 
    dmfile = dmpath / 'raw.ndjson'
    with open(dmfile) as f:
        dm = ndjson.load(f)
    for d in dm:
        d['human_completions'] = d['human_completions'].lower()
        d['source'] = d['source'].lower()
    with open(dmpath / 'data.ndjson', 'w') as f:
        ndjson.dump(dm, f, ensure_ascii=False)


    # clean dailydialog (remove EOT tokens)
    dmpath = Path('..') / 'datasets' / 'dailydialog' 
    dmfile = dmpath / 'data.ndjson'

    with open(dmfile) as f:
        dm = ndjson.load(f)

    for col in ["source", "human_completions"]:
        for d in dm:
            # remove EOT token
            d[col] = re.sub(r'\s*\[EOT\]\s*', '', d[col])

            # replace multiple spaces with a single space
            d[col] = re.sub(r'\s+', ' ', d[col])

    with open(dmpath / 'data.ndjson', 'w') as f:
        ndjson.dump(dm, f, ensure_ascii=False)

if __name__ == '__main__':
    cleanup()