#final code for the scraper after experimenting in jupyter notebook

import os
import getpass
import argparse
from tqdm import tqdm
import time
import json
from piazza_api import Piazza

PIAZZA_USERNAME = ''
PIAZZA_PASSWORD = ''
REQ_DELAY = 0.5 #how much time to wait between each request to Piazza (avoids "too fast" error)

#set up argument parser
parser = argparse.ArgumentParser(
            prog='Piazza Scraper',
            description='Scrapes an entire piazza class for research purposes')

parser.add_argument('-i', '--id', help='Course ID of course to scrape')

def get_creds():
    #get credentials
    global PIAZZA_USERNAME, PIAZZA_PASSWORD
    PIAZZA_USERNAME = input('Enter email for login: ')
    PIAZZA_PASSWORD = getpass.getpass('Enter password for login: ')

def save_data(data):
    for name in data.keys():
        with open(f'output/{name}.json', 'w', encoding='utf-8') as f: #TODO: allow users to select output folder through args
            json.dump(data[name], f, ensure_ascii=False, indent=4)

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
    
    for post in tqdm(course.iter_all_posts()):
        try:
            p_data = {} #post data

            #put main post content
            p_data['subject'] = post['history'][0]['subject']
            p_data['content'] = post['history'][0]['content']

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
        except KeyboardInterrupt:
            break #save data gathered so far in case program is running longer than user wants
        except:
            break
    
    print("Done. Saving data...")
    save_data(posts)
    print("Saved!")

if __name__ == '__main__':
    args = parser.parse_args()

    main(args.id)