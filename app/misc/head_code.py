sheet = workbook["{sheet_name}"]
rows = list(sheet.iter_rows(values_only=True))

if not rows:
    print("Sheet is empty.")
elif len(rows) == 1:
    header = rows[0]
    print("Header only, no data rows present.")
else:
    header = rows[0]
    data_rows = rows[1:{num_rows}]

    col_count = len(header)
    # Pad rows in case some rows are shorter
    padded_data = [
        tuple((row[i] if row and len(row) > i else None) for i in range(col_count))
        for row in data_rows
    ]

    # Only include columns if at least one value in the data rows (not header) is not None
    keep_col_idxs = []
    for i in range(col_count):
        col_values = [row[i] for row in padded_data]
        if any(val is not None for val in col_values):
            keep_col_idxs.append(i)

    # Limit columns
    keep_col_idxs = keep_col_idxs[:{max_columns}]

    # Print header
    print(tuple(header[i] for i in keep_col_idxs))
    # Print data rows
    for row in padded_data:
        print(tuple(row[i] for i in keep_col_idxs))