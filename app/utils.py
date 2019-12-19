import json
from datetime import datetime
from itertools import combinations
from .models import Course
# This file consists of all helper functions

def run(rawString = '',numCourses = 5):
    errors = None
    (courseList,errors) = dissect(rawString)
    scheduleList = getAllValidSchedules(courseList,numCourses)

    def sortByScore(val):
        return getScore(val)

    scheduleList.sort(key=sortByScore, reverse=True)

    return (scheduleList[:10],errors)

def dissect(rawString):
    rtn = []
    error = None;
    failed = []
    rawString = rawString.split("\r\n \r\n")
    for i in rawString:
        try:
            rtn.append(getCourse(i))
        except:
            error = ['Some content could not be parsed.']
            try:
                t = i.strip().split('\n')[0].split('\t')
                failed.append(t[2] + " " + t[3])
            except:
                failed.append("\"{}\"".format(i))

    if error != None and len(rtn)>0:
        error.append('{} Courses parsed, failed parses:'.format(len(rtn)))
        for c in failed:
            error.append('- ' + c)

    return (rtn,error)

def getCourse(rawString):
    split = rawString.strip().split('\n')
    split[0] = split[0].split('\t')
    found = Course()
    found.status = split[0][0]
    found.crn = split[0][1]
    found.code = split[0][2] #+ " " + split[0][3]
    found.section = split[0][3]
    found.name = split[0][4]
    found.credits = float(split[0][5])
    found.type = split[0][6]
    found.instructor = split[0][10].strip()
    found.days = split[1][split[1].find('Days:') + 6:split[1].find('Time:') - 1].split()
    found.time = split[1][split[1].find('Time:') + 6:split[1].find('Building:') - 1].split(' - ')
    if (found.time == ['']):
        found.time = []

    i = 5
    found.reqs = []
    for line in split:
        if ('Also Register in:' in line):
            temp = line.split()
            while i < len(temp):
                if (temp[i] != 'or'):
                    found.reqs.append(found.code + ' ' + temp[i])
                i += 1
            break

    try:
        temp = str(datetime.strptime(found.time[1], '%H:%M') - datetime.strptime(found.time[0], '%H:%M')).split(':')
        found.length = round(float(int(temp[0]) + float(int(temp[1])/60))*2)/2
    except:
        found.length = 0

    # Fix arrays
    found.days = json.dumps(found.days)
    found.time = json.dumps(found.time)
    found.reqs = json.dumps(found.reqs)

    return found

def generateCalenderInput(courseList=[]):
    calender = []
    getIndex00 = {'Sun': 1, 'Mon': 2, 'Tue': 3, 'Wed': 4, 'Thu': 5, 'Fri': 6, 'Sat': 7}
    getIndex30 = {'Sun': 9, 'Mon': 10, 'Tue': 11, 'Wed': 12, 'Thu': 13, 'Fri': 14, 'Sat': 15}

    # find range of times to display to user
    earliest = 24
    latest = 0
    for i in courseList:
        temp = int(i['time'][0].split(':')[0])
        if temp < earliest:
            earliest = temp
        temp = int(i['time'][1].split(':')[0])
        if (i['time'][1].split(':')[1][0] == '5'): temp += 1 # will handle :55's
        if temp > latest:
            latest = temp
    if earliest < 9: earliest = 9 # earliest will be 8

    # Generate starter calender input (blank calender)
    for i in range(earliest-1,latest+1):
        temp = [''] * 16
        temp[0] = str(i) + ":00"
        calender.append(temp)

    # Go through courses and add them to calender
    for course in courseList:
        cHour = course['time'][0].split(':')[0] #course start time hour
        if (cHour[0] == '0'): cHour = cHour[1] # remove starting 0

        for i in range(len(calender)):
            if calender[i][0].split(':')[0] == cHour: # found correct hour
                curIndex = []
                # find correct half hour and get starting index
                if course['time'][0].split(':')[1][0] == '0':
                    for d in course['days']:
                        curIndex.append(getIndex00[d])
                elif course['time'][0].split(':')[1][0] == '3':
                    for d in course['days']:
                        curIndex.append(getIndex30[d])

                # add to array (calender)
                for s in range(round(course['length']*2)):
                    for wd in curIndex:
                        calender[i][wd] = course['code'] + ' ' + course['section']
                    if (curIndex[0] < 7):
                        for wd in range(len(curIndex)):
                            curIndex[wd] += 8
                    else:
                        i += 1
                        for wd in range(len(curIndex)):
                            curIndex[wd] -= 8

                break;

    return calender

def getAllValidSchedules(courseList=[], numLectures = 5):
    rtn = []
    numLecturesWithTutorial = len([i for i in courseList if i['type'] == 'Lecture' and len(i['reqs']) > 0])
    maxNum = numLectures + min(numLecturesWithTutorial,numLectures)
    for i in range(numLectures,maxNum+1):
        allPossibilities = combinations(courseList, i)
        for schedule in allPossibilities:
            if isCalenderValid(schedule,numLectures):
                rtn.append(schedule)

    return rtn

def getScore(schedule, dayOffScore = 10, waitHourPenalty = -4,badStartEndHourPenalty = -2,shortDayPenalty = -10):
    score = 0

    hoursPerDay = getHoursPerDay(schedule)
    daysOff = 0
    for d in hoursPerDay:
        if hoursPerDay[d] == 0:
            daysOff += 1
    score += (dayOffScore * daysOff)

    score += (waitHourPenalty * getWaitHours(schedule))
    score += (badStartEndHourPenalty * getHoursOutOfBounds(schedule))

    for d in hoursPerDay:
        if hoursPerDay[d] < 2:
            score += shortDayPenalty

    return score

def isCalenderValid(courseList=[],numLectures = 5):
    # Ensure there is a calender
    if courseList == []: return False

    # ensure all classes are 'Open'
    # notOpen = [i for i in courseList if 'Open' not in i['status'] and i['status'] != 'Already Registered']
    # if len(notOpen) > 0:
    #     return False

    lectures = [i for i in courseList if i['type'] == 'Lecture']
    tutorials = [i for i in courseList if i['type'] == 'Tutorial']

    # check if correct # of lectures is present
    if len(lectures) != numLectures: return False

    # check for any overlaps
    if isAnyOverlap(courseList): return False

    # check for duplicate lectures (eg COMP 3000 A and COMP 3000 B)
    for c in range(len(lectures)):
        for i in range(c+1,len(lectures)):
            if (lectures[c]['code'] == lectures[i]['code']):return False

    # ensure tutorial requirements are met (as well as max 1 per class)
    numFoundOwner = 0 # used to ensure all tutorials have an owner
    for c in lectures:
        foundTut = False
        for check in tutorials:
            if check['type'] != 'Lecture' and c['code'] == check['code'] and check['code'] + ' ' + check['section'] in c['reqs']:
                if foundTut:return False # we found 2 applicable tutorials

                foundTut = True
                numFoundOwner += 1

        # Check if req was met
        if len(c['reqs']) > 0 and not foundTut:return False
    if numFoundOwner != len(tutorials): return False

    # if everything passed then schedule is valid
    return True

def isAnyOverlap(courseList=[]):
    toCheck = combinations(courseList, 2)

    for cur in toCheck:
        if not set(cur[0]['days']).isdisjoint(cur[1]['days']):
            # try to determine if there is a gap between courses (only if on same day)
            timeOne = cur[0]['time']
            timeTwo = cur[1]['time']

            # Find closest points
            latestStart = timeOne if (int(timeOne[0].split(':')[0]) > int(timeTwo[0].split(':')[0])) else timeTwo
            earliestEnd = timeOne if (int(timeOne[1].split(':')[0]) < int(timeTwo[1].split(':')[0])) else timeTwo

            # if one class has swallowed another or overlap return false
            if latestStart == earliestEnd or int(latestStart[0].split(':')[0]) < int(earliestEnd[1].split(':')[0]):
                return True
            # if the gap points share the hour - check the min
            if int(latestStart[0].split(':')[0]) == int(earliestEnd[1].split(':')[0]):
                if int(latestStart[0].split(':')[1]) <= int(earliestEnd[1].split(':')[1]):
                    return True
    return False

def getHoursOutOfBounds(courseList=[], minHour = 10, maxHour = 17):
    rtn = 0
    for c in courseList:
        if (int(c['time'][0].split(':')[0]) < minHour): # if course starts before minHour
            if (int(c['time'][1].split(':')[0]) < minHour): # if course ends before minHour
                rtn += c['length']
            else: # course start < minHour < courseEnd
                temp = str(datetime.strptime('{}:00'.format(minHour), '%H:%M') - datetime.strptime(c['time'][0], '%H:%M')).split(':')
                temp = round(float(int(temp[0]) + float(int(temp[1]) / 60)) * 2)
                rtn += temp/2

        if (int(c['time'][1].split(':')[0]) >= maxHour): # if course ends after maxHour
            if (int(c['time'][0].split(':')[0]) >= maxHour): # if course starts after maxHour
                rtn += c['length']
            else: # course start < maxHour < courseEnd
                temp = str(datetime.strptime(c['time'][1], '%H:%M') - datetime.strptime('{}:00'.format(maxHour), '%H:%M')).split(':')
                temp = round(float(int(temp[0]) + float(int(temp[1]) / 60)) * 2)
                rtn += temp/2
    # the "round(... * 2) /2"'s are to ensure all time units (30min) stays consistant
    return rtn

def getWaitHours(courseList=[]):
    rtn = float(0)
    # Assumes courseList is a valid schedule
    weekDays = {}
    for c in courseList:
        for d in c['days']:
            if d not in weekDays.keys():
                weekDays[d] = []
            weekDays[d].append(c['time'])

    def sortTimes(val):
        return val[0]
    for d in weekDays:
        weekDays[d].sort(key = sortTimes)
        for t in range(len(weekDays[d])):
            try:
                temp = str(datetime.strptime(weekDays[d][t+1][0], '%H:%M') - datetime.strptime(weekDays[d][t][1], '%H:%M')).split(':')
                rtn += round(float(int(temp[0]) + float(int(temp[1]) / 60)) * 2) / 2
            except IndexError:
                pass
    return rtn

def getHoursPerDay(courseList):
    rtn = {'Mon':0, 'Tue':0, 'Wed':0, 'Thu':0, 'Fri':0}
    for c in courseList:
        for d in c['days']:
            rtn[d] += c['length']
    return rtn