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

PIAZZA_USERNAME = ''
PIAZZA_PASSWORD = ''
REQ_DELAY = 0.3 #how much time to wait between each request to Piazza (avoids "too fast" error)

count = 0 #for printing later on

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

def scrape(posts, generator):
    global count

    for post in generator:
        print(f'Scraping post {count}...', end='\r')
        sys.stdout.flush()
        count += 1

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
        except Exception as e:
            print(e)
            break

def main(cid=''):
    global count

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

    generator = course.iter_all_posts()
    count = 0 #global variable that will be updated in the scrape function
    while True:
        try:
            scrape(posts=posts, generator=generator)
            break
        except:
            time.sleep(REQ_DELAY*5) #wait extra long if Piazza starts yelling at us for spamming them

    print()
    print("Done. Saving data...")
    save_data(posts, cid)
    print("Saved!")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("No class ID given!")