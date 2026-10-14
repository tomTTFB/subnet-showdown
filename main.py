import asyncssh
import os
import asyncio
import pyfiglet
import logging
import ipaddress
import random

logging.basicConfig(level=logging.DEBUG)
HOST_KEY_FILE = "ssh_host_key"

def load_key():
    if not os.path.exists(HOST_KEY_FILE):
        key = asyncssh.generate_private_key("ssh-ed25519")
        key.write_private_key("ssh_host_key")
        os.chmod(HOST_KEY_FILE, 0o600)
        print("ERROR: Host key not found, made new host key")
    return HOST_KEY_FILE

def toggle_cursor(toggle, process):
    if toggle == False:
        process.stdout.write("\x1b[?25l")
    elif toggle == True:
        process.stdout.write("\x1b[?25h")

def draw_text(process, row, col, text, fg=37, bg="", centerx=False):

    width, height, pixel_width, pixel_height = process.get_terminal_size()

    x = (width - len(text)) // 2 + 1

    if centerx == True:
        col = x

    bgcolour = ""
    if bg != "":
        bgcolour = ";" + str(bg)

    process.stdout.write(
        f"\x1b[{row};{col}H\x1b[{fg}{bgcolour}m{text}\x1b[0m"
    )

def draw_figlet_text(process, row, text, fg=37, bg=""):
    banner = pyfiglet.figlet_format(text, font = "slant" )
    lines = banner.splitlines()

    banner_width = max(len(line) for line in lines)
    width = process.get_terminal_size()[0]

    x = max(1, (width - banner_width) // 2 + 1)
    
    for i, line in enumerate(lines):
        draw_text(process, row + i, x, line, fg, bg)

# ──────────────────
def draw_line(process, row, fg=37, bg=""):
    width, height, pixel_width, pixel_height = process.get_terminal_size()
    text = "─" * width
    bgcolour = ""
    if bg != "":
        bgcolour = ";" + str(bg)
    process.stdout.write(
            f"\x1b[{row};1H\x1b[{fg}{bgcolour}m{text}\x1b[0m"
        )

def draw_box(process, row, col, width, height, fg=37, bg="", text=""):
    bgcolour = ""
    if bg != "":
        bgcolour = ";" + str(bg)

    # draw top left corner
    process.stdout.write(f"\x1b[{row};{col}H\x1b[{fg}{bgcolour}m┌\x1b[0m")

    for i in range(0, width):
        process.stdout.write(f"\x1b[{row};{(col + 1) + i}H\x1b[{fg}{bgcolour}m─\x1b[0m")

    # draw top right corner
    process.stdout.write(f"\x1b[{row};{col + width + 1}H\x1b[{fg}{bgcolour}m┐\x1b[0m")

    for i in range(0, height):
        process.stdout.write(f"\x1b[{(row + 1) + i};{col + width + 1}H\x1b[{fg}{bgcolour}m│\x1b[0m")

    # draw bottom right corner
    process.stdout.write(f"\x1b[{row + height + 1};{col + width + 1}H\x1b[{fg}{bgcolour}m┘\x1b[0m")

    for i in range(0, width):
        process.stdout.write(f"\x1b[{row + height + 1};{(col + 1) + i}H\x1b[{fg}{bgcolour}m─\x1b[0m")

    # draw bottom left corner
    process.stdout.write(f"\x1b[{row + height + 1};{col}H\x1b[{fg}{bgcolour}m└\x1b[0m")

    for i in range(0, height):
        process.stdout.write(f"\x1b[{(row + 1) + i};{col}H\x1b[{fg}{bgcolour}m│\x1b[0m")

    if text != "":
        process.stdout.write(f"\x1b[{row};{col + 2}H\x1b[{fg}{bgcolour}m{text}\x1b[0m")

# ──────────────────
async def draw_scrolling_line(process, row, fg=37, bg=""):
    width, height, pixel_width, pixel_height = process.get_terminal_size()
    text = "─"
    bgcolour = ""
    if bg != "":
        bgcolour = ";" + str(bg)

    col = 0

    while col < width - 1:
        col = col + 1
        process.stdout.write(f"\x1b[{row};{col}H\x1b[{fg}{bgcolour}m \x1b[0m")
        process.stdout.write(f"\x1b[{row};{col+1}H\x1b[{fg}{bgcolour}m─\x1b[0m")
        await asyncio.sleep(0.02)

        if col >= width -1:
            col = 0
            process.stdout.write(f"\x1b[{row};{width}H\x1b[{fg}{bgcolour}m \x1b[0m")

    

def clear_screen(process):
    process.stdout.write("\x1b[2J\x1b[H")

async def get_special_key(key, process):
    if key in ("\r", "\n"):
        key = "ENTER"
    elif key in ("\x7f", "\b"):
        key = "BACKSPACE"
    
    if key == "\x1b":
        try:
            second = await asyncio.wait_for(
                process.stdin.read(1),
                timeout=0.1
            )
        except asyncio.TimeoutError:
            key = "ESC"
            second = None
    
        if second == "[":
            third = await process.stdin.read(1)

            arrow_keys = {
                "A": "UP",
                "B": "DOWN",
                "C": "RIGHT",
                "D": "LEFT"
            }

            key = arrow_keys.get(third, "UNKNOWN")

    print(key)
    return(key)







# gap to make this one easier to find

async def handle_client(process):

    question_types = ["network", "broadcast"]
    # , "hosts", "mask"

    question_type = random.choice(question_types)

    ip = ".".join(str(random.randint(0, 255)) for _ in range(4))
    prefix = random.randint(24, 30)

    network = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)

    if question_type == "network":
        answer = str(network.network_address)

    elif question_type == "broadcast":
        answer = str(network.broadcast_address)

    print(f"Question Type: {question_type}")
    print(f"IP: {ip}/{prefix}")
    print(f"Answer: {answer}")

    toggle_cursor(False, process)

    state = "MENU"
 
    clear_screen(process)

    draw_figlet_text(process, 5, "Subnet", 32, "")
    draw_figlet_text(process, 10, "Showdown", 32, "")

    draw_text(process, 17, 10, "A Secure SHell Networking Quiz Game.", 37, "", True)

    options = [" Solo Mode ", "Multiplayer", "How to Play"]
    selected_option = 0

    draw_line(process, 20, 32, "")

    draw_text(process, 25, 10, "Solo Mode", 30, 107, True)
    draw_text(process, 26, 10, "Multiplayer", 37, "", True)
    draw_text(process, 27, 10, "How To Play", 37, "", True)

    draw_box(process, 23, 73, 15, 5, fg=37, bg="", text="Main Menu")

    animation_task = asyncio.create_task(draw_scrolling_line(process, 19))

    while True:
        try:
            key = await process.stdin.read(1)
        except asyncssh.TerminalSizeChanged:
            continue
        if not key or key == "q":
            clear_screen(process)
            break

        key = await get_special_key(key, process)

        if key == "DOWN" and state == "MENU":
            selected_option = (selected_option + 1) % len(options)
        elif key == "UP" and state == "MENU":
            selected_option = (selected_option - 1) % len(options)

        if selected_option == 0:
            draw_text(process, 25, 10, "Solo Mode", 30, 107, True)
            draw_text(process, 26, 10, "Multiplayer", 37, "", True)
            draw_text(process, 27, 10, "How To Play", 37, "", True)

        elif selected_option == 1:
                    draw_text(process, 25, 10, "Solo Mode", 37, "", True)
                    draw_text(process, 26, 10, "Multiplayer", 30, 107, True)
                    draw_text(process, 27, 10, "How To Play", 37, "", True)

        elif selected_option == 2:
                    draw_text(process, 25, 10, "Solo Mode", 37, "", True)
                    draw_text(process, 26, 10, "Multiplayer", 37, "", True)
                    draw_text(process, 27, 10, "How To Play", 30, 107, True)        

    animation_task.cancel()

    try:
        await animation_task
    except asyncio.CancelledError:
        pass

    toggle_cursor(True, process)
    process.exit(0)

async def main():
    await asyncssh.create_server(
        OpenServer,
        "127.0.0.1",
        2222,
        server_host_keys=[load_key()],
        process_factory=handle_client,
        line_editor=False,
    )
    print("now listening on port 2222")
    await asyncio.Future()

class OpenServer(asyncssh.SSHServer):
    def begin_auth(self, username):
        return False

if __name__ == "__main__":
    asyncio.run(main())
