import uuid
def _build_multipart_form(fields: dict[str, str]) -> tuple[bytes, str]:
    """Build a multipart/form-data payload and return (body_bytes, content_type_header)."""
    boundary = f"----AdvanceRBoundary{uuid.uuid4().hex}"
    body = bytearray()

    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{value}\r\n".encode("utf-8"))

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body), f"multipart/form-data; boundary={boundary}"