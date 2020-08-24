import re


OPERATORS = {
    "=": "$eq",
    "!": "$ne",
    ">": "$gt",
    ")": "$gte",
    "<": "$lt",
    "(": "$lte",
    "~": "$regex",
    "*": "$in",
    "@": "$exists",
}
FILTER_RE = re.compile(r"([a-zA-Z\._]+)([" + "".join(OPERATORS.keys()) + "])(.*)")


def convert_filter(filter_string, model):
    match = FILTER_RE.match(filter_string)
    if not match:
        return None
    field = match.group(1)
    oper = match.group(2)
    value = match.group(3).strip('"')
    # Do some type casting
    if oper == "@":
        # Need to typecast the value for the $exists operation
        if value[0].lower() in ["y", "t", "1"]:
            value = True
        else:
            value = False
    elif oper == "*":
        value = value.split(";")
    elif "build_number" not in field:
        # This is a horrible hack, because Jenkins build numbers are strings :-(
        if value.isdigit():
            # Try to typecast if we get a digit
            try:
                value = int(value)
            except (ValueError, TypeError):
                # Just ignore it and carry on if there's a problem
                pass
        else:
            # Lastly, try to convert to a float
            try:
                value = float(value)
            except (ValueError, TypeError):
                # Just ignore it and carry on
                pass
    field_parts = field.split(".")
    if field == "id":
        column = model.id
    else:
        column = model.data[field_parts[0]]
        for idx, part in enumerate(field_parts):
            if idx == 0:
                continue
            column = column[part]
    if oper == "=":
        return column == value
    if oper == "!":
        return column != value
    if oper == ">":
        return column > value
    if oper == "<":
        return column < value
    if oper == ")":
        return column >= value
    if oper == "(":
        return column <= value
    if oper == "*":
        return column.in_(value)
    if oper == "~":
        return column.op("~")(value)
    return None


def generate_filter_object(filter_string):
    """
    Extract an API query to a filter object
    """
    match = FILTER_RE.match(filter_string)
    if match:
        name = match.group(1)
        oper = OPERATORS[match.group(2)]
        value = match.group(3).strip('"')
        if oper == "$exists":
            # Need to typecast the value for the $exists operation
            if value[0].lower() in ["y", "t", "1"]:
                value = True
            else:
                value = False
        elif oper == "$in":
            value = value.split(";")
        elif "build_number" not in name:
            # This is a horrible hack, because Jenkins build numbers are strings :-(
            if value.isdigit():
                # Try to typecast if we get a digit
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    # Just ignore it and carry on if there's a problem
                    pass
            else:
                # Lastly, try to convert to a float
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    # Just ignore it and carry on
                    pass
        return {name: {oper: value}}
    return None
