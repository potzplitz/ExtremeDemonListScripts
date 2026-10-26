import os
import psycopg
import time
from dotenv import load_dotenv
import subprocess

load_dotenv()

def get_connection():
    #v_count = 0
    
    #while True or v_count < 5:
     #   v_count = v_count + 1
      #  try:
    conn = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    conn.execute("SET search_path TO extremedemonlist")
       # except psycopg.OperationalError:
        #    subprocess.run(["systemctl"], ["restart"], ["postgres-tunnel.service"] check=True)

         #   time.sleep(5)

    return conn

def execute_query(sql, params=(), fetch="none"):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)

            if fetch == "one":
                return cur.fetchone()

            if fetch == "all":
                return cur.fetchall()

            return cur.rowcount