from typing import Tuple
from requests import head
import subprocess
import os
import shutil
import re
import config_reader

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


async def process(user: str, latex_expr: str) -> Tuple[str, int, int]:
    file_hash = get_hash(latex_expr)
    if not await url_is_available(http_address.format(get_hash(latex_expr))):
        user_path = os.path.join(os.getcwd(), user)

        if os.path.exists(user_path):
            shutil.rmtree(user_path)

        os.mkdir(user_path)

        await write_to_file(latex_expr, user_path)
        await create_pdf(user_path)
        jpg_path = await conver_pdf_to_jpg(user_path, file_hash)
        width, height = await get_width_and_height(user_path, file_hash)
        await copy_to_server(jpg_path, remote_path)

        shutil.rmtree(user_path)

    print("Sent" + http_address.format(file_hash), int(width), int(height))
    return http_address.format(file_hash), int(width), int(height)


async def write_to_file(latex_expr: str, user_path: str) -> None:
    print("Writing file.")
    os.chdir(user_path)
    with open("the_latex.tex", "w") as tex_output:
            tex_output.write(tex_body % latex_expr)
    os.chdir("..")


async def create_pdf(user_path) -> None:
    print("Creating pdf...", end="")
    os.chdir(user_path)
    subprocess.run(["pdflatex", "-no-shell-escape", "the_latex.tex"], stdout=subprocess.DEVNULL)
    os.chdir("..")
    print("Created.")

async def conver_pdf_to_jpg(user_path, the_hash) -> str:
    print("Converting to jpg...", end="")
    os.chdir(user_path)
    subprocess.run(["convert", "-density", "1000", "the_latex.pdf", "-flatten", "{}.jpg".format(the_hash)])
    os.chdir("..")
    print(" Converted.")
    return os.path.join(user_path, "{}.jpg".format(the_hash))


async def copy_to_server(local_path, the_remote_path) -> None:
    print("Copying to server...")
    subprocess.run(["scp", local_path, "{}@{}:{}".format(username, host, the_remote_path)])
    print("Copied.")


def get_hash(expr: str) -> str:    # TODO: make sure this function is one-to-one
    return str(hash(expr))


async def url_is_available(url: str) -> bool:
    print("Checking availability...", end="")
    resp = head(url)
    print("Got {}".format(resp.status_code))
    return True if resp.status_code < 400 else False


async def get_width_and_height(user_path, the_hash) -> Tuple[int, int]:
    print("Measuring result...", end="")
    os.chdir(user_path)
    result = subprocess.run(["identify", "-format", r"%wx%h", "{}.jpg".format(the_hash)], stdout=subprocess.PIPE)
    regex = re.match(r"(\d+)x(\d+)", result.stdout.decode())
    os.chdir("..")
    print("Got {}x{}".format(regex.group(1), regex.group(2)))
    return regex.group(1), regex.group(2)
