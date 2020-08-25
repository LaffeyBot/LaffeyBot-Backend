from datetime import datetime
import xlsxwriter
from data.model import PersonalRecord
import os


def make_xlsx_for_group(group_id: int):
    # Create a workbook and add a worksheet.
    records = PersonalRecord.query.filter(PersonalRecord.group_id == group_id).all()
    workbook = xlsxwriter.Workbook(os.path.join('server_app', 'temp', f'group-{group_id}-report.xlsx'))
    worksheet = workbook.add_worksheet()

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': 1})

    # Add an Excel date format.
    date_format = workbook.add_format({'num_format': 'yy/mm/dd hh:mm'})

    # Adjust the column width.
    worksheet.set_column(1, 1, 20)
    worksheet.set_column(0, 0, 20)

    # Write some data headers.
    worksheet.write('A1', '出刀时间', bold)
    worksheet.write('B1', '出刀玩家', bold)
    worksheet.write('C1', 'Boss周目', bold)
    worksheet.write('D1', 'Boss编号', bold)
    worksheet.write('E1', '伤害', bold)
    worksheet.write('F1', '分数', bold)
    worksheet.write('G1', '出刀类型', bold)

    # Start from the first cell below the headers.
    row = 1

    record: PersonalRecord
    for record in records:
        worksheet.write_datetime(row, 0, record.detail_date, date_format)
        worksheet.write_string(row, 1, record.nickname)
        worksheet.write(row, 2, record.boss_gen)
        worksheet.write(row, 3, record.boss_order)
        worksheet.write(row, 4, record.damage)
        worksheet.write(row, 5, record.score)
        worksheet.write_string(row, 6, record.type)
        row += 1

    workbook.close()