#!/usr/bin/env python

import sys
import os
from xml.etree import ElementTree as ET
import time
import datetime
import csv
from collections import defaultdict
import hashlib
import math

def date2str(date):
    return time.strftime('%A %d %B', time.strptime(date, '%Y-%m-%d'))

def hrefname(string):
    return string.lower().replace('&','').replace(' ','_')


def get_xml_events(xmlfile):
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    events = []

    for x in list(root):
        if x.tag == 'conference':
            pass
        elif x.tag == 'day':
            events += get_day_events(x)

    return events

def get_day_events(elem):
    if len(elem) == 0:
        return []

    day = date2str(elem.attrib['date'])
    dayofweek = day.split(' ')[0]
    dayofweek = "%s."%dayofweek[0:3] # Sat. or Sun.

    events = []
    for x in elem:
        if x.tag == 'room':
            roomevents = get_room_events(x)
            for ev in roomevents:
                ev['day'] = day
                ev['shortday'] = get_shortday(day)
                ev['dayofweek'] = dayofweek
            events += roomevents

    return events

def get_shortday(day):
    if day.startswith('Saturday'):
        return 'sat'
    if day.startswith('Sunday'):
        return 'sun'
    return 'xxx'

def get_room_events(elem):
    if len(elem) == 0:
        return []

    events = []
    for x in elem:
        events.append(get_event(x))

    return events

def get_event(elem):
    if len(elem) == 0:
        return []

    tracktype = elem.find('type').text.strip()
    track = elem.find('track').text.strip()
    room = elem.find('room').text.strip()

    talk = dict()
    talk['id'] = elem.attrib['id']
    for x in elem:
        if x.text:
            talk[x.tag] = x.text.strip().encode('ascii', 'xmlcharrefreplace')
        else:
            talk[x.tag] = ''

    # calculate stop
    (sh, sm) = elem.find('start').text.split(':')
    hours = int(sh)
    minutes = int(sm)
    (dur_hr,dur_min) = elem.find('duration').text.split(':')
    newminutes = minutes + int(dur_min) + (60*int(dur_hr))
    if newminutes < 60:
        talk['stop'] = "%i:%s"%(hours, ("%i"%newminutes).zfill(2))
    else:
        talk['stop'] = "%i:%s"%(hours+(newminutes//60), ("%i"%(newminutes%60)).zfill(2))

    # speakers
    talk['speakers'] = [latexify(s.text) for s in elem.find('persons')]
    talk['allspeakers'] = ", ".join(talk['speakers'])
    talk['title'] = latexify(talk['title']).replace(' - ', ' -- ')
    talk['subtitle'] = latexify(talk['subtitle']).replace(' - ', ' -- ')
    talk['abstract'] = latexify(talk['abstract'])
    talk['description'] = latexify(talk['description'])

    return talk

def latexify(string):
    # f and b are only approximations to the correct characters
    return string.encode('ascii', 'xmlcharrefreplace').replace('&#10765;','f').replace('&#1073;','b').replace('&#8212;','\\textemdash{}').replace('&#345;','\\v{r}').replace('&#283;','\\\'{y}').replace('&#263;','\\\'{c}').replace('&#229;','\\r{a}').replace('&#242;','\\`{o}').replace('&#382;','\\v{z}').replace('&#192;','\\`{A}').replace('&#225;','\\`{a}').replace('&#233;','\\\'{e}').replace('&#353;','\\v{s}').replace('&#253;','\\\'{y}').replace('&#246;','\\"{o}').replace('&#228;','\\"{a}').replace('&#235;','\\"{e}').replace('&#201;','\\\'{E}').replace('&#252;','\\"{u}').replace('&#231;','\\c{c}').replace('&#232;','\\`{e}').replace('&#243;','\\\'{o}').replace('&#250;','\\\'{u}').replace('&#239;','\\"{\\i}').replace('&#241;','\\~{n}').replace('&#8217;', '\'').replace('&#8230;', '\\ldots{}').replace('&#251;','\\^{u}').replace('&#259;','\\u{a}').replace('&#248;','\\o{}').replace('&#237;','\\\'{i}').replace('&#352;','\\v{S}').replace('&#223;','\\ss').replace('<em>','\\textbf{').replace('</em>','}').replace('<ul>','').replace('</li></ul>','.').replace('</ul>','').replace('<li>','').replace('</li>',';').replace('#','\\#').replace('&','\\&').replace('_','\\_')


def urlify(string):
    return string.lower().replace(' ','-').replace('&','').replace('.','')


def get_groupname(event):
    return "%s-%s-%s-%s"%(
                urlify(event['type']),
                urlify(event['shortday']),
                urlify(event['track']),
                urlify(event['room']))
def get_texname(groupname):
    return "generated/%s.tex"%groupname

def write_tex(content, fname):
    hashtag = "% generator-hash:"
    newhash = hashlib.md5(content).hexdigest()
    oldhash = get_hash(fname, hashtag)

    if newhash != oldhash:
        # only when hashes (of ORIGINAL content!) differ
        out = open(fname, 'w')
        out.write("%s %s\n"%(hashtag, newhash))
        out.write("\n")
        out.write(content)
        print "Updated '%s'"%fname

def get_hash(fname, hashtag):
    # return the hash in the first line of the file (or "")
    try: 
        with open(fname) as f:
            firstline = f.readline()
            if firstline.startswith(hashtag):
                return firstline[len(hashtag):].strip()
    except Exception:
        pass
    return ""
    

def generate_tables(events):
    day_groups = defaultdict(list)
    for e in events:
        day_groups[e['day']].append(e)

    # slice seq in pieces of length rowlen
    def get_slice(seq, rowlen):
        for start in xrange(0, len(seq), rowlen):
            yield seq[start:start+rowlen]

    for (day_name, day_events) in day_groups.iteritems():
        fname = "gen-tables-%s.tex"%get_shortday(day_name)
        content = ""

        # hack: all rooms except if only certification there
        rooms = set([e['room'] for e in day_events if e['track'] != 'Certification'])

        # first page: main tracks and ltalks,
        #             in: Janson, K.1.105 and H.2215
        mainrooms = [r for r in ['Janson', 'K.1.105 (La Fontaine)', 'H.2215 (Ferrer)'] if r in rooms]
        restrooms = rooms.difference(mainrooms)
        paged_rooms = [mainrooms] + [x for x in get_slice(sorted(restrooms), 4)]


        # per page 4 rooms, so it fits in modulo4 pages
        for (i,room_slice) in enumerate(paged_rooms):
            subroom_events = [e for e in day_events if e['room'] in room_slice]
                
            # create subfile
            subcontent = "\\pagebreak"
            subcontent += table_events(subroom_events, get_shortday(day_name))
            subfile = get_texname("tableify_events_%s_%i"%
                                        (get_shortday(day_name),i) )
            write_tex(subcontent, subfile)

            # include subfile
            content += "\\input{%s}\n"%subfile

        write_tex(content, fname)

def truncate(msg, length):
    # this should better be done in latex, but too advanced for me (Tias)
    if len(msg) <= length:
        return msg

    pos = msg.rfind(' ', 0, int(length))
    return "%s\\dots"%msg[0:pos]

def table_events(allevents, msg=""):
    t = lambda s: datetime.datetime.strptime(s, '%H:%M')

    def roomhack(name):
        # map has 'AW' as building name, not AW1
        if name.startswith('AW1'):
            return name.replace('AW1','AW')
        elif name.startswith('UA2'):
            return name.replace('UA2','UA')
        elif name.startswith('UB2'):
            return name.replace('UB2','UB')
        elif name.startswith('UD2'):
            return name.replace('UD2','UD')
        # map has 'J' as building name
        elif name == 'Janson':
            return 'J.Janson'
        else:
            return name

    def titlehack(name):
        # for rooms with a too long name
        if name == 'HPC and computational science':
            return 'HPC and comp. science'
        elif name == 'Configuration management':
            return 'Configuration mngmt'
        elif name == 'Microkernel-based operating systems':
            return 'Microkernel-based OSs'
        else:
            return name


    roomTevents = defaultdict(list)
    roomTitle = defaultdict()
    for e in allevents:
        start = t(e['start'])
        stop = t(e['stop'])
        room = roomhack(e['room'])
        roomTevents[room].append( (start,stop, e) )
        # title
        roomTitle[room] = titlehack(e['track'])
        if e['type'] in ['maintrack', 'keynote']:
            roomTitle[room] = "Main tracks"

    f_roomstart = lambda tEvents: min( [e[0] for e in tEvents] )
    f_roomstop  = lambda tEvents: max( [e[1] for e in tEvents] )
    daystart = min( [f_roomstart(tEvents) for tEvents in roomTevents.values()] )
    daystop  = max( [f_roomstop(tEvents)  for tEvents in roomTevents.values()] )

    # returns (status, event)
    # where status one of 'START', 'MID', 'NONE'
    def find_tEvent_hour(tEvents, hour, delta):
        for e in tEvents:
            if hour-delta < e[0] <= hour:
                return ('START',e)
            #elif hour < e[1] <= hour+delta:
            #    return ('END',e)
            elif e[0] < hour < e[1]:
                return ('MID',e)
        return ('NONE',None)

    rooms = sorted(roomTevents.keys())
    # hack: main tracks fixed order
    if 'Main tracks' in roomTitle.values():
        # wanted: J.Janson, K.1.105, H.2215
        if rooms[0].startswith('H.2215'):
            ltalk = rooms.pop(0)
            rooms.append(ltalk)
        

    content = "\\begin{talktable}{%i}\n"%len(rooms)

    # header: room & track
    for r in rooms:
        content += " & \HeaderTitle{%s}"%roomTitle[r]
    content += "\\\\ \n"
    for r in rooms:
        content += " & \HeaderSubtitle{%s}"%r
    content += "\\\\ \\thickcline{%i-%i} \n"%(1,len(rooms)+1)

    # iterate per hour
    curhour  = daystart
    delta    = datetime.timedelta(minutes=5)
    tblocks  = ['00', '15', '30', '45']
    while (curhour < daystop):
        # print time (in blocks)
        strhour = curhour.strftime('%H:%M')
        if True in [strhour.endswith(x) for x in tblocks]:
            xtra = ""
            if strhour.endswith('00'):
                content += "\\cellcolor{gray!25}"
                xtra = "\\bf"
            elif strhour.endswith('30'):
                content += "\\cellcolor{gray!15}"
            content += "\\raisebox{-0.4ex}{\\small%s %s}"%(xtra, strhour)

        xtra = ""
        if strhour.endswith('55'):
            xtra = "thick"
        clines = "\\%scline{%i-%i} "%(xtra,1,1)

        for i,room in enumerate(rooms):
            content += " & "
            (status,tEv) = find_tEvent_hour(roomTevents[room], curhour, delta)
            if status == 'NONE':
                if strhour.endswith('00'):
                    content += "\\cellcolor{gray!25}"
                elif strhour.endswith('30'):
                    content += "\\cellcolor{gray!15}"
            elif status == 'START':
                e = tEv[2]
                msg = e['title']
                speakers = e['speakers']
                timerows = math.ceil((tEv[1] - tEv[0]).total_seconds() / delta.total_seconds())
                linelength = 25
                if timerows == 1:
                    # restrict and truncate to 1 row
                    content += "\\truncate{\linewidth}{%s}\n"%msg
                elif timerows == 2:
                    # restrict and truncate to 1 row, but with title styled (=larger)
                    content += "\\CellTalkSingle{%i}{%s}{%s}\n"%\
                                 (timerows, msg, "")
                elif timerows == 3 or timerows == 4:
                    tspeakers = ", ".join(speakers)
                    texcmd = "CellTalk"
                    if len(msg) <= linelength:
                        # case 1: title (fits 1 line) + author 1 line
                        texcmd += "Trunk"
                    else:
                        # 2 lines of text, author inline if enough space
                        texcmd += "TrunkTrunk"
                        #restchars = (linelength*2) - len(msg)
                        #if restchars < 12:
                        #    # inline author
                        #    minipage += larger(truncate(msg, linelength*2))
                    content += "\\%s{%i}{%s}{%s}\n"%\
                               (texcmd, timerows, msg, tspeakers)

                else:
                    tspeakers = ", ".join(speakers)
                    texcmd = "CellTalk"
                    linesleft = math.ceil(timerows/2)

                    if (1.0*len(msg)/linelength) > (linesleft-1): #-1 for author
                        # message too long, truncate it
                        msg = truncate(msg, linelength*(linesleft-1))
                    linesleft -= math.ceil(1.0*len(msg)/linelength)

                    if linesleft <= 1:
                        texcmd += "Trunk"
                    else:
                        tspeakers = truncate(", ".join(speakers),
                                             (linelength*(linesleft-1))-4) # minus ' -
                        linesleft -= math.ceil(len(tspeakers)/linelength)

                        if linesleft <= 1:
                            texcmd += "Compact"
                    content += "\\%s{%i}{%s}{%s}\n"%\
                               (texcmd, timerows, msg, tspeakers)

            # draw line under this cell?
            if status == 'NONE' or \
               curhour <= tEv[1] <= curhour+delta: # end of slot
                xtra = ""
                if strhour.endswith('55'):
                    xtra = "thick"
                clines += "\\%scline{%i-%i} "%(xtra,i+2,i+2) # offset 0
        content += "\\\\ "+clines+"%\n"
        curhour += delta
    content += "\\thickcline{%i-%i}"%(1,len(rooms)+1)
    content += "\\end{talktable}%\n"

    return content


if __name__ == "__main__":
    xmlfile = 'xml'

    if len(sys.argv) == 1:
	if not os.path.isfile(xmlfile):
            print "Usage: %s schedule.xml"%sys.argv[0]
            sys.exit(1)
    else:
    	xmlfile = sys.argv[1]

    events = get_xml_events(xmlfile)

    # write out generated tables in subfiles
    generate_tables(events)

    print "Done, everything up-to-date."
