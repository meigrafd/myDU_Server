#! /usr/bin/env python3
'''
    python3 -m pip install vec3 psycopg2
    
    you need to add "ports" for postgres in docker-compose.yml to access it outside docker.
        ports:
          - 127.0.0.1:5432:5432
    
    based on https://discord.com/channels/184691218184273920/1275058488757846139/1281985434536247427
    ported to python3 by meigrafd
'''
import sys
import os
import math
import pytz
import random
import psycopg2
from decimal import Decimal
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from vec3 import Vec3, dist as vec3_dist


targetPosition = Vec3(12329354.3114, 10221338.3959, -32152019.1165)
maxDeviation = 25637659
minDeviation = 10000
minDistance = 10000
planetId = 5
daysAgo = 3
DSN = 'host=localhost port=5432 dbname=dual user=dual password=dual'


def generateNewPosition(target, maxDev, minDev):
    return Vec3(
        target.x + random.uniform(minDev, maxDev) * random.random(),
        target.y + random.uniform(minDev, maxDev) * random.random(),
        target.z + random.uniform(minDev, maxDev) * random.random()
    )


def calculateDistance(pos1, pos2):
    return vec3_dist(pos1, pos2)


def createDUpos(sol, id, x, y, z):
    #pos = "{0},{1},{2},{3},{4}".format(sol, id,  round(Decimal(x), 0),  round(Decimal(y), 0),  round(Decimal(z), 0))
    pos = "{0},{1},{2},{3},{4}".format(sol, id, x, y, z)
    return "::pos{%s}"%pos


def changePlanetPosition():
    with psycopg2.connect(DSN) as dbcon:
        with dbcon.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT position_x,position_y,position_z,name,moved_at FROM construct WHERE id={};".format(planetId))
            currentPlanet = cur.fetchone()
            if currentPlanet == None:
                print("ERROR: Unknown planet ID {}".format(planetId))
                return
            print("Current position of planet '{0}' with ID {1} => {2}".format(currentPlanet["name"], planetId, createDUpos(0, 0, currentPlanet["position_x"], currentPlanet["position_y"], currentPlanet["position_z"])))
            
            n_days_ago = datetime.now().replace(tzinfo=pytz.UTC) - timedelta(days=daysAgo)
            if currentPlanet["moved_at"] is None:
                currentPlanet_moved_at = n_days_ago
            else:
                currentPlanet_moved_at = currentPlanet["moved_at"].replace(tzinfo=pytz.UTC)
            
            if (currentPlanet_moved_at > n_days_ago):
                print("Planet '{0}' with ID {1} was already moved in the last {2} days".format(currentPlanet["name"], planetId, daysAgo))
                return
            
            currentPosition = Vec3(currentPlanet["position_x"], currentPlanet["position_y"], currentPlanet["position_z"])
            newPosition = generateNewPosition(targetPosition, maxDeviation, minDeviation)
            while calculateDistance(currentPosition, newPosition) < minDistance:
                newPosition = generateNewPosition(targetPosition, maxDeviation, minDeviation)
            
            try:
                updateQuery = "UPDATE construct SET position_x = {0}, position_y = {1}, position_z = {2}, moved_at = NOW() WHERE id = {3};".format(newPosition.x, newPosition.y, newPosition.z, planetId)
                cur.execute(updateQuery)
                dbcon.commit()
                print("Planet '{0}' with ID {1} updated to new position => {2}".format(currentPlanet["name"], planetId, createDUpos(0, 0, newPosition.x, newPosition.y, newPosition.z)))
            except psycopg2.Error as e:
                print('ERROR: {}'.format(e))
            except psycopg2.OperationalError as e:
                print('ERROR: {}'.format(e))


if __name__ == '__main__':
    changePlanetPosition()
