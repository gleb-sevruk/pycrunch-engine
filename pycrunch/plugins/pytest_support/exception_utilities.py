from collections import OrderedDict

MAXIMUM_BYTES_TO_REPR = 1024


def get_originating_frame_and_location(tb):
    """
    Get the most recent stack frame, filename, and line number where the exception originated.

    :param tb: The traceback object from the exception.
    :type tb: traceback
    :return: A tuple containing the most recent stack frame, filename, and line number.
    :rtype: Tuple[frame, str, int]
    """
    frame = None
    filename = None
    line_number = None
    frames = []
    while tb is not None:
        frame = tb.tb_frame
        frames.append(frame)
        filename = tb.tb_frame.f_code.co_filename
        line_number = tb.tb_lineno
        tb = tb.tb_next

    return frame, filename, line_number, frames


def stringify_locals(frame):
    frame_locals = frame.f_locals
    stringified_locals = OrderedDict()
    for key, value in frame_locals.items():
        try:
            stringified_value = custom_repr(value)
        except Exception:
            stringified_value = "<unrepresentable>"
        stringified_locals[key] = stringified_value

    return stringified_locals


def custom_repr_list(value, depth):
    return [custom_repr(item, depth=depth - 1) for item in value]


def custom_repr_dict(value, depth):
    stringified_value = OrderedDict()
    keys = value.keys()
    for k in keys:
        v = value[k]
        stringified_value[str(k)] = custom_repr(v, depth=depth - 1)
    return stringified_value


def limited_repr(obj):
    representation = repr(obj)
    if len(representation) > MAXIMUM_BYTES_TO_REPR:
        remaining_bytes = len(representation) - MAXIMUM_BYTES_TO_REPR
        return (
            representation[:MAXIMUM_BYTES_TO_REPR]
            + f'... ({remaining_bytes} more bytes not recorded)'
        )
    return representation


def custom_repr(obj, depth=2):
    if depth == 0:
        return limited_repr(obj)

    try:
        classname = obj.__class__.__name__

        if isinstance(obj, list):
            return custom_repr_list(obj, depth)

        if isinstance(obj, dict):
            stringified_attributes = OrderedDict()
            keys = list(obj.keys())
            for key in keys:
                value = obj[key]
                # if not is_serializable(value):
                #     stringified_value = "<non-serializable>"
                # else:
                stringified_value = custom_repr(value, depth=depth - 1)
                stringified_attributes[str(key)] = stringified_value
            return {"object": classname, "props": stringified_attributes}

        # this line will fail for primitives,
        #   and interpreter will fallback into exception block
        attributes = vars(obj)
        attributes = OrderedDict()
        object_attributes = sorted(dir(obj))
        for key in object_attributes:
            if not key.startswith('__'):
                try:
                    attr = getattr(obj, key)
                    if not callable(attr):
                        attributes[key] = attr
                except Exception:
                    # We just skip this pseudo_variable
                    # print(f'  ungettable key = {key}')
                    pass

        stringified_attributes = OrderedDict()
        keys = list(attributes.keys())
        for key in keys:
            value = attributes[key]
            try:
                if isinstance(value, (list, tuple)):
                    stringified_value = custom_repr_list(value, depth)
                elif isinstance(value, dict):
                    stringified_value = custom_repr_dict(value, depth)
                else:
                    stringified_value = custom_repr(value, depth=depth - 1)
            except Exception:
                stringified_value = limited_repr(value)

            stringified_attributes[str(key)] = stringified_value

        return {"object": classname, "props": stringified_attributes}
    except Exception:
        return limited_repr(obj)
