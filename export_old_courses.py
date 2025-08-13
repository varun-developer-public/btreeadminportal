import json
import sqlite3

def export_data():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Export courses
    cursor.execute("SELECT id, code, name, category_id FROM studentsdb_course")
    courses = cursor.fetchall()
    course_data = [{'id': r[0], 'code': r[1], 'name': r[2], 'category_id': r[3]} for r in courses]

    # Export categories
    cursor.execute("SELECT id, name FROM studentsdb_coursecategory")
    categories = cursor.fetchall()
    category_data = [{'id': r[0], 'name': r[1]} for r in categories]

    conn.close()

    with open('old_course_data.json', 'w') as f:
        json.dump({'courses': course_data, 'categories': category_data}, f, indent=4)

    print("Successfully exported old course data to old_course_data.json")

if __name__ == '__main__':
    export_data()