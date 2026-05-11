import sys

import models
from database import SessionLocal, engine
from parsers.excel import parse_excel_test
from test_importer import create_test_from_data


def main(path):
    models.Base.metadata.create_all(bind=engine)

    data = parse_excel_test(path)
    db = SessionLocal()
    try:
        create_test_from_data(db, data)
    finally:
        db.close()

    print(f"Тест {data['code']} импортирован из {path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python import_excel.py path/to/test.xlsx")
        raise SystemExit(1)

    main(sys.argv[1])
