import uuid

def convert_to_uuid(text: str):
    namespace = uuid.NAMESPACE_DNS

    if isinstance(text, str) is not True:
        text = str(text)
    return uuid.uuid5(namespace=namespace, name=text)