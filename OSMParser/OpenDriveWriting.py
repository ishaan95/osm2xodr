#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 14:14:34 2019

@author: jhm
"""

#from .OSMparsing import OSMNode, OSMJunction, OSMNodeLink, OSMWay
import numpy as np

def writeOdrive():
    string= '''<?xml version="1.0" standalone="yes"?>
<OpenDRIVE>
    <header revMajor="1" revMinor="1" name="" version="1.00" date="Tue Mar 11 08:53:30 2014" north="0.0000000000000000e+00" south="0.0000000000000000e+00" east="0.0000000000000000e+00" west="0.0000000000000000e+00" maxRoad="3" maxJunc="0" maxPrg="0">
    </header>
    '''
    for road in openDriveRoad.roaddictionary.values():
        string += road.giveODriveString()
    for junction in openDriveJunction.junctions.values():
        string += junction.giveODriveString()
    string += '''
</OpenDRIVE>
    '''
    return string




class openDriveRoad:
    roadids = 1
    roaddictionary = {}
    OSMlinkToRoads = {}
    
    @staticmethod
    def reset():
        openDriveRoad.roadids = 1
        openDriveRoad.roaddictionary = {}
        openDriveRoad.OSMlinkToRoads = {}

    @staticmethod
    def giveId(road):
        openDriveRoad.roaddictionary[str(openDriveRoad.roadids)] = road
        openDriveRoad.roadids += 1
        return str(openDriveRoad.roadids-1)
    
    def __init__(self, length, x, y, hdg, wayIsOpposite, geoparam = None):
        self.id = openDriveRoad.giveId(self)
        self.geometrietyp = 'line' if geoparam is None else 'poly3'
        self.geoparam = geoparam
        self.length = length
        self.x = x
        self.y = y
        self.name = ""
        self.hdg = hdg
        self.heighta = ""
        self.heightb = ""
        self.lanesLeft = []
        self.laneMiddle = []
        self.lanesRight = []
        self.wayIsOpposite = wayIsOpposite   #if the tags are meant to read backwards (speed:forwards becomes speed:backwards)
        self.RoadLinksPredecessor = []
        self.RoadLinksSuccessor = []
        self.lanes = {}
        openDriveRoad.roaddictionary[self.id] = self
        self.OSMWay = None
        #self.OSMJunctionId = OSMNode.allOSMNodes[str(self.OSMnodeid)].idJunction
        self.odriveJunction = '-1'   ## nur die geraden sind die junctions - die Kurven sind einzellanes
    
    def giveODriveJunctionString(self, idx):
        string = ""
        for predecessorLink in self.RoadLinksPredecessor:
            for successorLink in self.RoadLinksSuccessor:
                _, predecessor,  contactPoint = link.giveODriveJunction(self)
                string += '''
                <connection id="{0}" incomingRoad="{1}" connectingRoad="{2}" contactPoint="{3}">
                '''.format(str(idx), predecessor, self.id, contactPoint)
                for laneLink in link.openDriveLaneLinks:
                    string += laneLink.giveOdriveJunctionString(self)
                string += '''
                </connection>
                '''

        if len(self.RoadLinksPredecessor) > 1:  # 
                string += link.giveODriveJunction(self)
        if len(self.RoadLinksSuccessor) > 1:  # 
            for link in self.RoadLinksSuccessor:
                string += link.giveODriveJunction(self)
        return string
 

    def giveODriveString(self):
        roadlinksPre = ""
        if len(self.RoadLinksPredecessor) > 0:
            roadlinksPre = self.RoadLinksPredecessor[0].giveODriveString(self)
        roadlinksSuc = ""
        if len(self.RoadLinksSuccessor) > 0:
            roadlinksSuc = self.RoadLinksSuccessor[0].giveODriveString(self)

        if self.geometrietyp == 'poly3':
            geo = '''
                <poly3 a="0" b="0" c="{0}" d="0"/>'''.format(self.geoparam)
        else:
            geo = '''
                <line/>'''

        leftlanes = ""
        for lane in self.lanesLeft:
            leftlanes += lane.giveODriveString()
        centerlanes = ""
        for lane in self.laneMiddle:
            centerlanes += lane.giveODriveString()
        rightlanes = ""
        for lane in self.lanesRight:
            rightlanes += lane.giveODriveString()

        elevation = '''
        <elevationProfile>
            <elevation s="0.0" a="{0}" b="{1}" c="0.00" d="0.00"/>
        </elevationProfile>'''.format(self.heighta, self.heightb)

        string =  '''    
        <road name="{3}" length="{0}" id="{1}" junction="{2}">
            <link>
                '''.format(self.length, self.id, self.odriveJunction, self.name) + '''
                {0}
                {1}'''.format(roadlinksPre,roadlinksSuc) + '''
            </link>
             <planView>
                <geometry s="0.0" x="{0}" y="{1}" hdg="{2}" length="{3}">
                '''.format(self.x, self.y, self.hdg, self.length) + geo + '''
                </geometry>
             </planView>
             {3}
             <lanes>
                <laneSection s="0.0">
                    <left>{0}
                    </left>
                    <center>{1}
                    </center>
                    <right>{2}
                    </right>
                </laneSection>
            </lanes>
        </road>
        '''.format(leftlanes, centerlanes, rightlanes, elevation)
        return string

        
class openDriveLane:
    def __init__(self, laneid, OpendriveRoad, OSMWay=None):
        self.id = laneid
        self.road = OpendriveRoad
        self.road.lanes[self.id] = self
        self.OSMway = OSMWay
        self.type = 'driving'
        self.width = "2.75e+00"
        self.roadmark = "broken"
        self.linksPredecessor = {} #roadId gives Connecting Lanenumber - lanelink trägt sich hier ein
        self.linksSuccessor = {} # roadId gives Connecting Lanenumber - lanelink trägt sich hier ein
        if self.id == 0:
            self.width = "0.0"
            #self.roadmark
            self.type = 'none'

    def giveODriveString(self):
        predecessor = ""
        if len(self.linksPredecessor) == 1:
            for preroad, val in self.linksPredecessor.items():
                if len(val) == 1:
                    predecessor = val[0].giveODriveString(self,self.road)
        successor = ""
        if len(self.linksSuccessor) == 1:
            for sucroad, val in self.linksSuccessor.items():
                if len(val) == 1:
                    successor = val[0].giveODriveString(self,self.road)
        #predecessor = '''<predecessor id="{0}"/>'''.format(self.OSMway.)

        return '''
                        <lane id="{0}" type="driving" level= "0">
                            <link>{1}{2}
                            </link>
                            <width sOffset="0.0" a="{3}" b="0.0" c="0.00" d="0.00"/>
                            <roadMark sOffset="0.00" type="{4}" weight="standard" color="standard" width="1.30e-01"/>
                        </lane>'''.format(self.id, predecessor, successor, self.width, self.roadmark)


class openDriveRoadMark:
    def __init__(self):
        self.type = 'broken'

class openDriveJunction:
    junctionids = 1
    junctiondictionary = {}
    junctions = {}
    roads = {}
    connections = {}
    
    @staticmethod
    def giveJunction(OSMWay, OSMNode):
        if str(OSMWay.id + OSMNode.id) in openDriveJunction.junctiondictionary:
            return openDriveJunction.junctiondictionary[OSMWay.id + OSMNode.id]
        else:
            j = openDriveJunction(OSMWay, OSMNode)
            return j
    
    @staticmethod
    def reset():
        openDriveJunction.junctionids = 1
        openDriveJunction.junctiondictionary = {}
    
    def __init__(self, OSMWay, rNode):
        '''One Junction for every Way in a JunctionNode'''
        self.id = str(openDriveJunction.junctionids)
        openDriveJunction.junctionids += 1
        self.OSMWay = OSMWay
        self.openDriveRoads = []
        self.openDriveRoadLinks = []
        openDriveJunction.junctions[str(self.id)] = self
        self.r1Roads = []
        self.r4Roads = []

    def register(self, opendriveRoad, r1=True):
        if r1 == True:
            self.r1Roads.append(opendriveRoad)
        else:
            self.r4Roads.append(opendriveRoad)
        opendriveRoad.odriveJunction = self.id

    def giveODriveString(self):
            connString = ""
            idx = 0
            for incomingRoad in self.r1Roads:
                connString += incomingRoad.giveODriveJunctionString(idx)
                idx +=1

            string = '''
            <junction name="" id="{0}">
                 {1}
            </junction>
            '''.format(str(self.id), connString)

        
class openDriveLaneLink:
    def __init__(self, PredecessorRoad, SuccessorRoad, PredecessorLane, SuccessorLane):
        try: SuccessorLane = SuccessorLane.id
        except: pass
        try: PredecessorLane = PredecessorLane.id
        except: pass
        self.predecessor = PredecessorRoad
        self.successor = SuccessorRoad
        self.predecessorLane = PredecessorLane
        self.successorLane = SuccessorLane
        try: self.predecessor.lanes[PredecessorLane].linksSuccessor[SuccessorRoad].append(self)
        except: 
            self.predecessor.lanes[PredecessorLane].linksSuccessor[SuccessorRoad] = [self]
        try: self.successor.lanes[SuccessorLane].linksPredecessor[PredecessorRoad].append(self)
        except: 
            self.successor.lanes[SuccessorLane].linksPredecessor[PredecessorRoad] = [self]
            

    def giveODriveString(self, questionLane, questionRoad):
        if questionRoad == self.predecessor:
            if questionLane.id == self.predecessorLane:
                return '''
                \t\t\t<successor id ="{0}"/>'''.format(self.successorLane)
        if questionRoad == self.successor:
            if questionLane.id == self.successorLane:
                return '''
                \t\t\t<predecessor id="{0}"/>'''.format(self.predecessorLane)
        else:
            return ""

    def giveOdriveJunctionString(self, oDriveRoad):
        if oDriveRoad.id == self.predecessor:
            return '\t\t\t<laneLink from="{0}" to="{1}"/>'.format(str(self.predecessorLane),str(self.successorLane))
        if oDriveRoad.id == self.successor:
            return '\t\t\t<laneLink from="{0}" to="{1}"/>'.format(str(self.successorLane),str(self.predecessorLane))
        return ""
    
class openDriveRoadLink:
    def __init__(self, oDriveRoadPredecessor, oDriveRoad, contactPointRoad, contactPointPredecessor):
        self.oDriveRoadPredecessor = oDriveRoadPredecessor
        self.oDriveRoad = oDriveRoad
        self.contactPointRoad = contactPointRoad
        self.contactPointPredecessor = contactPointPredecessor
        self.openDriveLaneLinks = []
        #oDriveRoadPredecessor.RoadLinksSuccessor.append(self)
        #oDriveRoad.RoadLinksPredecessor.append(self)

    def evaluateLaneLinks(self):
        if len(self.openDriveLaneLinks) == 0 and len(self.oDriveRoadPredecessor.lanes) > 0 and len(self.oDriveRoadPredecessor.lanes)==len(self.oDriveRoad.lanes):
            for lane in self.oDriveRoadPredecessor.lanesLeft:
                contactID = lane.id if self.contactPointRoad != self.contactPointPredecessor else -lane.id
                contactID = -contactID if self.oDriveRoadPredecessor.wayIsOpposite != self.oDriveRoad.wayIsOpposite and (self.oDriveRoad.geometrietyp == 'line' and self.oDriveRoadPredecessor.geometrietyp == 'line') else contactID
                link = openDriveLaneLink(self.oDriveRoadPredecessor, self.oDriveRoad, lane.id, contactID)
                self.openDriveLaneLinks.append(link)
            for lane in self.oDriveRoadPredecessor.lanesRight:
                contactID = lane.id if self.contactPointRoad != self.contactPointPredecessor else -lane.id
                contactID = -contactID if self.oDriveRoadPredecessor.wayIsOpposite != self.oDriveRoad.wayIsOpposite and (self.oDriveRoad.geometrietyp == 'line' and self.oDriveRoadPredecessor.geometrietyp == 'line') else contactID
                link = openDriveLaneLink(self.oDriveRoadPredecessor, self.oDriveRoad, lane.id, contactID)
                self.openDriveLaneLinks.append(link)

    def giveODriveJunction(self, oDriveRoadQuestion):
        if oDriveRoadQuestion.id == self.oDriveRoadPredecessor.id:
            return 'successorIs', self.oDriveRoad,  self.contactPointRoad
        if oDriveRoadQuestion.id == self.oDriveRoad.id:
            return 'predecessorIs', self.oDriveRoadPredecessor.id,  self.contactPointPredecessor

    def giveODriveString(self, oDriveRoadQuestion):
        self.evaluateLaneLinks()
        if oDriveRoadQuestion.id == self.oDriveRoadPredecessor.id or oDriveRoadQuestion.id == self.oDriveRoad.id:
            order = "successor"
            roadOrJunction = "road" if self.oDriveRoad.odriveJunction == "-1" else "junction"
            contactpoint = self.contactPointRoad
            orderID = str(self.oDriveRoad.id) if self.oDriveRoad.odriveJunction == "-1" else str(self.oDriveRoad.odriveJunction)

            if oDriveRoadQuestion.id == self.oDriveRoad.id:
                order = "predecessor"
                contactpoint = self.contactPointPredecessor
                roadOrJunction = "road" if self.oDriveRoadPredecessor.odriveJunction == "-1" else "junction"
                orderID = str(self.oDriveRoadPredecessor.id) if self.oDriveRoadPredecessor.odriveJunction == "-1" else str(self.oDriveRoadPredecessor.odriveJunction)
            if roadOrJunction == "road":
                dic =  {'string':'\t\t<{0} elementType="road" elementId="{1}" contactPoint="{2}" />'.format(order, orderID, contactpoint),
                        'contact':contactpoint,
                        'order':order,
                        'id':orderID,
                        'isJunction':roadOrJunction}
                return dic['string']
            else:
                dic =  {'string':'\t\t<{0} elementType="junction" elementId="{1}" />'.format(order, orderID),
                        'contact':contactpoint,
                        'order':order,
                        'id':orderID,
                        'isJunction':roadOrJunction}
                return dic['string']
        else: return ""
