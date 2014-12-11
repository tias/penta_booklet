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
    

def generate_chapters(events):
    type_groups = defaultdict(list)
    for e in events:
        type_groups[e['type']].append(e)

    for (type_name, type_events) in type_groups.iteritems():
        if type_name == 'lightningtalk':
            generate_chap_lightningtalk(type_events)
        elif type_name == 'keynote':
            generate_chap_keynotes(type_events)
        elif type_name == 'certification':
            generate_chap_certification(type_events)
        elif type_name == 'maintrack':
            generate_chap_maintrack(type_events)
        elif type_name == 'devroom':
            generate_chap_devroom(type_events)

def generate_chap_lightningtalk(events):
    fname = "gen-chap-lightningtalks.tex"
    days = defaultdict(list)
    for e in events:
        days[e['day']].append(e)

    content = ""
    content += "\\section{%s}\n"%events[0]['track']
    content += "{\\bf %s}\n"%events[0]['room']
    content += "\n"
    content += get_devroom_descr(events[0]['track'])
    for day, dayevents in sorted(days.iteritems()):
        content += "\\subsection*{Lightning talks, %s}\n"%dayevents[0]['day'].split(' ')[0]
        # create subfile
        subcontent = get_roomoverview(dayevents, title=False, label=True)
        subfile = get_texname(get_groupname(dayevents[0]))
        write_tex(subcontent, subfile)
        # include subfile
        content += "\\input{%s}\n"%subfile
        content += "\\pagebreak\n"

    write_tex(content, fname)

def generate_chap_keynotes(events):
    fname = "gen-chap-keynotes.tex"

    content = ""
    content += "\\section{%s}\n"%events[0]['track']
    content += "{\\bf %s}\n"%events[0]['room']
    content += "\n"

    # create subfile
    subcontent  = "% overview of all keynotes (sat and sun)\n"
    subcontent += get_roomoverview(events, title=False, label=False)
    subcontent += "\n"
    subcontent += get_maintrack(events)
    subfile = get_texname('keynotes')
    write_tex(subcontent, subfile)

    # include subfile
    content += "\\input{%s}\n"%subfile
    write_tex(content, fname)

def generate_chap_certification(events):
    fname = "gen-chap-certification.tex"
    # group by speakers and days
    organizerdays = dict()
    for e in events:
        if not e['allspeakers'] in organizerdays:
            organizerdays[e['allspeakers']] = defaultdict(list)
        organizerdays[e['allspeakers']][e['day']].append(e)

    content = ""
    content += "\\section{%s}\n"%events[0]['track']
    content += "%% some more intro?\n"
    content += "Please note that in order to take part in these exams, you need to have registered beforehand!\n\n"

    for organizer, orgdays in sorted(organizerdays.iteritems()):
        content += "\\subsection{%s}\n"%organizer
        for day, dayevents in sorted(orgdays.iteritems()):
            content += "\\paragraph{%s -- %s}\n"%(day.split(' ')[0], dayevents[0]['room'])
            content += get_roomoverview(dayevents, title=False, label=False)
        content += "\n"

    write_tex(content, fname)

def generate_chap_maintrack(events):
    fname = "gen-chap-maintracks.tex"
    # group by days and tracks
    daytracks = dict()
    for e in events:
        if not e['day'] in daytracks:
            daytracks[e['day']] = defaultdict(list)
        daytracks[e['day']][e['track']].append(e)

    content = ""
    #content += "\\pagestyle{empty}\n"
    content += "\\part{Main tracks}\n"
    content += "\n"

    # chapter title page
    for day, tracks in sorted(daytracks.iteritems()):
        content += "\\paragraph{%s}\n"%day
        content += get_trackoverview(tracks)

    content += "\\vspace*{\\fill}\n"
    content += "\\pagebreak\n"
    content += "\\pagestyle{plain}\n"

    # main tracks per day
    for day, tracks in sorted(daytracks.iteritems()):
        content += "\n"
        content += "\\begin{center}"
        content += "{\\Large \\bf Main tracks, %s}"%day.split(' ')[0]
        content += "\\end{center}"
        content += "%% %s\n"%day
        content += "\\label{%s-maintracks}\n"%get_shortday(day)
        for (track, events) in sorted(tracks.iteritems()):
            # create subfile
            subcontent = get_roomoverview(events, title=True, label=True, subtitle=False)
            subcontent += "\n"
            subcontent += get_maintrack(events)
            subfile = get_texname(get_groupname(events[0]))
            write_tex(subcontent, subfile)

            # include subfile
            content += "\\input{%s}\n"%subfile
        content += "\\label{%s-maintracks-end}\n"%get_shortday(day)
        content += "\\vspace{2em}\n"

    write_tex(content, fname)

def generate_chap_devroom(events):
    fname = "gen-chap-devrooms.tex"
    # group by days and tracks
    daytracks = dict()
    for e in events:
        if not e['day'] in daytracks:
            daytracks[e['day']] = defaultdict(list)
        daytracks[e['day']][e['track']].append(e)

    content = ""
    for day, tracks in sorted(daytracks.iteritems()):
        #content += "\\pagestyle{empty}\n"
        content += "\\part{Devrooms %s}\n"%day.split(' ')[0]
        content += "\\label{%s-devrooms}\n"%get_shortday(day)
        content += "\n"

        # chapter title page
        content += get_trackoverview(tracks)
        content += "\\vspace*{\\fill}\n"
        content += "\\pagebreak\n"
        content += "\\pagestyle{plain}\n"
        content += "\n"

        # devroom includes
        content += "%% devrooms of %s\n"%day
        i = 0
        for (track, events) in sorted(tracks.iteritems()):
            i += 1
            # create subfile
            subcontent = get_roomoverview(events, title=True, label=True)
            subcontent += "\n"
            subcontent += get_maintrack(events)
            subfile = get_texname(get_groupname(events[0]))
            write_tex(subcontent, subfile)

            # include subfile
            content += "\\input{%s}\n"%subfile
            if (i % 2 == 0):
                content += "\\pagebreak\n"

        content += "\\label{%s-devrooms-end}\n"%get_shortday(day)
        content += "\n"

    write_tex(content, fname)


def get_roomoverview(talks, title=True, label=True, subtitle=True):
    groupname = get_groupname(talks[0])
    content = ""

    # optional pre-stuff
    if label:
        content += "\\label{%s}\n"%groupname
    if title:
        content += "\\Room{%(track)s}{%(room)s}\n"%talks[0]
        content += get_devroom_descr(talks[0]['track'])

    content += "\\begin{roomoverview}\n"
    for talk in talks:
        if subtitle:
            content += "\\Event{%(title)s}{%(subtitle)s}{%(allspeakers)s}{%(dayofweek)s}{%(start)s}{%(stop)s}\n"%talk
        else:
            content += "\\Event{%(title)s}{}{%(allspeakers)s}{%(dayofweek)s}{%(start)s}{%(stop)s}\n"%talk
    content += "\\end{roomoverview}\n"

    # optional post-stuff
    if label:
        content += "\\label{%s-end}\n"%groupname

    return content

def get_maintrack(events):
    content = "\\begin{multicols}{2}\n"
    for talk in events:
        content += "\\Maintrack{%(title)s}{%(subtitle)s}{%(allspeakers)s}{%(dayofweek)s}{%(start)s}{%(stop)s}\n\n"%talk
        content += talk['abstract'].replace('<p>','').replace('</p>','\n') + "\n\n"
    content += "\\end{multicols}\n"

    return content

def get_trackoverview(tracks):
    content = "\\begin{trackoverview}\n"
    for (track, events) in sorted(tracks.iteritems()):
        content += "\\ItemTrack{%s}{%s}\n"%(track, get_groupname(events[0]))
    content += "\\end{trackoverview}\n"

    return content

def get_devroom_descr(track):
    slug = hrefname(track)
    fname = "devroom_descr/%s.html"%slug

    try:
        with open(fname, 'r') as fin:
            return fin.read().replace('#','\\#').replace('&','\\&').replace('_','\\_').replace('<p>','').replace('</p>','\n')
    except IOError:
        pass

    return ""

def generate_tables(events):
    fname = "gen-chap-tables.tex"
    content = ""

    day_groups = defaultdict(list)
    for e in events:
        day_groups[e['day']].append(e)

    # slice seq in pieces of length rowlen
    def get_slice(seq, rowlen):
        for start in xrange(0, len(seq), rowlen):
            yield seq[start:start+rowlen]

    for (day_name, day_events) in day_groups.iteritems():
        rooms = set([e['room'] for e in day_events])

        # per page 4 rooms
        for (i,room_slice) in enumerate(get_slice(sorted(rooms), 3)):
            subroom_events = [e for e in day_events if e['room'] in room_slice]
                
            # create subfile
            subcontent = table_events(subroom_events, get_shortday(day_name))
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
        # map has 'J' as building name
        elif name == 'Janson':
            return 'J.Janson'
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
        roomTitle[room] = e['track']
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

    larger = lambda msg: "{\\large %s}"%msg
    Larger = lambda msg: msg
    #Larger = lambda msg: "{\\small %s}"%msg

    rooms = sorted(roomTevents.keys())
    content = "\\pagebreak"
    content += "{\\fontsize{10}{8.2}\selectfont \\renewcommand{\\arraystretch}{0.9}%\n"
    content += "\\begin{tabu} to \\linewidth {c" + "X"*len(rooms) + "}%\n"

    # header: room & track
    content += "\multicolumn{1}{c}{} "
    for r in rooms:
        content += " & \multicolumn{1}{c}{\\bf %s} "%larger(roomTitle[r])
    content += "\\\\ \n"
    content += "\multicolumn{1}{c}{} "
    for r in rooms:
        content += " & \multicolumn{1}{c}{%s} "%larger(r)
    content += "\\\\ \\tabucline[1pt]- \n"

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

        clines = "\\cline{%i-%i} "%(1,1)
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
                if timerows == 1:
                    # restrict and truncate to 1 row
                    content += "\\truncate{\linewidth}{%s}"%msg
                elif timerows == 2:
                    # restrict and truncate to 1 row, but larger
                    msg = "\\truncate{\linewidth}{%s}"%msg
                    content += "\\multirow{%i}{\linewidth}{%s}"%(timerows,msg)
                elif timerows == 3 or timerows == 4:
                    authors = "{ -- %s}"%", ".join(speakers)
                    minipage = "\\begin{minipage}{\linewidth}"
                    linelength = 28
                    if len(msg) <= linelength:
                        # case 1: title 1 line + author 1 line
                        minipage += larger(msg)
                        minipage += "\\\\ \\truncate{\linewidth}{%s}"%authors
                    else:
                        # 2 lines of text, author inline if enough space
                        restchars = (linelength*2) - len(msg)
                        if restchars < 12:
                            minipage += larger(truncate(msg, linelength*2))
                        else:
                            minipage += larger(msg)
                            tspeakers = truncate(", ".join(speakers), restchars-4) # minus ' -- '
                            minipage += "{$ $ -- %s}"%tspeakers

                    minipage += "\\end{minipage}"
                    content += "\\multirow{%i}{\linewidth}{\parbox{\linewidth}{%s}}"%(timerows,minipage)
                else:
                    linelength = 20
                    linesleft = math.ceil(timerows/2)

                    if (len(msg)/linelength) > (linesleft-1): #-1 for author
                        # message too long, truncate it
                        msg = truncate(msg, linelength*(linesleft-1))
                    linesleft -= math.ceil(len(msg)/linelength)

                    tspeakers = truncate(", ".join(speakers),
                                         (linelength*(linesleft-1))-4) # minus ' -
                    linesleft -= math.ceil(len(tspeakers)/linelength)

                    minipage = "\\begin{minipage}{\linewidth}"
                    minipage += larger(msg)
                    if linesleft > 1:
                        # long version, with blank line between title/authors
                        minipage += "\\\\ $ $"
                    minipage += "\\\\ { -- %s}"%tspeakers
                    minipage += "\\end{minipage}"
                    # span multiple rows
                    content += "\\multirow{%i}{\linewidth}{\parbox{\linewidth}{%s}}"%(timerows,minipage)
            # draw line under this cell?
            if status == 'NONE' or \
               curhour <= tEv[1] <= curhour+delta: # end of slot
                clines += "\\cline{%i-%i} "%(i+2,i+2) # offset 0
        content += "\\\\ "+clines+"%\n"
        curhour += delta
    content += "\\tabucline[1pt]-"
    content += "\\end{tabu}}%\n" # last } closes {\tiny

    return content

def table_trackoverview(alltracks, day=""):
    roomtracks = defaultdict(list)
    for (track, events) in alltracks.iteritems():
        start = min([e['start'] for e in events])
        stop = max([e['stop'] for e in events])
        room = events[0]['room']
        # convert to time
        t = lambda s: datetime.datetime.strptime(s, '%H:%M')
        roomtracks[room].append( (t(start), t(stop), track, get_groupname(events[0])) )

    f_roomstart = lambda tracks: min( [t[0] for t in tracks] )
    f_roomstop  = lambda tracks: max( [t[1] for t in tracks] )
    daystart = min( [f_roomstart(tracks) for tracks in roomtracks.values()] )
    daystop  = max( [f_roomstop(tracks)  for tracks in roomtracks.values()] )

    # returns (status, track)
    # where status one of 'START', 'MID', 'END', 'NONE'
    def find_track_hour(tracks, hour, delta):
        for t in tracks:
            if hour-delta < t[0] <= hour:
                return ('START',t)
            elif hour <= t[1] <= hour+delta:
                return ('END',t)
            elif t[0] < hour < t[1]:
                return ('MID',t)
        return ('NONE',None)

    rooms = roomtracks.keys()
    content = ""
    content += "\\begin{center}\n"
    content += "\\begin{tabular}{|l" + "|l"*len(rooms) + "|}\n"
    content += "{\\bf %s} & "%day
    content += " & ".join(rooms) + "\\\\ \\hline\n"

    # iterate per hour
    curhour  = daystart
    delta    = datetime.timedelta(hours=1)
    while (curhour < daystop):
        content += "%s "%curhour.strftime('%H:%M')
        clines = "\\cline{%i-%i} "%(1,1)
        for i,room in enumerate(rooms):
            content += " & "
            (status,track) = find_track_hour(roomtracks[room], curhour, delta)
            if status == 'START':
                msg = "%s (page \\pageref{%s})"%(track[2],track[3])
                hours = math.ceil((track[1] - track[0]).seconds / 3600.0)
                if hours > 1:
                    # span multiple rows
                    content += "\multirow{%i}{*}{%s}"%(hours,msg)
                else:
                    content += msg
            elif status=='END' or status=='NONE':
                # draw line under this cell
                clines += "\\cline{%i-%i} "%(i+2,i+2) # offset 0
        content += "\\\\ "+clines+"\n"
        curhour += delta
    content += "\\hline \n" # for events ending on the last slot
    content += "\\end{tabular}\n"
    content += "\\end{center}\n"

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

    # write out generated chapters and subfiles
    generate_chapters(events)

    # write out generated tables in subfiles
    generate_tables(events)

    print "Done, everything up-to-date."
