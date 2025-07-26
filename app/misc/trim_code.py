def trim_sheet(ws):
    max_data_row = 0
    max_data_col = 0

    # Scan all cells to find the maximum row/column that contains data
    for row in ws.iter_rows():
        for cell in row:
            if cell.value not in (None, ""):
                if cell.row > max_data_row:
                    max_data_row = cell.row
                if cell.column > max_data_col:
                    max_data_col = cell.column

    # If the sheet is entirely empty, nothing to trim
    if max_data_row == 0 or max_data_col == 0:
        return

    # Delete rows below max_data_row
    # Note: delete from the bottom up to avoid reindexing issues
    for row_idx in range(ws.max_row, max_data_row, -1):
        ws.delete_rows(row_idx)

    # Delete columns to the right of max_data_col
    for col_idx in range(ws.max_column, max_data_col, -1):
        ws.delete_cols(col_idx)

for ws in workbook.worksheets:
    trim_sheet(ws)