#! /usr/local/bin/python3
import subprocess
import time
import ipaddress
import re



def print_error_message(reason):
    print("Error: " + reason + "\n")


def is_cef_message(message):
    return "CEF:" in message


def is_cisco_asa_message(message):
    return "%ASA-" in message


def get_prefix(message):
    if is_cisco_asa_message(message) or is_cef_message(message):
        return message.split(':')[0]
    else:
        return ""


def get_message(message):
    result = ""
    if is_cisco_asa_message(message) or is_cef_message(message):
        tokens = message.split(':')
        result = ':'.join(tokens[1:len(tokens)])
    else:
        result = message
    result = "\"" + result + "\""
    return result


def send_message(ip, port, message_to_send):
    command_tokens = ["logger", "-p",  "local4.warn", "-t", get_prefix(message_to_send),
                      get_message(message_to_send), "-P", str(port),
                      "-T", "-n", str(ip)] if get_prefix(message_to_send) != "" else ["logger", "-p",  "local4.warn", get_message(message_to_send), "-P", str(port), "-T", "-n", str(ip)]
    print("Commands\n")
    print(command_tokens)
    print("\n\n")
    logger = subprocess.Popen(command_tokens, stdout=subprocess.PIPE)
    o, e = logger.communicate()
    if e is None:
        return
    else:
        print("Error could not send message")


def get_seconds(line):
    tokens = line.split("|")
    if len(tokens) >=2:
        try:
            seconds = float(tokens[0])
            return seconds
        except ValueError:
            print_error_message("time: {time} is not a number".format(time=tokens[0]))
            return False
    else:
        print_error_message("line is not in the required format. Line:{line}".format(line=line))
        return False


def get_message_token(line):
    tokens = line.split("|")
    if len(tokens) >= 3:
        # we can assume that the first token is the number and and the last should be the destination
        message = '|'.join(tokens[1:len(tokens)-1])
        return message
    else:
        print_error_message("Incorrect line format : Line:{line}".format(line=line))
        return False


def validate_ip(ip_addr_str):
    try:
        ipaddress.ip_address(ip_addr_str.strip())
        return True
    except(ValueError, TypeError) as e:
        print_error_message("Provided destination ip is not valid. got: {ip}".format(ip=ip_addr_str))
        return False


def validate_port(port_str):
    try:
        int(port_str)
        return True
    except ValueError:
        print_error_message("Provided port is invalid. Got: {port_str}".format(port_str=port_str))
        return False


def get_port(line):
    tokens = line.split("|")
    # last token should be ip and port
    ip_port_str = tokens[len(tokens)-1]
    ip_port_arr = ip_port_str.split(":")
    if len(ip_port_arr) == 2:
        if validate_port(ip_port_arr[1]):
            port_str = str(int(ip_port_arr[1]))
            return port_str
    else:
        print_error_message("Destination should be in the following format ip:port. Got: {ip_port_str}"
                            .format(ip_port_str=ip_port_str))
        return False


def get_ip(line):
    tokens = line.split("|")
    # last token should be ip and port
    ip_port_str = tokens[len(tokens)-1]
    ip_port_arr = ip_port_str.split(":")
    if len(ip_port_arr) == 2:
        if validate_ip(ip_port_arr[0]):
            ip_str = ip_port_arr[0]
            return ip_str
    else:
        print_error_message("Destination should be in the following format ip:port. Got: {ip_port_str}"
                            .format(ip_port_str=ip_port_str))
        return False


def process_line(line):
    if not line.startswith("#"):
        seconds = get_seconds(line)
        if seconds:
            message = get_message_token(line)
            if message:
                ip = get_ip(line)
                port = get_port(line)
                if message and ip and port:
                    time.sleep(seconds)
                    send_message(ip, port, message)
                    print("Message was sent - {message}".format(message=message))


def read_line(path):
    # opening the file for read and iterating on each line
    command_files = open(path, 'r')
    lines = command_files.readlines()

    for line in lines:
        process_line(line)


if __name__ == '__main__':
    read_line("../example/4_lines_example.txt")