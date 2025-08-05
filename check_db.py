import sqlite3

DATABASE_FILE = 'proposals.db'

def check_generated_opportunities():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, scheme_name, funding_agency, last_date_submission, description, is_processed FROM generated_opportunities ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No entries found in the 'generated_opportunities' table.")
    else:
        print("Entries in 'generated_opportunities' table (most recent first):")
        print("-----------------------------------------------------------")
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"Timestamp: {row[1]}")
            print(f"Scheme Name: {row[2]}")
            print(f"Funding Agency: {row[3]}")
            print(f"Last Date Submission: {row[4]}")
            print(f"Description: {row[5][:100]}...") # Truncate description for readability
            print(f"Processed: {bool(row[6])}")
            print("-----------------------------------------------------------")

if __name__ == "__main__":
    check_generated_opportunities() 