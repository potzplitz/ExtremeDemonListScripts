from database import execute_query
from datetime import date
from psycopg.types.json import Jsonb
import requests
import time

v_SART = ''

#führe API request aus
def requestAPI(in_URL):
    resp = requests.get(in_URL)
    data = resp.json()

    return data

#SQL query
def query_SQL(in_action, in_ID, in_nameRAW, in_name = None, in_pos = None, in_diff = None, in_song = None, in_creator = None, in_verifier = None, in_tags = None, in_desc = None, in_legacy = None):
    if in_action == 1 or in_action == 2:
        v_SQL = """
                select EXISTS (
                  select 1
                    from levels
                    where sart = %s
                    and level_id = %s
                    and levelname_raw = %s
                )
                """

        #wenn action 2 dann erweitere
        if in_action == 1:
            result = execute_query(v_SQL, (v_SART, in_ID, in_nameRAW), fetch="one")
        else:
            v_SQL = v_SQL.replace(')', '')
            v_SQL += """
                     \n
                     and position = %s
                     and difficulty = %s
                     and song = %s
                     and description = %s
                     and legacy = %s
                     )
                    """

            result = execute_query(v_SQL, (v_SART, in_ID, in_nameRAW, in_pos, in_diff, in_song, in_desc, in_legacy), fetch="one")

        #gebe ergebnis zurück
        return result

    #update
    elif in_action == 3:
        execute_query(
            """
            update levels
                set position = %s,
                    difficulty = %s,
                    song = %s,
                    description = %s,
                    legacy = %s,
                    last_updated = %s
              where sart = %s
                and level_id = %s
                and levelname_raw = %s
            """,
            (in_pos, in_diff, in_song, in_desc, in_legacy, date.today(), v_SART, in_ID, in_nameRAW)
        )

    #insert
    elif in_action == 4:
        execute_query(
            """
            insert into levels (sart, level_id, levelname, levelname_raw, creator, verifier, position, song, tags, description, last_updated, legacy, difficulty)
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '0', %s)
            """,
            (v_SART, in_ID, in_name, in_nameRAW, in_creator, in_verifier, in_pos, in_song, in_tags, in_desc, date.today(), in_diff)
        )

#hole AREDL Daten
def get_LevelAREDL():
    global v_SART
    v_SART = 'AREDL'
    
    url ="https://api.aredl.net/v2/api/aredl/levels"

    for row in requestAPI(url):
        j_name    = row["name"].strip()
        j_pos     = row["position"]
        j_status  = row["status"]
        j_levelid = row["level_id"]
        j_tags    = row["tags"]
        j_desc    = row["description"]
        j_song    = row["song"]
        j_nameRaw = j_name.lower().replace(" ", "_").replace("(", "").replace(")", "")

        #setze Status
        if j_status == "Legacy":
            v_legacy = 1
        else:
            v_legacy = 0

        #wenn Song leer dann hole von Robtop
        if j_song is None:
            lvlDetail = requestAPI(f"https://dev.potzplitz.de/api/gdwrapper/levels/{j_levelid}")
            j_song = lvlDetail["song_id"]

            time.sleep(0.5)

        #diff immer Extreme
        v_diff = 'EX'
        
        #prüfe ob lvl bereits vorhanden
        exist = query_SQL(in_action=1, in_ID=j_levelid, in_nameRAW=j_nameRaw)
        
        #wenn lvl existiert dann prüfe auf update
        if exist[0]:
            upd = query_SQL(in_action=2, in_ID=j_levelid, in_nameRAW=j_nameRaw, in_pos=j_pos, in_diff=v_diff, in_song=j_song, in_desc=j_desc, in_legacy=v_legacy)
            
            #wenn daten veraltet dann update
            if not upd[0]:
                query_SQL(in_action=3, in_ID=j_levelid, in_nameRAW=j_nameRaw, in_pos=j_pos, in_diff=v_diff, in_song=j_song, in_desc=j_desc, in_legacy=v_legacy)
        
        else:
            #nur wenn lvl NICHT legacy
            if v_legacy == 0:
                #hole Creator / Veriefier
                detail = requestAPI(f"https://api.aredl.net/v2/api/aredl/levels/{j_levelid}")

                #hole Creator
                try:
                    j_creator  = detail["publisher"]["global_name"]
                    if not j_creator:
                        j_creator = 'ERROR_EMPTY'
                except Exception:
                    j_creator = 'ERROR_DATA'
                
                #hole Verifier
                try:
                    j_verifier = detail["verifications"][0]["submitted_by"]["global_name"]
                    if not j_verifier:
                        j_verifier = 'ERROR_EMPTY'
                except Exception:
                    j_verifier = 'ERROR_DATA'

                #inserte neuen lvl
                query_SQL(in_action=4, in_ID=j_levelid, in_name=j_name, in_nameRAW=j_nameRaw, in_creator=j_creator, in_verifier=j_verifier, in_pos=j_pos, in_song=j_song, in_tags=Jsonb(j_tags), in_desc=j_desc, in_diff=v_diff)

        #warte eine halbe sekunde vor nächstem durchlauf
        time.sleep(0.5)

#hole NCL Daten
def get_LevelNCL():
    global v_SART
    v_SART = 'NCL'
    
    url = "https://api.ninecirclesdemonlist.com/list"

    for row in requestAPI(url):
        j_name     = row["name"].strip()
        j_levelid  = row["level_id"]
        j_pos      = row["position"]
        j_diff     = row["difficulty"]
        j_creator  = row["creator"]
        j_verifier = row["verifier"]
        j_gversion = row["game_version"]
        j_desc     = row["description"]
        j_nameRaw  = j_name.lower().replace(" ", "_").replace("(", "").replace(")", "")

        #decode difficulty
        match j_diff:
            case 11:
                v_diff = 'EX'
            case 10:
                v_diff = 'IN'
            case 9:
                v_diff = 'HA'
            case 8:
                v_diff = 'ME'
            case 7:
                v_diff = 'EA'
            case _:
                v_diff = 'NA'

        #mache game version zu einer Liste
        l_gversion = [j_gversion]

        #hole SongID
        lvlDetail = requestAPI(f"https://dev.potzplitz.de/api/gdwrapper/levels/{j_levelid}")
        j_song = lvlDetail["song_id"]

        #prüfe ob lvl vorhanden
        exists = query_SQL(in_action=1, in_ID=j_levelid, in_nameRAW=j_nameRaw)

        #prüfe auf änderungen
        if exists[0]:
            upd = query_SQL(in_action=2, in_ID=j_levelid, in_nameRAW=j_nameRaw, in_pos=j_pos, in_diff=v_diff, in_song=j_song, in_desc=j_desc, in_legacy=0)

            #update
            if not upd[0]:
                query_SQL(in_action=3, in_ID=j_levelid, in_nameRAW=j_nameRaw, in_pos=j_pos, in_diff=v_diff, in_song=j_song, in_desc=j_desc, in_legacy=0)

        #insert
        else:
            query_SQL(in_action=4, in_ID=j_levelid, in_name=j_name, in_nameRAW=j_nameRaw, in_creator=j_creator, in_verifier=j_verifier, in_pos=j_pos, in_song=j_song, in_tags=l_gversion, in_desc=j_desc, in_diff=v_diff)

        #pause
        time.sleep(0.5)


def main():
    get_LevelAREDL()
    #get_LevelNCL()

if __name__ == "__main__":
    main()