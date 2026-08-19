#!/usr/bin/env python3
"""CLI to publish a PDF to kpcwebsitestorageaccount and generate its QR code.

Usage:
  python qr_publish.py list-containers
  python qr_publish.py check   <pdf> [--container NAME] [--blob-name NAME] [--domain DOMAIN] [--overwrite]
  python qr_publish.py publish <pdf> [--container NAME] [--blob-name NAME] [--domain DOMAIN] [--overwrite] [--no-upload-qr]

`check` validates everything (file exists, container resolves, blob doesn't
already exist) without touching Azure - use it to catch mistakes before
`publish` actually uploads anything.
"""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote

import qrcode

import azure_blob
from containers import CONTAINERS, CONTAINER_NAMES
from resolve import resolve_container

DEFAULT_DOMAIN = "cdn.kpc.com.kw"


def _validate(args):
    errors = []
    warnings = []

    pdf_path = Path(args.pdf)
    if not pdf_path.is_file():
        errors.append(f"File not found: {pdf_path}")
    elif pdf_path.suffix.lower() != ".pdf":
        errors.append(f"Not a PDF file: {pdf_path}")

    resolution = resolve_container(args.container, filename=pdf_path.name,
                                    folder=pdf_path.parent.name)
    container = resolution["resolved"]
    if not container:
        errors.append(
            "Could not confidently resolve a container/department. "
            f"Top candidates: {resolution['candidates']}. "
            f"Valid containers: {CONTAINER_NAMES}"
        )
    else:
        access = next(c["public_access"] for c in CONTAINERS if c["name"] == container)
        if access is None:
            warnings.append(
                f"Container '{container}' is private (no anonymous access). "
                "A QR code pointing at it will NOT be publicly accessible."
            )

    blob_name = args.blob_name or pdf_path.name
    if container and not errors:
        if azure_blob.blob_exists(container, blob_name) and not args.overwrite:
            errors.append(
                f"Blob '{blob_name}' already exists in container '{container}'. "
                "Re-run with --overwrite to replace it, or choose a different --blob-name."
            )

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "container": container,
        "resolution": resolution,
    }


def cmd_list_containers(args):
    print(json.dumps(CONTAINERS, indent=2))


def cmd_check(args):
    result = _validate(args)
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if result["ok"] else 1)


def cmd_publish(args):
    result = _validate(args)
    if not result["ok"]:
        print(json.dumps(result, indent=2, default=str))
        sys.exit(1)

    pdf_path = Path(args.pdf).resolve()
    container = result["container"]
    blob_name = args.blob_name or pdf_path.name

    pdf_url = azure_blob.upload_file(container, str(pdf_path), blob_name,
                                      "application/pdf", overwrite=args.overwrite)
    public_url = f"https://{args.domain}/{container}/{quote(blob_name)}"

    qr_img = qrcode.make(public_url)
    qr_local_path = pdf_path.with_name(f"{pdf_path.stem}_qr.png")
    qr_img.save(qr_local_path)

    qr_blob_name = f"qrcodes/{pdf_path.stem}_qr.png"
    qr_url = None
    if not args.no_upload_qr:
        qr_url = azure_blob.upload_file(container, str(qr_local_path), qr_blob_name,
                                         "image/png", overwrite=True)

    summary = {
        "ok": True,
        "container": container,
        "public_access": next(c["public_access"] for c in CONTAINERS if c["name"] == container),
        "warnings": result["warnings"],
        "pdf_blob_name": blob_name,
        "pdf_blob_url": pdf_url,
        "public_url": public_url,
        "qr_local_path": str(qr_local_path),
        "qr_blob_name": qr_blob_name if not args.no_upload_qr else None,
        "qr_blob_url": qr_url,
    }
    print(json.dumps(summary, indent=2))


def add_common_args(p):
    p.add_argument("pdf", help="Path to the local PDF file")
    p.add_argument("--container", "--department", dest="container", default=None,
                    help="Target container name or department alias. If omitted, "
                         "it's inferred from the filename/folder name.")
    p.add_argument("--blob-name", default=None,
                    help="Override the blob name (defaults to the PDF's filename)")
    p.add_argument("--domain", default=DEFAULT_DOMAIN,
                    help=f"Public custom domain used to build the QR URL (default: {DEFAULT_DOMAIN})")
    p.add_argument("--overwrite", action="store_true", help="Allow overwriting an existing blob")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Publish a PDF to Azure Blob Storage and generate its QR code.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list-containers", help="List known departments/containers")
    p_list.set_defaults(func=cmd_list_containers)

    p_check = sub.add_parser("check", help="Validate inputs WITHOUT uploading anything")
    add_common_args(p_check)
    p_check.set_defaults(func=cmd_check)

    p_publish = sub.add_parser("publish", help="Upload the PDF and generate/upload its QR code")
    add_common_args(p_publish)
    p_publish.add_argument("--no-upload-qr", action="store_true",
                            help="Skip uploading the QR PNG to Azure (still saved locally)")
    p_publish.set_defaults(func=cmd_publish)

    return parser


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
