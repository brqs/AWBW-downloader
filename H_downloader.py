# -*- coding: utf-8 -*-

import os
import cv2
import time
import shutil
import requests
import numpy as np
import tkinter as tk
from bs4 import BeautifulSoup as bs

savedir_template = '[{}]_{}_{}_vs_{}'
replay_url_template = 'https://awbw.amarriner.com/replay.php?games_id={}&ndx={}'
screen_url_template = 'https://awbw.amarriner.com/replay_screenshot.php?games_id={}&ndx={}'
new_rep_url_template = 'https://awbw.amarriner.com/2030.php?games_id={}&ndx={}'
download_url_template = 'https://awbw.amarriner.com/replay_download.php?games_id={}'
re = 0

def gen_text (strx, w0, h0):
    '''
    '''
    h = 10
    w = 10 * len (strx)
    img = 255 * np.ones ((h0, w0, 3), dtype = np.uint8)
    font = cv2.FONT_HERSHEY_PLAIN
    img1 = cv2.putText (img, strx, ((w0 - w) // 2, (h0 + h) // 2), font, 1, (0, 0, 0), 1)
    return img1
    
def gen_copstar (cop):
    if cop == 1:
        starimg = cv2.imread ('common/redstar.png')
    elif cop == 2:
        starimg = cv2.imread ('common/bluestar.png')
    else:
        return 255 * np.ones ((14, 14, 3), dtype = np.uint8)
    return starimg
    
def gen_logo (country_name):
    starimg = cv2.imread ('common/{}logo.png'.format (country_name))
    return starimg

class AW_Game (object):
    '''
    '''
    
    def __init__ (self, gameid, max_loop_times = 6):
        '''
        '''
        self.gameid = gameid
        self.mapname = None
        self.p1_name = None
        self.p1_country = None
        self.p2_name = None
        self.p2_country = None
        self.turns = None
        self.picsize = None
        self.unsavendx = 0
        self.max_loop_times = max_loop_times
    
    @property
    def savedir (self):
        '''
        '''
        return savedir_template.format (self.gameid, self.mapname, self.p1_name, self.p2_name)
    
    @property
    def ingredients (self):
        '''
        '''
        return '{}/ingredients'.format (self.savedir)
    
    
    def mk_savedir (self):
        '''
        '''
        if not os.path.exists (self.savedir):
            os.mkdir (self.savedir)
            os.mkdir (self.ingredients)
    
    def get_gameinfo (self):
        '''
        '''
        global re
        url = replay_url_template.format (self.gameid, 0)
        re = requests.get (url, verify = False, stream = True)
        sp0 = bs (re.text,'lxml')
        
        sp = sp0.find ('span', {'id' : 'replay-header-text'})
        text = sp.text.split ('Map:') [-1].strip ()
        self.mapname = text
        
        sp = sp0.find ('div', {'id':'replay-player-info'})
        
        sp1, sp2 = sp.find_all ('a')
        self.p1_name = sp1.text
        self.p2_name = sp2.text
        
        self.mk_savedir ()
        
        logo = 1
        co = 1
        for sp1 in sp.find_all ('img'):
            text = sp1 ['src']
            if 'logo.gif' in text:
                text = text.split ('logo.gif') [0] [-2 :]
                if (logo):
                    self.p1_country = text
                    logo = 0
                else:
                    self.p2_country = text
            if '.png' in text:
                re1 = requests.get (text, verify = False)
                text = text.split ('.png') [0]
                text = text.split ('/') [-1]
                if (co):
                    self.p1_co = text
                    with open ('{}/p1_co.png'.format (self.ingredients), 'wb') as f:
                        f.write (re1.content)
                    co = 0
                else:
                    with open ('{}/p2_co.png'.format (self.ingredients), 'wb') as f:
                        f.write (re1.content)
                    self.p2_co = text
                  
        sp = sp0.find ('select', {'id' : 'selectndx'})
        sp = sp.find_all () [-1]
        self.turns = int (sp ['value']) + 1
    
    def get_info_loop (self):
        '''
        '''
        count = 0
        print ('Getting info {}...'.format (self.gameid))
        while not self.turns:
            count += 1
            if count > self.max_loop_times:
                print ('{} - Try too many times!'.format (self.gameid))
                return 0            
            try:
                print ('try: {} - {}'.format (self.gameid, count))
                self.get_gameinfo ()
            except KeyboardInterrupt:
                return 0
            except Exception as e:
                print(repr(e))
        return 1
    
    def load_saved_ndx (self):
        '''
        '''
        saved_max = -1
        headstr = '[{}]_'.format (self.gameid)
        headlen = len (headstr)
        for obj in os.listdir ():
            if obj [: headlen] == headstr:
                for obj1 in os.listdir (obj):
                    if obj1 [: 6] == 'fixed_':
                        png_index = int (obj1 [6 : -4])
                        if png_index > saved_max:
                            saved_max = png_index
        self.unsavendx = saved_max + 1
    
    def get_screenshot_ndx (self, ndx):
        '''
        '''
        global re
        url = screen_url_template.format (self.gameid, ndx)
        re = requests.get (url, verify = False, stream = True)
        with open ('{}/shot_{}.png'.format (self.ingredients, ndx), 'wb') as f:
            f.write (re.content)
    
    def get_awbw_file (self, ndx):
        '''
        '''
        pass
            
    def get_picture (self, ndx, borderwidth = 8, textheight = 16, textwidth = 80):
        '''
        '''
        global re
        self.get_screenshot_ndx (ndx)
        
        result = {}

        url = replay_url_template.format (self.gameid, ndx)
        re = requests.get (url, verify = False, stream = True)
        sp0 = bs (re.text,'lxml')
        
        sp = sp0.find ('div', {'id':'replay-player-info'})
        sps = sp.find_all ('tr')
        sp1 = sps [-2]
        sp2 = sps [-1]
        sps = sp1.find_all ('td')
        result ['p1_in'] = sps [4].text.strip()
        result ['p1_fd'] = sps [5].text.strip()
        result ['p1_un'] = sps [6].text.strip()
        result ['p1_uf'] = sps [7].text.strip()
        text = sps [1]['style']
        if '#0066CC' in text:
            result ['p1_cop'] = 2
        elif '#FF0000' in text:
            result ['p1_cop'] = 1
        else:
            result ['p1_cop'] = 0
        
        sps = sp2.find_all ('td')
        result ['p2_in'] = sps [4].text.strip()
        result ['p2_fd'] = sps [5].text.strip()
        result ['p2_un'] = sps [6].text.strip()
        result ['p2_uf'] = sps [7].text.strip()
        text = sps [1]['style']
        if '#0066CC' in text:
            result ['p2_cop'] = 2
        elif '#FF0000' in text:
            result ['p2_cop'] = 1
        else:
            result ['p2_cop'] = 0
        
        power = 1
        for sp1 in sp.find_all ('img'):
            text = sp1 ['src']
            if 'power_bar' in text:
                text = text.split ('&') [0].split ('pct=') [1]
                if power:
                    result ['p1_pw'] = '{}%'.format(text.strip())
                    power = 0
                else:
                    result ['p2_pw'] = '{}%'.format(text.strip())       
                        
        sp = sp0.find ('select', {'id' : 'selectndx'})
        sp = sp.find_all () [-1]

        img = cv2.imread ('{}/shot_{}.png'.format (self.ingredients, ndx))
        height = img.shape [0] * 2
        width = img.shape [1] * 2
        img = cv2.resize (img, (width, height))
        
        turnimg = cv2.imread ('common/yourturn_arrow.png')
        hturn = turnimg.shape [0]
        wturn = turnimg.shape [1]
        
        logo1 = gen_logo (self.p1_country)
        logo2 = gen_logo (self.p2_country)
        hlogo = logo1.shape [0]
        wlogo = logo1.shape [1]
        
        co1 = cv2.imread ('{}/p1_co.png'.format (self.ingredients))
        co2 = cv2.imread ('{}/p2_co.png'.format (self.ingredients))
        hco = co1.shape [0]
        wco = co1.shape [1]
        
        hinfohead0 = height + 2 * borderwidth
        
        hcohead1 = hinfohead0 + textheight + borderwidth
        hmid1 = hcohead1 + hco // 2
        hturnhead1 = hmid1 - hturn // 2
        hlogohead1 = hmid1 - hlogo // 2
        hinfohead1 = hmid1 - textheight // 2
        
        hcohead2 = hcohead1 + hco + borderwidth
        hmid2 = hcohead2 + hco // 2
        hturnhead2 = hmid2 - hturn // 2
        hlogohead2 = hmid2 - hlogo // 2
        hinfohead2 = hmid2 - textheight // 2
        
        wturnhead = borderwidth
        wlogohead = wturnhead + wturn + borderwidth
        wcohead = wlogohead + wlogo + borderwidth
        wcophead = wcohead + wco + borderwidth
        wpwhead = wcophead + wlogo + borderwidth
        winhead = wpwhead + textwidth + borderwidth
        wfdhead = winhead + textwidth + borderwidth
        wunhead = wfdhead + textwidth + borderwidth
        wufhead = wunhead + textwidth + borderwidth
        
        imgheight = hcohead2 + hco + borderwidth
        
        shotwidth = width + 2 * borderwidth
        subwidth = wufhead + textwidth + borderwidth
        if subwidth < shotwidth:
            imgwidth = shotwidth
            sub_fix = (shotwidth - subwidth) // 2
            shot_fix = 0
        else:
            imgwidth = subwidth
            sub_fix = 0
            shot_fix = (subwidth - shotwidth) // 2
        
        newimg = 255 * np.ones ([imgheight, imgwidth, 3], dtype = np.uint8)
        newimg [borderwidth : borderwidth + height, borderwidth + shot_fix : borderwidth + width + shot_fix, :] = img
        
        newimg [hinfohead0 : hinfohead0 + textheight, wturnhead + sub_fix : wcohead + wco + sub_fix, :] = gen_text ('Day: {}'.format(ndx // 2 + 1), wturn + wlogo + wco + 2 * borderwidth, textheight)
        newimg [hinfohead0 : hinfohead0 + textheight, wpwhead + sub_fix : wpwhead + textwidth + sub_fix, :] = gen_text ('Power', textwidth, textheight)
        newimg [hinfohead0 : hinfohead0 + textheight, winhead + sub_fix : winhead + textwidth + sub_fix, :] = gen_text ('Income', textwidth, textheight)
        newimg [hinfohead0 : hinfohead0 + textheight, wfdhead + sub_fix : wfdhead + textwidth + sub_fix, :] = gen_text ('Funds', textwidth, textheight)
        newimg [hinfohead0 : hinfohead0 + textheight, wunhead + sub_fix : wunhead + textwidth + sub_fix, :] = gen_text ('Units(#)', textwidth, textheight)
        newimg [hinfohead0 : hinfohead0 + textheight, wufhead + sub_fix : wufhead + textwidth + sub_fix, :] = gen_text ('Units($)', textwidth, textheight)
            
        newimg [hlogohead1 : hlogohead1 + hlogo, wlogohead + sub_fix : wlogohead + wlogo + sub_fix, :] = logo1
        newimg [hcohead1 : hcohead1 + hco, wcohead + sub_fix : wcohead + wco + sub_fix, :] = co1
        newimg [hinfohead1 : hinfohead1 + textheight, wpwhead + sub_fix : wpwhead + textwidth + sub_fix, :] = gen_text (result ['p1_pw'], textwidth, textheight)
        newimg [hinfohead1 : hinfohead1 + textheight, winhead + sub_fix : winhead + textwidth + sub_fix, :] = gen_text (result ['p1_in'], textwidth, textheight)
        newimg [hinfohead1 : hinfohead1 + textheight, wfdhead + sub_fix : wfdhead + textwidth + sub_fix, :] = gen_text (result ['p1_fd'], textwidth, textheight)
        newimg [hinfohead1 : hinfohead1 + textheight, wunhead + sub_fix : wunhead + textwidth + sub_fix, :] = gen_text (result ['p1_un'], textwidth, textheight)
        newimg [hinfohead1 : hinfohead1 + textheight, wufhead + sub_fix : wufhead + textwidth + sub_fix, :] = gen_text (result ['p1_uf'], textwidth, textheight)
        if result ['p1_cop']:
            newimg [hlogohead1 : hlogohead1 + hlogo, wcophead + sub_fix : wcophead + wlogo + sub_fix, :] = gen_copstar (result ['p1_cop'])
        
        newimg [hlogohead2 : hlogohead2 + hlogo, wlogohead + sub_fix : wlogohead + wlogo + sub_fix, :] = logo2
        newimg [hcohead2 : hcohead2 + hco, wcohead + sub_fix : wcohead + wco + sub_fix, :] = co2
        newimg [hinfohead2 : hinfohead2 + textheight, wpwhead + sub_fix : wpwhead + textwidth + sub_fix, :] = gen_text (result ['p2_pw'], textwidth, textheight)
        newimg [hinfohead2 : hinfohead2 + textheight, winhead + sub_fix : winhead + textwidth + sub_fix, :] = gen_text (result ['p2_in'], textwidth, textheight)
        newimg [hinfohead2 : hinfohead2 + textheight, wfdhead + sub_fix : wfdhead + textwidth + sub_fix, :] = gen_text (result ['p2_fd'], textwidth, textheight)
        newimg [hinfohead2 : hinfohead2 + textheight, wunhead + sub_fix : wunhead + textwidth + sub_fix, :] = gen_text (result ['p2_un'], textwidth, textheight)
        newimg [hinfohead2 : hinfohead2 + textheight, wufhead + sub_fix : wufhead + textwidth + sub_fix, :] = gen_text (result ['p2_uf'], textwidth, textheight)
        if result ['p2_cop']:
            newimg [hlogohead2 : hlogohead2 + hlogo, wcophead + sub_fix : wcophead + wlogo + sub_fix, :] = gen_copstar (result ['p2_cop'])
        
        if ndx % 2 == 0:
            newimg [hturnhead1 : hturnhead1 + hturn, wturnhead + sub_fix : wturnhead + wturn + sub_fix, :] = turnimg
        else:
            newimg [hturnhead2 : hturnhead2 + hturn, wturnhead + sub_fix : wturnhead + wturn + sub_fix, :] = turnimg
        
        cv2.imwrite ('{}/fixed_{}.png'.format (self.savedir, ndx), newimg)
        self.picsize = (imgwidth, imgheight)
        
    
    def get_screen (self):
        '''
        '''
        self.mk_savedir ()
        for i in range (self.turns):
            print ('Downloading {}...'.format (i))
            self.get_picture (i)
            self.unsavendx = i + 1
            print ('Completed! {}/{}'.format (i + 1, self.turns))
    
    def get_screen_loop (self):
        '''
        '''
        count = 0
        self.mk_savedir ()
        self.load_saved_ndx ()
        while self.unsavendx < self.turns:
            count += 1
            if count > self.max_loop_times:
                print ('{} - Try too many times!'.format (self.gameid))
                return 0
            try:
                print ('try: {} - {}'.format (self.gameid, count))
                for i in range (self.unsavendx, self.turns):
                    print ('Downloading {}-{}...'.format (self.gameid, i))
                    self.get_picture (i)
                    self.unsavendx = i + 1
                    print ('Completed! [{}/{}]\n'.format (i + 1, self.turns))
                    count = 0
            except KeyboardInterrupt:
                return 0
            except Exception as e:
                print(repr(e))
        return 1            
    
    def mk_mp4 (self, fps = 1):
        '''
        '''
        fourcc = cv2.VideoWriter_fourcc('D', 'I', 'V', 'X')
        video = cv2.VideoWriter('{}/{}.MP4'.format(self.savedir, self.savedir), fourcc, fps, self.picsize)
        for fig_order in range (self.turns):
            img = cv2.imread('{}/fixed_{}.png'.format (self.savedir, fig_order))
            video.write(img)
            if fig_order > 11:
                video.write(img)
        video.release ()
        
    def save_as (self, dest_dir):
        '''
        '''
        asdir = os.path.join(dest_dir, self.savedir)
        if not os.path.exists (asdir):
            shutil.copytree (self.savedir, os.path.join(dest_dir, self.savedir))

def batch_save (new_list = [], dest_dir = 'E:/AwOnly/semiwar/', retry_old = True):
    '''
    '''
    requests.packages.urllib3.disable_warnings()
    if retry_old:
        with open ('H_fail_list.log', 'r') as f:
            content = f.read ().strip ()
        old_list = [int (i.strip ()) for i in content.split ('\n')] if content else []
    else:
        old_list = []
    save_list = new_list + old_list
    success_list = []
    fail_list = []
    for gameid in save_list:
        game = AW_Game (gameid)
        if (game.get_info_loop ()):
            if (game.get_screen_loop ()):            
                game.mk_mp4 ()
                game.save_as (dest_dir)
                time_version = time.strftime('%Y%m%d%H%M', time.localtime())
                with open ('H_download_log.log', 'a') as f:                   
                    f.write ('{} successfully download on {}!\n'.format (game.gameid, time_version))
                success_list.append (gameid)                
            else:
                fail_list.append (gameid)
        else:
            fail_list.append (gameid)
    with open ('H_fail_list.log', 'w' if retry_old else 'a') as f:
        f.writelines (['{}\n'.format (i) for i in fail_list])
    print ('success_list')
    print (success_list)
    print ('fail_list')
    print (fail_list)
     
if __name__ == '__main__':
    
    dest_dir = 'E:'
    new_list = [376037, 370930, 376711, 378265]
    batch_save (new_list, dest_dir, False)