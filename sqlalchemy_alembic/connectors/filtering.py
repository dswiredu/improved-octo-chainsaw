def build_filters(filters: dict) -> tuple[list[str], dict]:
    """
    Build SQL WHERE clauses and parameters from a flexible filter dict.

    Supported filter formats:
    - "col": value                        → col = :col
    - "col": ("date", value)             → DATE(col) = :col_date
    - "col": ("range", start, end)       → col BETWEEN :col_start AND :col_end
    - "col": (">", value)                → col > :col
    - "col": ("<=", value)               → col <= :col
    - "col": ("in", [val1, val2])        → col IN :col_list
    - "col": ("like", pattern)           → col LIKE :col_like
    - "col": ("null", True/False)        → col IS NULL / IS NOT NULL

    Returns:
    - clauses: list of string fragments
    - params: dict of parameters to bind
    """
    clauses = []
    params = {}

    for col, val in filters.items():
        if isinstance(val, tuple):
            op = val[0]

            if op == "date":
                clauses.append(f"DATE({col}) = :{col}_date")
                params[f"{col}_date"] = val[1]

            elif op == "range":
                clauses.append(f"{col} BETWEEN :{col}_start AND :{col}_end")
                params[f"{col}_start"] = val[1]
                params[f"{col}_end"] = val[2]

            elif op in {">", "<", ">=", "<=", "!="}:
                clauses.append(f"{col} {op} :{col}")
                params[col] = val[1]

            elif op == "in":
                clauses.append(f"{col} IN :{col}_list")
                # MySQL requires tuple, not list
                params[f"{col}_list"] = tuple(val[1])

            elif op == "like":
                clauses.append(f"{col} LIKE :{col}_like")
                params[f"{col}_like"] = val[1]

            elif op == "null":
                if val[1] is True:
                    clauses.append(f"{col} IS NULL")
                else:
                    clauses.append(f"{col} IS NOT NULL")

            else:
                raise ValueError(f"Unsupported filter operator: {op}")

        else:
            clauses.append(f"{col} = :{col}")
            params[col] = val

    return clauses, params
