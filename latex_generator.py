from typing import Tuple
from requests import head
import os
import shutil
import re
import config_reader
import logging
import asyncio
import asyncio.subprocess

loop = None     # type: asyncio.BaseEventLoop
run_dir = ""    # type: str

async def process(user: str, latex_expr: str) -> Tuple[str, int, int]:
    file_hash = get_hash(latex_expr)
    if not await url_is_available(http_address.format(get_hash(latex_expr))):
        user_path = os.path.join(run_dir, user)
        try:
            if os.path.exists(user_path):
                shutil.rmtree(user_path)

            os.mkdir(user_path)

            await write_to_file(latex_expr, user_path)
            await create_pdf(user_path)
            jpg_path = await convert_pdf_to_jpg(user_path, file_hash)
            width, height = await get_width_and_height(user_path, file_hash)
            await copy_to_server(jpg_path, remote_path)
        except asyncio.CancelledError:
            tex_logger.info("Processing query cancelled.\n")
            raise

    tex_logger.debug("Sent (%s, %s, %s)\n" % (http_address.format(file_hash), width, height))
    return http_address.format(file_hash), int(width), int(height)


async def write_to_file(latex_expr: str, user_path: str) -> None:
    tex_logger.debug("Writing file... ")
    os.chdir(user_path)
    with await loop.run_in_executor(None, open, "the_latex.tex", "w") as tex_output:
            await loop.run_in_executor(None, tex_output.write, (tex_body % latex_expr))
    os.chdir(os.path.dirname(user_path))
    tex_logger.debug("Wrote.\n")


async def create_pdf(user_path) -> None:
    tex_logger.debug("Creating pdf... ")
    os.chdir(user_path)
    pdflatex_process = await asyncio.create_subprocess_exec(*["pdflatex", "-no-shell-escape", "the_latex.tex"],
                                                            stdout=asyncio.subprocess.DEVNULL)
    try:
        await pdflatex_process.wait()
    except asyncio.CancelledError:
        tex_logger.debug("PDF generation cancelled.")
        pdflatex_process.kill()
        raise

    os.chdir(os.path.dirname(user_path))
    tex_logger.debug("Created.\n")

async def convert_pdf_to_jpg(user_path, the_hash) -> str:
    tex_logger.debug("Converting to jpg...")
    os.chdir(user_path)

    conversion_process = await asyncio.create_subprocess_exec(*["gs", "-o", "{}.jpg".format(the_hash), "-sDEVICE=jpeg",
                                                                "-dJPEGQ=100", "-r1000", "the_latex.pdf"],
                                                              stdout=asyncio.subprocess.DEVNULL)
    try:
        await conversion_process.wait()
    except asyncio.CancelledError:
        tex_logger.debug("Conversion cancelled.\n")
        conversion_process.kill()
        raise

    os.chdir(os.path.dirname(user_path))
    tex_logger.debug(" Converted.\n")
    return os.path.join(user_path, "{}.jpg".format(the_hash))


async def copy_to_server(local_path, the_remote_path) -> None:
    tex_logger.debug("Copying to server... ")
    scp_process =\
        await asyncio.create_subprocess_exec(*["scp", local_path, "{}@{}:{}".format(username, host, the_remote_path)],
                                             stdout=asyncio.subprocess.DEVNULL)
    try:
        await scp_process.wait()
    except asyncio.CancelledError:
        tex_logger.debug("Cancelled while uplading result to server.\n")
        scp_process.kill()
        raise
    tex_logger.debug("Copied.\n")


def get_hash(expr: str) -> str:
    return str(hash(expr))


async def url_is_available(url: str) -> bool:
    tex_logger.debug("Checking availability... ")
    resp = await loop.run_in_executor(None, head, url)
    tex_logger.debug("Got {}\n".format(resp.status_code))
    return True if resp.status_code < 400 else False


async def get_width_and_height(user_path, the_hash) -> Tuple[int, int]:
    tex_logger.debug("Measuring result...")
    os.chdir(user_path)
    measurer_process = await asyncio.create_subprocess_exec(*["identify", "-format", r"%wx%h", "{}.jpg".format(the_hash)],
                                                  stdout=asyncio.subprocess.PIPE)
    try:
        stdout_bytes, stderr_byets = await measurer_process.communicate()
    except asyncio.CancelledError:
        tex_logger.debug("Cancelled while measuring dimensions\n")
        measurer_process.kill()
        return
    regex = re.match(r"(\d+)x(\d+)", stdout_bytes.decode())
    os.chdir(os.path.dirname(user_path))
    tex_logger.debug(" Got {}x{}\n".format(regex.group(1), regex.group(2)))
    return regex.group(1), regex.group(2)

tex_logger = logging.getLogger('tex_logger')

# the latex template
tex_body = r"""
\nonstopmode
\documentclass[border=1pt]{standalone}
\begin{document}
$%s$
\end{document}
"""

# parameters for setting up the server
username = config_reader.username
host = config_reader.host
remote_path = config_reader.remote_path
http_address = config_reader.http_address
