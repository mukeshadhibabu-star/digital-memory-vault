import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="muKesh@123",
    database="digital_memory_vault"
)

print("Database Connected Successfully")