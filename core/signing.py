"""Signature support.

- stamp_image: visible signature image overlay (not cryptographic).
- sign_pkcs7: invisible PKCS#7 digital signature via pyhanko + PKCS#12 cert.
"""
import os
from pathlib import Path
import fitz


def stamp_image(
    src: Path,
    out: Path,
    image: Path,
    page: int = -1,
    x: float = 72,
    y: float = 72,
    width: float = 200,
) -> Path:
    src, out = Path(src), Path(out)
    doc = fitz.open(str(src))
    try:
        idx = page if page >= 0 else doc.page_count - 1
        pg = doc.load_page(idx)
        import PIL.Image
        with PIL.Image.open(image) as im:
            ratio = im.height / im.width
        rect = fitz.Rect(x, y, x + width, y + width * ratio)
        pg.insert_image(rect, filename=str(image))
        if src.resolve() == out.resolve():
            tmp = out.with_suffix(out.suffix + ".tmp")
            doc.save(str(tmp))
            doc.close()
            os.replace(tmp, out)
        else:
            doc.save(str(out))
            doc.close()
    except Exception:
        doc.close()
        raise
    return out


def sign_pkcs7(
    src: Path,
    out: Path,
    pfx_path: Path,
    password: str,
    reason: str | None = None,
    location: str | None = None,
    field_name: str = "Signature1",
) -> Path:
    """Apply invisible PKCS#7 digital signature using a PKCS#12 (.pfx/.p12) cert."""
    from pyhanko.sign import signers
    from pyhanko.sign.signers.pdf_signer import PdfSigner
    from pyhanko.sign.fields import SigFieldSpec
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    from pyhanko.sign import PdfSignatureMetadata

    signer = signers.SimpleSigner.load_pkcs12(
        pfx_file=str(pfx_path),
        passphrase=password.encode("utf-8") if password else None,
    )
    if signer is None:
        raise RuntimeError("Failed to load PKCS#12. Wrong password or invalid file.")

    meta = PdfSignatureMetadata(
        field_name=field_name,
        reason=reason,
        location=location,
    )
    with open(src, "rb") as inf, open(out, "wb") as outf:
        w = IncrementalPdfFileWriter(inf)
        # Ensure field exists (invisible)
        try:
            from pyhanko.sign import fields as sig_fields
            sig_fields.append_signature_field(
                w, sig_field_spec=SigFieldSpec(sig_field_name=field_name)
            )
        except Exception:
            # Field may already exist; ignore
            pass
        pdf_signer = PdfSigner(meta, signer=signer)
        pdf_signer.sign_pdf(w, output=outf)
    return out
