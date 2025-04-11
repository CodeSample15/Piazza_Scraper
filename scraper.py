#Final code for the scraper after experimenting in jupyter notebook
#Script usage --> python scraper.py course_id
#               Example: python scraper.py m470f2rs65zff

import os
import getpass
import time
import json
import sys
import shutil
from piazza_api import Piazza
from tqdm import tqdm

PIAZZA_USERNAME = ''
PIAZZA_PASSWORD = ''
REQ_DELAY = 0.4 #how much time to wait between each request to Piazza (avoids "too fast" error)

def get_creds():
    #get credentials
    global PIAZZA_USERNAME, PIAZZA_PASSWORD
    PIAZZA_USERNAME = input('Enter email for login: ')
    PIAZZA_PASSWORD = getpass.getpass('Enter password for login: ')

def save_data(data, course_id):
    #handle folder
    if not os.path.isdir('output'):
        os.mkdir('output')
    if os.path.isdir(f'output/{course_id}'):
        shutil.rmtree(f'output/{course_id}')
    os.mkdir(f'output/{course_id}')

    for name in data.keys():
        with open(f'output/{course_id}/{name}.json', 'w', encoding='utf-8') as f: #TODO: allow users to select output folder through args
            json.dump(data[name], f, ensure_ascii=False, indent=4)

def convert_uid_to_name(course, data):
    """
    Converts the raw uids scraped from the Piazza posts to real names

    This logic is put into a separate function to allow for an easy way to disable this feature should
    we decide to make the collected data more anonymous (only display users' uids rather than their names).
    """

    #fetch names for uids
    uids = []
    for folder in data:
        uids.extend([n['author'] for n in data[folder]])
    uids = list(filter(lambda x: x!='anon', set(uids))) #remove duplicates and anon entries
    names = course.get_users(uids) #Piazza api call

    #build uid-name dict
    name_dict = {}
    for name, uid in zip(names, uids):
        name_dict[uid] = name['name']

    #loop through data and convert names
    for folder in data:
        for n in data[folder]:
            n['author'] = name_dict.get(n['author'], 'anon')
    

def scrape(posts, post):
    try:
        p_data = {} #post data

        #author scraping
        uid = 'anon'
        if post['history'][0]['anon'] == 'no':
            uid = post['history'][0]['uid']

        #put main post content
        p_data['subject'] = post['history'][0]['subject']
        p_data['content'] = post['history'][0]['content']
        p_data['author'] = uid

        #add replies and follow up discussion
        replies = []
        for child in post['children']:
            if 'history' in child.keys():
                replies.append(child['history'][0]['content'])
            else:
                replies.append(child['subject'])
        p_data['replies'] = replies
        
        #sort data into dictionary using post's folder array
        for folder in post['folders']:
            if folder not in posts.keys():
                posts[folder] = []
            
            posts[folder].append(p_data)

        time.sleep(REQ_DELAY) #avoid spamming the Piazza server
    except Exception as e:
        print(e)

def main(cid=''):
    if cid == '':
        print('No course id specified. Exiting...')
        return

    p = Piazza()

    #attempt to get everything connected and logged in
    try:
        p.user_login(email=os.getenv(PIAZZA_USERNAME), password=os.getenv(PIAZZA_PASSWORD))
    except:
        print("Login failed!")
        return
    try:
        course = p.network(cid)
    except:
        print("Invalid course id given!")
        return

    '''
        posts { 
            'folder1': [
                {
                    'subject' : 'post subject',
                    'content' : 'post content',
                    'replies' : ['reply 1', 'reply 2', 'reply 3',]
                },
                {
                    ...
                },
            ],
        }
    '''

    posts = {}
    feed = course.get_feed(limit=999999, offset=0)
    cids = [post['id'] for post in feed["feed"]]

    print("Scraping...")
    for c in tqdm(cids):
        while True:
            try:
                scrape(posts=posts, post=course.get_post(c))
                break
            except KeyboardInterrupt:
                break
            except:
                time.sleep(REQ_DELAY*12)
                course = p.network(cid) #refresh network
                time.sleep(REQ_DELAY*12) # wait extra long before trying again

    #convert uids in collected data to real names
    convert_uid_to_name(course, posts)

    print("Done. Saving data...")
    save_data(posts, cid)
    print("Saved!")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("No class ID given!")