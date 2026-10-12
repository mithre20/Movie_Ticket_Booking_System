#!C:\Python\python.exe
"""
CineMithresh - Movie Booking Submission CGI Handler
Compatible with Python 3.13+ and legacy Python CGI environments.
"""

import os
import sys
import urllib.parse

print("Content-Type: text/html; charset=utf-8\r\n\r\n")

# Safely extract POST data
fmovie, fseats = "", ""

try:
    content_length = int(os.environ.get('CONTENT_LENGTH', 0))
except (ValueError, TypeError):
    content_length = 0

if content_length > 0:
    post_data = sys.stdin.read(content_length)
    fields = urllib.parse.parse_qs(post_data)
    fmovie = fields.get('mymovie', [''])[0]
    fseats = fields.get('myseats', [''])[0]
else:
    query_string = os.environ.get('QUERY_STRING', '')
    fields = urllib.parse.parse_qs(query_string)
    fmovie = fields.get('mymovie', [''])[0]
    fseats = fields.get('myseats', [''])[0]

db_status = "Processed"
try:
    import mysql.connector
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="movies"
    )
    mycursor = mydb.cursor()
    sql = "INSERT into booking(Movie,Seats) VALUES(%s,%s)"
    val = (fmovie, fseats)
    mycursor.execute(sql, val)
    mydb.commit()
    db_status = "Saved to MySQL Database (movies.booking)"
except Exception as e:
    db_status = f"Database note: {e}"

# Render modern confirmation page
print(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Booking Confirmed - CineMithresh</title>
  <link rel="stylesheet" href="./styles.css">
</head>
<body style="display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px;">
  <div style="background: rgba(18, 25, 43, 0.9); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 40px; max-width: 480px; width: 100%; text-align: center; box-shadow: 0 20px 50px rgba(0,0,0,0.6);">
    <div style="font-size: 3rem; margin-bottom: 12px;">🎟️</div>
    <h2 style="font-size: 1.8rem; margin-bottom: 8px; color: #fff;">Ticket Booking Registered!</h2>
    <p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 24px;">Your reservation request has been processed.</p>
    
    <div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 18px; text-align: left; margin-bottom: 24px;">
      <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 6px;">Movie: <strong style="color: #fff;">{fmovie or 'Blockbuster Feature'}</strong></div>
      <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 6px;">Seats Reserved: <strong style="color: #e50914;">{fseats or '1'} Seat(s)</strong></div>
      <div style="font-size: 0.75rem; color: #f5c518; margin-top: 10px;">Status: {db_status}</div>
    </div>

    <div style="display: flex; gap: 10px; justify-content: center;">
      <a href="./booking.html" class="btn btn-primary">Book Another Show</a>
      <a href="./index.html" class="btn btn-secondary">Back to Home</a>
    </div>
  </div>
</body>
</html>
""")
