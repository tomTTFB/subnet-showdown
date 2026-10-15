import asyncssh
import os
import asyncio
import pyfiglet
import logging
import ipaddress
import random
import time

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

# ─
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

def explain_answer(question_type, ip, prefix):
    network = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)

    if question_type == "network":
        return f"The network begins at {network.network_address}."

    elif question_type == "broadcast":
            return f"The last address in this subnet is {network.broadcast_address}."

    if question_type == "hosts":
            return f"{network.num_addresses} total addresses - 2 reversed = {network.num_addresses - 2} usable hosts."





def make_question():
    question_types = ["network", "broadcast", "hosts"]

    question_type = random.choice(question_types)

    ip = ".".join(str(random.randint(0, 255)) for _ in range(4))
    prefix = random.randint(24, 30)

    network = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)

    if question_type == "network":
        answer = str(network.network_address)

    elif question_type == "broadcast":
        answer = str(network.broadcast_address)

    elif question_type == "hosts":
            answer = str(network.num_addresses - 2)

    return question_type, ip, prefix, answer

# gap to make this one easier to find

async def handle_client(process):

    question_type, ip, prefix, answer = make_question()

    toggle_cursor(False, process)

    state = "MENU"
    user_answer = ""
    answered = False

    score = 0
    streak = 0
    round_number = 1

    correct_answers = 0
    best_streak = 0
    total_rounds = 10

    question_start = time.monotonic()
 
    clear_screen(process)

    draw_figlet_text(process, 5, "Subnet", 32, "")
    draw_figlet_text(process, 10, "Showdown", 32, "")

    draw_text(process, 17, 10, "A Secure SHell Networking Quiz Game.", 37, "", True)

    options = [" Solo Mode ", "Multiplayer", "How to Play", "Exit"]
    selected_option = 0

    draw_line(process, 20, 32, "")

    draw_text(process, 25, 10, "Solo Mode", 30, 107, True)
    draw_text(process, 26, 10, "Multiplayer", 37, "", True)
    draw_text(process, 27, 10, "How To Play", 37, "", True)
    draw_text(process, 28, 10, "Exit", 37, "", True)

    draw_box(process, 23, 73, 15, 5, fg=37, bg="", text="Main Menu")

    animation_task = asyncio.create_task(draw_scrolling_line(process, 19))

    while True:
        try:
            if state == "SOLO" and not answered:
                remaining_time = max(0, 30 - (time.monotonic() - question_start))
                key = await asyncio.wait_for(
                    process.stdin.read(1), timeout=remaining_time
                )
            else:
                key = await process.stdin.read(1)
        except asyncio.TimeoutError:
            answered = True
            streak = 0

            draw_text(process, 28, 10, "Times up!", 31, "", True)
            draw_text(process, 30, 10, f"Correct Answer: {answer}", 33, "", True)
            draw_text(process, 33, 10, "Press ENTER for the next question", 37, "", True)

            round_number += 1
            continue

        except asyncssh.TerminalSizeChanged:
            continue


        if not key:
            clear_screen(process)
            break

        key = await get_special_key(key, process)

        if key == "ESC" and state != "MENU":
            state = "MENU"
            clear_screen(process)

            clear_screen(process)
            
            draw_figlet_text(process, 5, "Subnet", 32, "")
            draw_figlet_text(process, 10, "Showdown", 32, "")
        
            draw_text(process, 17, 10, "A Secure SHell Networking Quiz Game.", 37, "", True)
        
            draw_line(process, 20, 32, "")

            animation_task = asyncio.create_task(draw_scrolling_line(process, 19))
        
            draw_text(process, 25, 10, "Solo Mode", 30, 107, True)
            draw_text(process, 26, 10, "Multiplayer", 37, "", True)
            draw_text(process, 27, 10, "How To Play", 37, "", True)
            draw_text(process, 28, 10, "Exit", 37, "", True)
        
            draw_box(process, 23, 73, 15, 5, fg=37, bg="", text="Main Menu")

        if state == "SOLO":
            if not answered:
                if len(key) == 1 and key in "0123456789." and len(user_answer) <= 15:
                    user_answer += key

                elif key == "BACKSPACE":
                    user_answer = user_answer[:-1]

                elif key == "ENTER" and not answered:
                    elapsed = time.monotonic() - question_start
                    remaining_time = max(0, 30 - elapsed)
                    answered = True
                    if user_answer == answer and elapsed < 30:
                        draw_text(process, 28, 72, "CORRECT!", 32, "", True)
                        score += 100
                        streak += 1
                        correct_answers += 1
                        best_streak = max(best_streak, streak)
                    else:
                        draw_text(process, 28, 72, "INCORRECT!", 31, "", True)
                        draw_text(process, 30, 72, f"Correct Answer: {answer}", 33, "", True)
                        explaination = explain_answer(question_type, ip, prefix)
                        draw_text(process, 31, 72, explaination, 36, "", True)
                        streak = 0

                    round_number += 1
                    draw_text(process, 33, 72, f"Press ENTER for next question", 37, "", True)

            elif key == "ENTER" and answered:

                if round_number > total_rounds:
                    state = "RESULTS"
                    clear_screen(process)

                    accuracy = (correct_answers / total_rounds) * 100

                    draw_figlet_text(process, 3, "Results", 32, "")
                    
                    draw_text(process, 12, 10, f"Final Score: {score}", 37, "", True)
                    draw_text(process, 13, 10, f"Accuracy: {accuracy:.0f}%", 37, "", True)
                    draw_text(process, 14, 10, f"Correct: {correct_answers}", 37, "", True)
                    draw_text(process, 16, 10, f"Best Streak: {best_streak}", 37, "", True)
                    draw_text(process, 19, 10, f"Press ESC to return to the menu", 37, "", True)

                else:
                    question_type, ip, prefix, answer = make_question()
                    user_answer = ""
                    answered = False
                    question_start = time.monotonic()
                
                    clear_screen(process)
                    draw_figlet_text(process, 3, "Solo Practice", 32, "")

                    if question_type == "hosts":
                        question_text = "" "How many usable hosts are in:"
                    else:
                        question_text = "" f"What is the {question_type} address of:"

                    draw_text(process, 10, 10, question_text, 37, "", True)

                    draw_text(process, 12, 10, f"{ip}/{prefix}", 33, "", True)

                    draw_text(process, 14, 10, f"Round: {round_number}", 37, "", True)
                    draw_text(process, 15, 10, f"Score: {score}", 37, "", True)

                    if streak != 0:
                        draw_text(process, 17, 10, f"Streak: {streak}", 93, "", True)

                    draw_box(process, 23, 70, 20, 1, fg=37, bg="", text="Answer Box")

            if state == "SOLO":
                draw_text(process, 24, 72, " " * 19)
                draw_text(process, 24, 72, user_answer, 37)


        if key == "DOWN" and state == "MENU":
            selected_option = (selected_option + 1) % len(options)
        elif key == "UP" and state == "MENU":
            selected_option = (selected_option - 1) % len(options)
        elif key == "ENTER" and state == "MENU":
            if selected_option == 0:
                state = "SOLO"
                animation_task.cancel()

                user_answer = ""
                answered = False
                score = 0
                streak = 0
                round_number = 1
                question_type, ip, prefix, answer = make_question()
                
                correct_answers = 0
                best_streak = 0

                clear_screen(process)
                draw_figlet_text(process, 3, "Solo Practice", 32, "")

                draw_text(process, 10, 10, f"What is the {question_type} address of:", 37, "", True)
                draw_text(process, 12, 10, f"{ip}/{prefix}", 33, "", True)

                draw_text(process, 14, 10, f"Round: {round_number}", 37, "", True)
                draw_text(process, 15, 10, f"Score: {score}", 37, "", True)

                draw_box(process, 23, 70, 20, 1, fg=37, bg="", text="Answer Box")

            elif selected_option == 2:
                state = "HELP"
                animation_task.cancel()
                clear_screen(process)

                draw_figlet_text(process, 3, "How to Play", 32, "")

                draw_text(process, 12, 10, f"Solve correct subnetting questions to earn points", 37, "", True)
                draw_text(process, 13, 10, f"Correct answer: +100 points", 32, "", True)
                draw_text(process, 15, 10, f"Build up a streak by getting multiple in a row", 37, "", True)
                draw_text(process, 16, 10, f"Press ENTER to submit answer", 37, "", True)
                draw_text(process, 17, 10, f"Press ESC to return to the menu", 37, "", True)

                draw_text(process, 19, 10, f"Multiplayer is coming soon!", 90, "", True)

            elif selected_option == 3:
                clear_screen(process)
                break


        if state == "MENU":
            if selected_option == 0:
                draw_text(process, 25, 10, "Solo Mode", 30, 107, True)
                draw_text(process, 26, 10, "Multiplayer", 37, "", True)
                draw_text(process, 27, 10, "How To Play", 37, "", True)
                draw_text(process, 28, 10, "Exit", 37, "", True)

            elif selected_option == 1:
                    draw_text(process, 25, 10, "Solo Mode", 37, "", True)
                    draw_text(process, 26, 10, "Multiplayer", 30, 107, True)
                    draw_text(process, 27, 10, "How To Play", 37, "", True)
                    draw_text(process, 28, 10, "Exit", 37, "", True)

            elif selected_option == 2:
                draw_text(process, 25, 10, "Solo Mode", 37, "", True)
                draw_text(process, 26, 10, "Multiplayer", 37, "", True)
                draw_text(process, 27, 10, "How To Play", 30, 107, True)
                draw_text(process, 28, 10, "Exit", 37, "", True)

            elif selected_option == 3:
                draw_text(process, 25, 10, "Solo Mode", 37, "", True)
                draw_text(process, 26, 10, "Multiplayer", 37, "", True)
                draw_text(process, 27, 10, "How To Play", 37, "", True)
                draw_text(process, 28, 10, "Exit", 30, 107, True)        

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
        "0.0.0.0",
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
