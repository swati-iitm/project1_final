import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('./data/ticket-sales.db')
cursor = conn.cursor()

# Calculate total sales for "Gold" ticket type
cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
total_sales = cursor.fetchone()[0]

# Write total sales to a file
with open('./data/ticket-sales-gold.txt', 'w') as f:
    f.write(str(total_sales))

# Close database connection
conn.close()