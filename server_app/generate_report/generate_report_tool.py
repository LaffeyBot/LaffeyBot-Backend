from datetime import datetime
import xlsxwriter
from data.model import PersonalRecord


def make_xlsx_for_group(group_id: int):
    # Create a workbook and add a worksheet.
    records = PersonalRecord.query.filter(PersonalRecord.group_id == group_id).all()
    workbook = xlsxwriter.Workbook(f'temp/group-{group_id}-report.xlsx')
    worksheet = workbook.add_worksheet()

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': 1})

    # Add an Excel date format.
    date_format = workbook.add_format({'num_format': 'yy/mm/dd hh:mm'})

    # Adjust the column width.
    worksheet.set_column(1, 1, 15)

    # Write some data headers.
    worksheet.write('A1', 'Item', bold)
    worksheet.write('B1', 'Date', bold)
    worksheet.write('C1', 'Cost', bold)

    # Start from the first cell below the headers.
    row = 1

    record: PersonalRecord
    for record in records:
        worksheet.write_datetime(row, 0, record.detail_date, date_format)
        worksheet.write_string(row, 1, record.nickname)
        worksheet.write_string(row, 2, record.boss_gen)
        worksheet.write_string(row, 3, record.boss_order)
        worksheet.write_string(row, 4, record.damage)
        worksheet.write_string(row, 5, record.score)
        worksheet.write_string(row, 6, record.type)
        row += 1

    workbook.close()