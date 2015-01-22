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

# from https://github.com/whimboo/mozdownload/commit/f1c524a50265f931c8954d1ea2b10b8fb845ea18
def total_seconds(td):
    # Keep backward compatibility with Python 2.6 which doesn't have
    # this method
    if hasattr(td, 'total_seconds'):
        return td.total_seconds()
    else:
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


def get_xml_events(xmlfile):
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    events = []

    for x in list(root):
        if x.tag == 'conference':
            pass
        elif x.tag == 'day':
            events += get_day_events(x)

    emptyrooms = []
    for x in list(root):
        if x.tag == 'day':
            day = date2str(x.attrib['date'])
            for y in x:
                if y.tag == 'room' and len(y) == 0:
                    room = y.attrib['name']
                    emptyrooms.append( (day,room) )

    return (events,emptyrooms)

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
    return string.encode('ascii', 'xmlcharrefreplace').replace('&#10765;','f').replace('&#1073;','b').replace('&#8212;','\\textemdash{}').replace('&#345;','\\v{r}').replace('&#283;','\\\'{y}').replace('&#263;','\\\'{c}').replace('&#229;','\\r{a}').replace('&#242;','\\`{o}').replace('&#269;','\\v{c}').replace('&#382;','\\v{z}').replace('&#192;','\\`{A}').replace('&#324;','\\\'{n}').replace('&#225;','\\`{a}').replace('&#233;','\\\'{e}').replace('&#353;','\\v{s}').replace('&#253;','\\\'{y}').replace('&#246;','\\"{o}').replace('&#228;','\\"{a}').replace('&#235;','\\"{e}').replace('&#214;','\\"{O}').replace('&#201;','\\\'{E}').replace('&#252;','\\"{u}').replace('&#231;','\\c{c}').replace('&#232;','\\`{e}').replace('&#243;','\\\'{o}').replace('&#250;','\\\'{u}').replace('&#239;','\\"{\\i}').replace('&#241;','\\~{n}').replace('&#8217;', '\'').replace('&#8230;', '\\ldots{}').replace('&#251;','\\^{u}').replace('&#259;','\\u{a}').replace('&#248;','\\o{}').replace('&#237;','\\\'{i}').replace('&#352;','\\v{S}').replace('&#223;','{\\ss}').replace('&#322;','\\l{}').replace('&#216;','{\\O}').replace('<em>','\\textbf{').replace('</em>','}').replace('<ul>','').replace('</li></ul>','.').replace('</ul>','').replace('<li>','').replace('</li>',';').replace('#','\\#').replace('&','\\&').replace('_','\\_')


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
    

def generate_tables(events,emptyrooms=[]):
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
        # plus empty ones, with hardcoded exceptions
        rooms |= set([room for (day,room) in emptyrooms if day == day_name and (room != "H.3227") ])

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
            subcontent += table_events(room_slice, subroom_events, get_shortday(day_name))
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

def table_events(rooms, allevents, msg=""):
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
        if name == 'Network management and SDN':
            return 'Network managmt and SDN'
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

    print daystart, daystop

    # returns (status, event)
    # where status one of 'START', 'MID', 'NONE'
    def find_tEvent_hour(tEvents, hour, delta):
        for e in tEvents:
            if hour-delta < e[0] <= hour and hour < e[1] <= hour+delta:
                return ('STARTEND',e)
            elif hour < e[1] <= hour+delta:
                return ('END',e)
            elif hour-delta < e[0] <= hour:
                return ('START',e)
            elif e[0] < hour < e[1]:
                return ('MID',e)
        return ('NONE',None)

    #rooms = sorted(roomTevents.keys())
    rooms = sorted([roomhack(r) for r in rooms])
    # handle empty rooms
    for r in rooms:
        if not r in roomTitle:
            roomTitle[r] = ''
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
    content += "\\\\ \\hhline{*{%i}-} \n"%(len(rooms)+1)

    # iterate per hour
    delta    = datetime.timedelta(minutes=5)
    tblocks  = ['00', '15', '30', '45']
    curhour  = daystart
    while not curhour.strftime('%M') in tblocks:
        curhour -= delta
    while (curhour < daystop):
        # print time (in blocks)
        strhour = curhour.strftime('%H:%M')
        if True in [strhour.endswith(x) for x in tblocks]:
            xtra = ""
            if strhour.endswith('00'):
                xtra = "\\bf"
            content += "\\raisebox{-0.33ex}{\\small%s %s}"%(xtra, strhour)

        # remove thickness diffs
        #clineidx = 0
        #if strhour.endswith('25'):
        #    clineidx = 1
        #elif strhour.endswith('55'):
        #    clineidx = 2
        #clines = "\\thickcline{%i}{%i}{%s} "%(1,1,clinesizes[clineidx])
        hharg = ">{\\arrayrulecolor{black}}-"

        for i,room in enumerate(rooms):
            content += " & "
            (status,tEv) = find_tEvent_hour(roomTevents[room], curhour, delta)
            if status == 'END' or status == 'STARTEND':
                e = tEv[2]
                msg = e['title']
                speakers = e['speakers']
                timerows = math.ceil(total_seconds(tEv[1] - tEv[0]) / total_seconds(delta))
                linelength = 32*4/len(rooms)
                # The horror, manual hacks...
                if msg.startswith('Xvisor'):
                    linelength = 28*4/len(rooms)
                if msg.startswith('Caciocavallo'):
                    linelength = 30*4/len(rooms)
                if msg.startswith('Taking Web GIS'):
                    linelength = 30*4/len(rooms)

                if timerows == 1:
                    # restrict and truncate to 1 row
                    content += "\\CellBG\\truncate{\linewidth}{%s}\n"%msg
                elif timerows == 2:
                    # restrict and truncate to 1 row, but with title styled (=larger)
                    content += "\\CellTalkSingle{%i}{%s}{%s}\n"%\
                                 (timerows, msg, "")
                else:
                    tspeakers = ", ".join(speakers)
                    texcmd = "CellTalk"
                    lines = math.ceil(timerows/2)
                    linesmsg = math.ceil(1.0*len(msg)/linelength)
                    linesspkr = math.ceil(0.8*len(tspeakers)/linelength)

                    debug = msg
                    debug += " lines: %f"%lines
                    debug += " msg: %f, sprk: %f"%(linesmsg,linesspkr)

                    if (len(msg) <= linelength*(lines-1)): # -1 for authors
                        # case 1: title fits
                        if linesmsg + linesspkr < lines:
                            # case 1.1: ample space
                            #print "Ample", debug
                            pass
                        elif linesmsg + linesspkr == lines:
                            # case 1.2: just, fewer space between title/author
                            # TODO: sometimes text on border
                            #print "Compact", debug
                            texcmd += "Compact"
                        else:
                            # case 1.2: too few, trunc authors
                            linesleft = lines - linesmsg
                            debug += " linesleft: %f"%linesleft
                            if linesleft == 1:
                                # case 1.2.1: one line of author, use truncate{}
                                print "AuthorTrunk", debug
                                texcmd += "AuthorTrunk"
                            else:
                                # case 1.2.1: multiple lines, manual trucate
                                print "AuthorTrunk, manual", debug
                                texcmd += "Compact"
                                lines = lines
                                tspeakers = truncate(tspeakers,
                                             (linelength*(linesleft)-4)) # minus ' --
                    else:
                        # case 2: title doesn't fit
                        if len(tspeakers) <= linelength*0.7:
                            # case 2.1 make author inline
                            # estimate title truncation...
                            chars = lines*linelength
                            chars -= 7+len(tspeakers)*0.7
                            if len(msg) >= chars:
                                print "Inline Author, MsgTrunk", debug
                                msg = truncate(msg, chars)
                            texcmd += "Inline"
                        elif lines == 2:
                            if linesspkr == 1:
                                # case 2.2.1 one line title, one line author
                                print "MsgTrunk", debug
                                texcmd += "MsgTrunk"
                            else:
                                # case 2.2.2 one line title, one line author
                                print "MsgTrunk + AuthorTrunk", debug
                                texcmd += "TrunkTrunk"
                        else:
                            msg = truncate(msg, linelength*(lines-1))
                            if linesspkr == 1:
                                # case 2.3.2 multi-line title, one line author
                                print "MsgTrunk (manual)", debug
                                texcmd += "Compact"
                            else:
                                # case 2.3.2 multi-line title, one line author
                                print "MsgTrunk (manual) + AuthorTrunk", debug
                                texcmd += "AuthorTrunk"

                    content += "\\%s{%i}{%s}{%s}\n"%\
                               (texcmd, timerows, msg, tspeakers)
            elif status == 'MID' or status == 'START':
                content += "\\CellBG"

            prestart = (find_tEvent_hour(roomTevents[room], curhour+delta, delta)[0] in ['START', 'STARTEND']) # next delta, a talk will start
            if prestart or status == 'END' or status == 'STARTEND':
                hharg += ">{\\arrayrulecolor{black}}-"
            elif status == 'MID' or status == 'START':
                hharg += ">{\\arrayrulecolor{gray!20}}-"
            else:
                hharg += "~"
        content += "\\\\ \\hhline{%s} \n"%hharg
        curhour += delta
    #content += "\\thickcline{%i}{%i}{%s}"%(1,len(rooms)+1,clinesizes[2])
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

    (events,emptyrooms) = get_xml_events(xmlfile)

    # write out generated tables in subfiles
    generate_tables(events,emptyrooms=emptyrooms)

    print "Done, everything up-to-date."
