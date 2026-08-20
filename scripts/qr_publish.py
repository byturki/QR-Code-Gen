#!/usr/bin/env python3
"""CLI to publish one or more PDFs to kpcwebsitestorageaccount and generate QR codes.

Usage:
  python qr_publish.py list-containers
  python qr_publish.py check   <pdf> [<pdf> ...] [--container NAME] [--blob-name NAME ...] [--domain DOMAIN] [--overwrite]
  python qr_publish.py publish <pdf> [<pdf> ...] [--container NAME] [--blob-name NAME ...] [--domain DOMAIN] [--overwrite] [--no-upload-qr]

`check` validates everything (files exist, container resolves, blobs don't
already exist) without touching Azure - use it to catch mistakes before
`publish` actually uploads anything.

Multiple PDFs may be passed at once; they all go into the same container. Blob
names are used exactly as provided via --blob-name (given once per PDF, in the
same order). The caller is responsible for making blob names URL-safe (no
spaces, ASCII only); the script does not rewrite them.
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


def _resolve_shared_container(pdf_paths, explicit):
    """Resolve a single container shared by all PDFs.

    When no container is given explicitly, inference is driven by the common
    parent folder plus all filenames (the files are guaranteed to belong to the
    same department).
    """
    folder = pdf_paths[0].parent.name if pdf_paths else ""
    filename = " ".join(p.name for p in pdf_paths)
    return resolve_container(explicit, filename=filename, folder=folder)


def _blob_names_for(pdf_paths, blob_names):
    """Map each PDF to its blob name (as-is), defaulting to the filename."""
    if not blob_names:
        return [p.name for p in pdf_paths]
    return list(blob_names)


def _validate(args):
    errors = []
    warnings = []

    pdf_paths = [Path(p) for p in args.pdf]

    if args.blob_name and len(args.blob_name) != len(pdf_paths):
        errors.append(
            f"Got {len(pdf_paths)} PDF(s) but {len(args.blob_name)} --blob-name "
            "value(s). Provide --blob-name once per PDF, in the same order, or omit it."
        )

    resolution = _resolve_shared_container(pdf_paths, args.container)
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

    blob_names = _blob_names_for(pdf_paths, args.blob_name)

    files = []
    seen_blob_names = {}
    for pdf_path, blob_name in zip(pdf_paths, blob_names):
        file_errors = []

        if not pdf_path.is_file():
            file_errors.append(f"File not found: {pdf_path}")
        elif pdf_path.suffix.lower() != ".pdf":
            file_errors.append(f"Not a PDF file: {pdf_path}")

        if blob_name in seen_blob_names:
            file_errors.append(
                f"Duplicate blob name '{blob_name}' also used for "
                f"'{seen_blob_names[blob_name]}'. Blob names must be unique."
            )
        else:
            seen_blob_names[blob_name] = str(pdf_path)

        if container and not file_errors:
            if azure_blob.blob_exists(container, blob_name) and not args.overwrite:
                file_errors.append(
                    f"Blob '{blob_name}' already exists in container '{container}'. "
                    "Re-run with --overwrite to replace it, or choose a different --blob-name."
                )

        files.append({
            "pdf": str(pdf_path),
            "blob_name": blob_name,
            "errors": file_errors,
        })
        errors.extend(file_errors)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "container": container,
        "resolution": resolution,
        "files": files,
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

    container = result["container"]
    public_access = next(c["public_access"] for c in CONTAINERS if c["name"] == container)

    published = []
    for entry in result["files"]:
        pdf_path = Path(entry["pdf"]).resolve()
        blob_name = entry["blob_name"]

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

        published.append({
            "pdf": str(pdf_path),
            "pdf_blob_name": blob_name,
            "pdf_blob_url": pdf_url,
            "public_url": public_url,
            "qr_local_path": str(qr_local_path),
            "qr_blob_name": qr_blob_name if not args.no_upload_qr else None,
            "qr_blob_url": qr_url,
        })

    summary = {
        "ok": True,
        "container": container,
        "public_access": public_access,
        "warnings": result["warnings"],
        "count": len(published),
        "published": published,
    }
    print(json.dumps(summary, indent=2))


def add_common_args(p):
    p.add_argument("pdf", nargs="+", help="Path(s) to the local PDF file(s)")
    p.add_argument("--container", "--department", dest="container", default=None,
                    help="Target container name or department alias. If omitted, "
                         "it's inferred from the filename/folder name. Applies to "
                         "all PDFs (they must belong to the same department).")
    p.add_argument("--blob-name", action="append", default=None,
                    help="Override the blob name (defaults to the PDF's filename). "
                         "Pass once per PDF, in the same order. Used exactly as "
                         "given - make it URL-safe yourself (no spaces, ASCII only).")
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
