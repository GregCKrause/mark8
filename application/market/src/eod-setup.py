# Standard library
import os

# Third party
import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  port=3307,
  user="root",
  password=os.getenv("MYSQL_ROOT_PASSWORD")
)

mycursor = mydb.cursor()

mycursor.execute("CREATE DATABASE IF NOT EXISTS eod;")

mycursor.execute("SHOW DATABASES")

for x in mycursor:
  print(x)
