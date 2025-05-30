from System.Reflection import BindingFlags


def get_class_field_data(cls, field_name: str):
    """Generic access to any private/protected field from a .NET object."""
    field = cls.GetType().GetField(
        field_name, BindingFlags.Instance | BindingFlags.NonPublic
    )
    if field is None:
        raise AttributeError(f"{field_name} not found on object.")
    return field.GetValue(cls)
