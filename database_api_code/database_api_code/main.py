from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
from datetime import datetime,  date
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection settings
DB_HOST = "localhost"
DB_NAME = "dtcc_db"
DB_USER = "postgres"
DB_PASSWORD = "admin"

# Create a connection to the PostgreSQL database
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")


# Pydantic model for the request body to update the Corporate_Actions table
class UpdateCorporateActionRequest(BaseModel):
    id: int
    Extracted_Information: str

# Pydantic model for the request body to insert new values
class InsertCorporateActionRequest(BaseModel):
    Company: str
    Corporate_Action: str
    Date_Announcement: Optional[str]
    Source: str
    Extracted_Information: str
    Insertion_Date_Time: Optional[str]
    Modified_Date_Time: Optional[str]


# Route to update the `Extracted_Information` and log the changes in `Action_History`
@app.put("/update-corporate-action/")
def update_corporate_action(request: UpdateCorporateActionRequest):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Fetch the current Extracted_Information
        cursor.execute(
            "SELECT Extracted_Information FROM Corporate_Actions WHERE id = %s",
            (request.id,)
        )
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Record not found")

        logging.info(result)

        extracted_info_before = result['extracted_information']

        # Update the Corporate_Actions table
        cursor.execute(
            """
            UPDATE Corporate_Actions
            SET Extracted_Information = %s, Status = 'Verified', Modified_Date_Time = %s
            WHERE id = %s
            """,
            (
                request.Extracted_Information,
                datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                request.id
            )
        )

        # Insert into Action_History table
        cursor.execute(
            """
            INSERT INTO Action_History(id, Extracted_Information_Before, Extracted_Information_After, Modified_Date_Time)
            VALUES (%s, %s, %s, %s)
            """,
            (
                request.id,
                extracted_info_before,
                request.Extracted_Information,
                datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            )
        )
        logging.info(result)
        conn.commit()
        return {"message": "Record updated and history logged successfully"}

    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    finally:
        cursor.close()
        conn.close()


# Route to insert new values with status set to "Not Verified"
@app.post("/insert-corporate-action/")
def insert_corporate_action(request: InsertCorporateActionRequest):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            """
            INSERT INTO Corporate_Actions (Company, Corporate_Action, Date_Announcement, Source, Extracted_Information, Status, Insertion_Date_Time, Modified_Date_Time)
            VALUES (%s, %s, %s, %s, %s, 'Not Verified', %s, %s)
            """,
            (
                request.Company,
                request.Corporate_Action,
                request.Date_Announcement,
                request.Source,
                request.Extracted_Information,
                request.Insertion_Date_Time,
                request.Modified_Date_Time
            )
        )
        conn.commit()
        return {"message": "New record inserted with status 'Not Verified'"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    finally:
        cursor.close()
        conn.close()


# Route to select records where Insertion_Date_Time is equal to today
@app.get("/get-records-today/")
def get_records_today():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    today = date.today()
    try:
        cursor.execute(
            """
            SELECT * FROM Corporate_Actions
            WHERE DATE(Insertion_Date_Time) = %s
            """,
            (today,)
        )
        records = cursor.fetchall()

        if not records:
            raise HTTPException(status_code=404, detail="No records found for today")

        return records

    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error")

    finally:
        cursor.close()
        conn.close()


# Route to select records where Insertion_Date_Time is less than today
@app.get("/get-records-before-today/")
def get_records_before_today():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    today = date.today()
    try:
        cursor.execute(
            """
            SELECT * FROM Corporate_Actions
            WHERE DATE(Insertion_Date_Time) < %s
            """,
            (today,)
        )
        records = cursor.fetchall()

        if not records:
            raise HTTPException(status_code=404, detail="No records found before today")

        return records

    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error")

    finally:
        cursor.close()
        conn.close()

# Pydantic model for the request body
class InsertSchedulerLogRequest(BaseModel):
    Scheduler_Name: str
    Source: str
    Date_Time_Scheduler_Ran: str
    Total_Records_Fetched: int
    Time_Taken: int
    Status: str

# Route to insert new values into Scheduler_Logs
@app.post("/insert-scheduler-log/")
def insert_scheduler_log(request: InsertSchedulerLogRequest):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            """
            INSERT INTO Scheduler_Logs (Scheduler_Name, Source, Date_Time_Scheduler_Ran, Total_Records_Fetched, Time_Taken, Status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                request.Scheduler_Name,
                request.Source,
                request.Date_Time_Scheduler_Ran,
                request.Total_Records_Fetched,
                request.Time_Taken,
                request.Status
            )
        )
        conn.commit()
        return {"message": "New record inserted successfully"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    finally:
        cursor.close()
        conn.close()

# Route to select all records from Scheduler_Logs
@app.get("/get-scheduler-logs/")
def get_scheduler_logs():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM Scheduler_Logs")
        records = cursor.fetchall()

        if not records:
            raise HTTPException(status_code=404, detail="No records found")

        return records

    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error")

    finally:
        cursor.close()
        conn.close()



# Route to select all records from Action_History
@app.get("/get-action-history/")
def get_action_history():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM Action_History")
        records = cursor.fetchall()

        if not records:
            raise HTTPException(status_code=404, detail="No records found")

        return records

    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error")

    finally:
        cursor.close()
        conn.close()
# Run the app using uvicorn
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
